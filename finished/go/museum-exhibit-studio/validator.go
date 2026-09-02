package main

import (
	"fmt"
	"regexp"
	"strings"
)

var (
	titlePattern    = regexp.MustCompile(`^# [^#].*$`)
	wordPattern     = regexp.MustCompile(`[\pL\pN]+(?:['’-][\pL\pN]+)*`)
	questionPattern = regexp.MustCompile(`^\s*\d+\.\s+(.+?)\s*$`)
	prohibitedWords = []string{"software", "codebase", "repository", "terminal", "GitHub Copilot"}
)

type TitleValidation struct {
	TitleCount int
}

func (validation TitleValidation) Present() bool { return validation.TitleCount == 1 }
func (validation TitleValidation) Valid() bool   { return validation.Present() }

type NarrativeValidation struct {
	Present   bool
	WordCount int
}

func (validation NarrativeValidation) WithinLimit() bool {
	return validation.WordCount >= 100 && validation.WordCount <= 140
}
func (validation NarrativeValidation) Valid() bool {
	return validation.Present && validation.WithinLimit()
}

type VisitorQuestionsValidation struct {
	Present              bool
	QuestionCount        int
	AllItemsAreQuestions bool
}

func (validation VisitorQuestionsValidation) ExactlyThree() bool {
	return validation.QuestionCount == 3
}
func (validation VisitorQuestionsValidation) Valid() bool {
	return validation.Present && validation.ExactlyThree() && validation.AllItemsAreQuestions
}

type VocabularyValidation struct {
	ProhibitedTerms []string
}

func (validation VocabularyValidation) Valid() bool {
	return len(validation.ProhibitedTerms) == 0
}

type ExhibitValidation struct {
	Title            TitleValidation
	Narrative        NarrativeValidation
	VisitorQuestions VisitorQuestionsValidation
	Vocabulary       VocabularyValidation
	Errors           []string
}

func (validation ExhibitValidation) Valid() bool {
	return len(validation.Errors) == 0
}

func validateExhibit(content string) ExhibitValidation {
	lines := strings.Split(strings.ReplaceAll(content, "\r\n", "\n"), "\n")
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

	var prohibited []string
	lowerContent := strings.ToLower(content)
	for _, term := range prohibitedWords {
		if strings.Contains(lowerContent, strings.ToLower(term)) {
			prohibited = append(prohibited, term)
		}
	}

	result := ExhibitValidation{
		Title:     TitleValidation{TitleCount: titleCount},
		Narrative: NarrativeValidation{Present: narrativeIndex >= 0, WordCount: wordCount},
		VisitorQuestions: VisitorQuestionsValidation{
			Present:              questionsIndex >= 0,
			QuestionCount:        len(questions),
			AllItemsAreQuestions: len(questions) > 0,
		},
		Vocabulary: VocabularyValidation{ProhibitedTerms: prohibited},
	}
	for _, question := range questions {
		if !strings.HasSuffix(question, "?") {
			result.VisitorQuestions.AllItemsAreQuestions = false
		}
	}
	if !result.Title.Valid() {
		result.Errors = append(result.Errors, "The exhibit must contain exactly one level-one title.")
	}
	if !result.Narrative.Present {
		result.Errors = append(result.Errors, "The exhibit must contain a Narrative section.")
	}
	if !result.Narrative.WithinLimit() {
		result.Errors = append(result.Errors, fmt.Sprintf("The narrative must contain 100-140 words; found %d.", wordCount))
	}
	if !result.VisitorQuestions.Present {
		result.Errors = append(result.Errors, "The exhibit must contain a Visitor questions section.")
	}
	if !result.VisitorQuestions.ExactlyThree() {
		result.Errors = append(result.Errors, fmt.Sprintf("The exhibit must contain exactly three numbered questions; found %d.", len(questions)))
	}
	if !result.VisitorQuestions.AllItemsAreQuestions {
		result.Errors = append(result.Errors, "Every numbered visitor item must end with a question mark.")
	}
	if !result.Vocabulary.Valid() {
		result.Errors = append(result.Errors, "The exhibit contains prohibited vocabulary: "+strings.Join(prohibited, ", ")+".")
	}
	return result
}

func findHeading(lines []string, heading string) int {
	for index, line := range lines {
		if strings.EqualFold(strings.TrimSpace(line), heading) {
			return index
		}
	}
	return -1
}
