package main

import (
	"bufio"
	"context"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"strings"
	"sync"
	"time"

	copilot "github.com/github/copilot-sdk/go"
	"github.com/github/copilot-sdk/go/rpc"
)

const (
	GenerationTimeout time.Duration = 120 * time.Second
	ResearchTimeout   time.Duration = 90 * time.Second

	MaximumFactCount  = 20
	MaximumFactLength = 500
	ExhibitFileName   = "exhibit.html"

	ApprovedFactLookupName = "approved_fact_lookup"
)

var Apollo11Facts = []string{
	"Apollo 11 launched July 16, 1969.",
	"It landed on the Moon July 20, 1969.",
	"Neil Armstrong and Buzz Aldrin walked on the Moon.",
	"Michael Collins remained in lunar orbit.",
	"The mission returned to Earth July 24, 1969.",
}

var GreatBarrierReefFacts = []string{
	"The Great Barrier Reef lies off the coast of Queensland, Australia.",
	"It stretches for about 2,300 kilometres.",
	"It is made up of more than 2,900 individual reefs.",
	"It was added to the UNESCO World Heritage List in 1981.",
	"Rising sea temperatures have caused repeated coral bleaching events.",
}

var TerracottaArmyFacts = []string{
	"The Terracotta Army was buried near the tomb of China's first emperor, Qin Shi Huang.",
	"Farmers digging a well discovered the site in 1974.",
	"The pits contain thousands of life-sized clay soldiers.",
	"Each figure was assembled from moulded parts and finished by hand.",
	"The site sits near the modern city of Xi'an in Shaanxi Province.",
}

type FactSet struct {
	Key   string
	Label string
	Facts []string
}

var FactSets = []FactSet{
	{Key: "apollo11", Label: "Apollo 11", Facts: Apollo11Facts},
	{Key: "reef", Label: "Great Barrier Reef", Facts: GreatBarrierReefFacts},
	{Key: "terracotta", Label: "Terracotta Army", Facts: TerracottaArmyFacts},
}

func BoundFacts(facts []string) ([]string, error) {
	bounded := make([]string, 0, len(facts))
	for _, fact := range facts {
		if trimmed := strings.TrimSpace(fact); trimmed != "" {
			bounded = append(bounded, trimmed)
		}
	}
	if len(bounded) == 0 {
		return nil, fmt.Errorf("Provide at least one approved fact.")
	}
	if len(bounded) > MaximumFactCount {
		return nil, fmt.Errorf("Provide no more than %d approved facts.", MaximumFactCount)
	}
	for _, fact := range bounded {
		if len([]rune(fact)) > MaximumFactLength {
			return nil, fmt.Errorf("Each approved fact must be %d characters or fewer.", MaximumFactLength)
		}
	}
	return bounded, nil
}

// ApprovedFactLookup owns the approved facts. It is the only way the curator can read them.
func ApprovedFactLookup(facts []string) (copilot.Tool, error) {
	approvedFacts, err := BoundFacts(facts)
	if err != nil {
		return copilot.Tool{}, err
	}

	lookup := copilot.DefineTool(
		ApprovedFactLookupName,
		"Returns the complete list of educator-approved facts this application holds for the current exhibit.",
		func(_ struct{}, _ copilot.ToolInvocation) ([]string, error) {
			return append([]string(nil), approvedFacts...), nil
		},
	)
	lookup.SkipPermission = true
	return lookup, nil
}

func StreamExhibit(session *copilot.Session, prompt string, timeout time.Duration) (string, error) {
	if timeout <= 0 {
		timeout = GenerationTimeout
	}
	ctx, cancel := context.WithTimeout(context.Background(), timeout)
	defer cancel()

	var mu sync.Mutex
	var content strings.Builder
	receivedDelta := false
	printedWholeMessage := false
	var sessionErr error

	unsubscribe := session.On(func(event copilot.SessionEvent) {
		mu.Lock()
		defer mu.Unlock()

		switch data := event.Data.(type) {
		case *copilot.AssistantMessageDeltaData:
			if data.DeltaContent != "" {
				receivedDelta = true
				content.WriteString(data.DeltaContent)
				fmt.Print(data.DeltaContent)
			}
		case *copilot.AssistantMessageData:
			if !receivedDelta && data.Content != "" {
				printedWholeMessage = true
				content.WriteString(data.Content)
				fmt.Print(data.Content)
			}
		case *copilot.ToolExecutionStartData:
			fmt.Printf("\n[tool:start] %s\n", data.ToolName)
		case *copilot.ToolExecutionCompleteData:
			fmt.Printf("[tool:done] success=%t\n", data.Success)
		case *copilot.SessionErrorData:
			sessionErr = fmt.Errorf("%s", data.Message)
		case *copilot.SessionIdleData:
			fmt.Println()
		}
	})
	defer unsubscribe()

	response, err := session.SendAndWait(ctx, copilot.MessageOptions{Prompt: prompt})
	if err != nil {
		if ctx.Err() != nil {
			return "", fmt.Errorf("timeout waiting for curator response: %w", err)
		}
		return "", err
	}

	mu.Lock()
	defer mu.Unlock()
	if !receivedDelta && !printedWholeMessage && response != nil {
		if message, ok := response.Data.(*copilot.AssistantMessageData); ok && message.Content != "" {
			content.WriteString(message.Content)
			fmt.Print(message.Content)
			fmt.Println()
		}
	}
	if sessionErr != nil {
		return content.String(), sessionErr
	}
	return content.String(), nil
}

type TitleValidation struct {
	Present    bool
	TitleCount int
}

type NarrativeValidation struct {
	Present     bool
	WordCount   int
	WithinLimit bool
}

type VisitorQuestionsValidation struct {
	Present              bool
	QuestionCount        int
	ExactlyThree         bool
	AllItemsAreQuestions bool
}

type VocabularyValidation struct {
	ProhibitedTerms []string
}

type ExhibitValidation struct {
	Title            TitleValidation
	Narrative        NarrativeValidation
	VisitorQuestions VisitorQuestionsValidation
	Vocabulary       VocabularyValidation
	Errors           []string
	Valid            bool
}

var (
	titlePattern          = regexp.MustCompile(`^# [^#].*$`)
	wordPattern           = regexp.MustCompile(`\b[\p{L}\p{N}]+(?:['’-][\p{L}\p{N}]+)*\b`)
	questionPattern       = regexp.MustCompile(`^\s*\d+\.\s+(.+?)\s*$`)
	prohibitedVocabulary  = []string{"software", "codebase", "repository", "terminal", "GitHub Copilot"}
	lineEndingNormalizer  = strings.NewReplacer("\r\n", "\n", "\r", "\n")
	terminalReader        = bufio.NewReader(os.Stdin)
	wikipediaAllowedTools = map[string]struct{}{
		"search":                {},
		"readArticle":           {},
		"wikipedia-search":      {},
		"wikipedia-readArticle": {},
	}
)

func ValidateExhibit(content string) ExhibitValidation {
	lines := strings.Split(lineEndingNormalizer.Replace(content), "\n")
	titleCount := 0
	for _, line := range lines {
		if titlePattern.MatchString(line) {
			titleCount++
		}
	}

	narrativeIndex := findHeading(lines, "## Narrative")
	questionsIndex := findHeading(lines, "## Visitor questions")

	narrative := ""
	if narrativeIndex >= 0 && questionsIndex > narrativeIndex {
		narrative = strings.Join(lines[narrativeIndex+1:questionsIndex], " ")
	}
	wordCount := len(wordPattern.FindAllString(narrative, -1))

	var questions []string
	if questionsIndex >= 0 {
		for _, line := range lines[questionsIndex+1:] {
			if match := questionPattern.FindStringSubmatch(line); match != nil {
				questions = append(questions, strings.TrimSpace(match[1]))
			}
		}
	}

	prohibitedTerms := make([]string, 0)
	lowerContent := strings.ToLower(content)
	for _, term := range prohibitedVocabulary {
		if strings.Contains(lowerContent, strings.ToLower(term)) {
			prohibitedTerms = append(prohibitedTerms, term)
		}
	}

	validation := ExhibitValidation{
		Title: TitleValidation{
			Present:    titleCount == 1,
			TitleCount: titleCount,
		},
		Narrative: NarrativeValidation{
			Present:     narrativeIndex >= 0,
			WordCount:   wordCount,
			WithinLimit: wordCount >= 100 && wordCount <= 140,
		},
		VisitorQuestions: VisitorQuestionsValidation{
			Present:              questionsIndex >= 0,
			QuestionCount:        len(questions),
			ExactlyThree:         len(questions) == 3,
			AllItemsAreQuestions: len(questions) > 0,
		},
		Vocabulary: VocabularyValidation{ProhibitedTerms: prohibitedTerms},
	}
	for _, question := range questions {
		if !strings.HasSuffix(question, "?") {
			validation.VisitorQuestions.AllItemsAreQuestions = false
		}
	}

	if !validation.Title.Present {
		validation.Errors = append(validation.Errors, "The exhibit must contain exactly one level-one title.")
	}
	if !validation.Narrative.Present {
		validation.Errors = append(validation.Errors, "The exhibit must contain a Narrative section.")
	}
	if !validation.Narrative.WithinLimit {
		validation.Errors = append(validation.Errors, fmt.Sprintf("The narrative must contain 100-140 words; found %d.", wordCount))
	}
	if !validation.VisitorQuestions.Present {
		validation.Errors = append(validation.Errors, "The exhibit must contain a Visitor questions section.")
	}
	if !validation.VisitorQuestions.ExactlyThree {
		validation.Errors = append(validation.Errors, fmt.Sprintf("The exhibit must contain exactly three numbered questions; found %d.", len(questions)))
	}
	if !validation.VisitorQuestions.AllItemsAreQuestions {
		validation.Errors = append(validation.Errors, "Every numbered visitor item must end with a question mark.")
	}
	if len(validation.Vocabulary.ProhibitedTerms) > 0 {
		validation.Errors = append(validation.Errors, "The exhibit contains prohibited vocabulary: "+strings.Join(prohibitedTerms, ", ")+".")
	}
	validation.Valid = len(validation.Errors) == 0
	return validation
}

func FormatValidation(validation ExhibitValidation) string {
	var report strings.Builder
	if validation.Valid {
		report.WriteString("Structural checks passed.\n")
	} else {
		report.WriteString("Structural checks found issues:\n")
	}
	fmt.Fprintf(&report, "- One level-one title: %t\n", validation.Title.Present)
	fmt.Fprintf(&report, "- Narrative section: %t\n", validation.Narrative.Present)
	fmt.Fprintf(&report, "- Narrative length: %d words (within 100-140: %t)\n", validation.Narrative.WordCount, validation.Narrative.WithinLimit)
	fmt.Fprintf(&report, "- Visitor questions section: %t\n", validation.VisitorQuestions.Present)
	fmt.Fprintf(&report, "- Numbered questions: %d (exactly three: %t)\n", validation.VisitorQuestions.QuestionCount, validation.VisitorQuestions.ExactlyThree)
	fmt.Fprintf(&report, "- Every item is a question: %t\n", validation.VisitorQuestions.AllItemsAreQuestions)
	if len(validation.Vocabulary.ProhibitedTerms) == 0 {
		report.WriteString("- Prohibited vocabulary: none\n")
	} else {
		fmt.Fprintf(&report, "- Prohibited vocabulary: %s\n", strings.Join(validation.Vocabulary.ProhibitedTerms, ", "))
	}
	for _, message := range validation.Errors {
		fmt.Fprintf(&report, "  - %s\n", message)
	}
	report.WriteString("\nStructural checks do not prove factual grounding. Unsupported claims require human review or a separate evaluator.")
	return report.String()
}

func findHeading(lines []string, heading string) int {
	for index, line := range lines {
		if strings.EqualFold(strings.TrimSpace(line), heading) {
			return index
		}
	}
	return -1
}

var WikipediaTools = []string{"wikipedia-search", "wikipedia-readArticle"}

// WikipediaServer returns the config to place in SessionConfig.MCPServers under the key "wikipedia".
func WikipediaServer() copilot.MCPStdioServerConfig {
	workingDirectory, err := os.Getwd()
	if err != nil {
		workingDirectory = "."
	}
	return copilot.MCPStdioServerConfig{
		Command:          "npx",
		Args:             []string{"-y", "wikipedia-mcp@1.0.3"},
		WorkingDirectory: workingDirectory,
		Tools:            []string{"search", "readArticle"},
	}
}

func WikipediaPermissionHandler() copilot.PermissionHandlerFunc {
	return func(request copilot.PermissionRequest, _ copilot.PermissionInvocation) (rpc.PermissionDecision, error) {
		serverName, toolName, ok := mcpPermissionDetails(request)
		if ok && serverName == "wikipedia" {
			if _, allowed := wikipediaAllowedTools[toolName]; allowed {
				return &rpc.PermissionDecisionApproveOnce{}, nil
			}
		}
		feedback := "This session allows only the scoped Wikipedia search and article tools."
		return &rpc.PermissionDecisionReject{Feedback: &feedback}, nil
	}
}

type Source struct {
	Title string
	URL   string
}

type SourceExtraction struct {
	Body    string
	Sources []Source
}

func ExtractSources(content string) SourceExtraction {
	normalized := lineEndingNormalizer.Replace(content)
	lines := strings.Split(normalized, "\n")
	sourcesIndex := -1
	for index, line := range lines {
		if strings.EqualFold(strings.TrimSpace(line), "## Sources") {
			sourcesIndex = index
		}
	}
	if sourcesIndex < 0 {
		return SourceExtraction{Body: strings.TrimSpace(normalized)}
	}

	extraction := SourceExtraction{Body: strings.TrimSpace(strings.Join(lines[:sourcesIndex], "\n"))}
	for _, line := range lines[sourcesIndex+1:] {
		item := strings.TrimSpace(line)
		if !strings.HasPrefix(item, "-") {
			continue
		}
		item = strings.TrimSpace(strings.TrimPrefix(item, "-"))
		urlIndex := strings.Index(item, "https://")
		if urlIndex < 0 {
			continue
		}
		title := strings.TrimSpace(strings.TrimSuffix(strings.TrimSpace(item[:urlIndex]), ":"))
		url := strings.TrimSpace(item[urlIndex:])
		if title != "" && url != "" {
			extraction.Sources = append(extraction.Sources, Source{Title: title, URL: url})
		}
	}
	return extraction
}

func ExhibitWritePermission(workingDirectory string) copilot.PermissionHandlerFunc {
	if absolute, err := filepath.Abs(workingDirectory); err == nil {
		workingDirectory = absolute
	}
	exhibitPath := filepath.Clean(filepath.Join(workingDirectory, ExhibitFileName))
	return func(request copilot.PermissionRequest, _ copilot.PermissionInvocation) (rpc.PermissionDecision, error) {
		if fileName, ok := writePermissionFileName(request); ok {
			candidate := fileName
			if !filepath.IsAbs(candidate) {
				candidate = filepath.Join(workingDirectory, candidate)
			}
			if filepath.Clean(candidate) == exhibitPath {
				return &rpc.PermissionDecisionApproveOnce{}, nil
			}
		}
		feedback := "This session allows writing only exhibit.html in the application working directory."
		return &rpc.PermissionDecisionReject{Feedback: &feedback}, nil
	}
}

func AskYesNo(question string, defaultYes bool) bool {
	if defaultYes {
		fmt.Printf("%s [Y/n]: ", question)
	} else {
		fmt.Printf("%s [y/N]: ", question)
	}
	answer, _ := terminalReader.ReadString('\n')
	switch strings.ToLower(strings.TrimSpace(answer)) {
	case "":
		return defaultYes
	case "y", "yes":
		return true
	case "n", "no":
		return false
	default:
		return defaultYes
	}
}

func AskLine(question string) string {
	fmt.Print(question)
	answer, _ := terminalReader.ReadString('\n')
	return strings.TrimSpace(answer)
}

func ReadFacts() []string {
	fmt.Println("Enter one approved fact per line. Submit a blank line when finished:")
	var facts []string
	for {
		line, err := terminalReader.ReadString('\n')
		fact := strings.TrimSpace(line)
		if fact != "" {
			facts = append(facts, fact)
		}
		if fact == "" || err != nil {
			return facts
		}
	}
}

func mcpPermissionDetails(request copilot.PermissionRequest) (string, string, bool) {
	switch value := request.(type) {
	case copilot.PermissionRequestMCP:
		return value.ServerName, value.ToolName, true
	case *copilot.PermissionRequestMCP:
		return value.ServerName, value.ToolName, true
	}

	raw, err := json.Marshal(request)
	if err != nil {
		return "", "", false
	}
	var value map[string]any
	if json.Unmarshal(raw, &value) != nil || value["kind"] != "mcp" {
		return "", "", false
	}
	serverName, _ := value["serverName"].(string)
	toolName, _ := value["toolName"].(string)
	return serverName, toolName, serverName != "" && toolName != ""
}

func writePermissionFileName(request copilot.PermissionRequest) (string, bool) {
	switch value := request.(type) {
	case copilot.PermissionRequestWrite:
		return value.FileName, value.FileName != ""
	case *copilot.PermissionRequestWrite:
		return value.FileName, value.FileName != ""
	}

	raw, err := json.Marshal(request)
	if err != nil {
		return "", false
	}
	var value map[string]any
	if json.Unmarshal(raw, &value) != nil || value["kind"] != "write" {
		return "", false
	}
	fileName, ok := value["fileName"].(string)
	return fileName, ok && fileName != ""
}
