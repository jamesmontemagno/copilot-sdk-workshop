package main

import (
	"context"
	"encoding/json"
	"fmt"
	"net/url"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"time"

	copilot "github.com/github/copilot-sdk/go"
	"github.com/github/copilot-sdk/go/rpc"
)

const maxSnapshotBytes = 1_000_000

type accessibilityRule struct {
	Criterion      string   `json:"criterion"`
	Title          string   `json:"title"`
	WhenItApplies  string   `json:"when_it_applies"`
	Recommendation string   `json:"recommendation"`
	Keywords       []string `json:"keywords"`
}

var accessibilityRules = []accessibilityRule{
	{"1.1.1", "Non-text Content", "An informative image has no useful text alternative.", `Add concise alt text that communicates the image purpose. Use alt="" only for decorative images.`, []string{"image", "alt text", "text alternative"}},
	{"1.3.1", "Info and Relationships", "Page structure or relationships are only conveyed visually.", "Use semantic landmarks and a logical heading hierarchy so structure is programmatically available.", []string{"main landmark", "heading hierarchy", "page structure", "semantic"}},
	{"1.4.3", "Contrast (Minimum)", "Text does not have enough contrast against its background.", "Provide at least 4.5:1 contrast for normal text and 3:1 for large text.", []string{"contrast", "low contrast", "color"}},
	{"2.4.7", "Focus Visible", "Keyboard focus cannot be seen clearly.", "Keep a visible, high-contrast focus indicator on every interactive element.", []string{"focus", "keyboard", "outline"}},
	{"3.3.2", "Labels or Instructions", "A form does not provide a persistent visible label or necessary instructions.", "Provide visible labels and instructions that explain the expected input.", []string{"visible label", "instructions", "required field", "input format"}},
	{"4.1.2", "Name, Role, Value", "A form control has no programmatically determinable accessible name.", "Associate a visible <label> with the input by using matching for and id values.", []string{"accessible name", "programmatic label", "unlabeled input", "name role value"}},
}

type lookupParams struct {
	Query string `json:"query" jsonschema:"The accessibility issue or WCAG criterion to look up."`
}

func accessibilityRuleLookup(params lookupParams, _ copilot.ToolInvocation) (any, error) {
	query := strings.ToLower(strings.TrimSpace(params.Query))
	for _, rule := range accessibilityRules {
		if strings.Contains(query, strings.ToLower(rule.Criterion)) ||
			strings.Contains(query, strings.ToLower(rule.Title)) {
			return rule, nil
		}
		for _, keyword := range rule.Keywords {
			if strings.Contains(query, keyword) {
				return rule, nil
			}
		}
	}
	return accessibilityRule{
		Criterion:      "No exact match",
		Title:          "Criterion not found",
		WhenItApplies:  "The issue is not represented in the workshop catalog.",
		Recommendation: "Verify the evidence and consult the complete WCAG reference.",
	}, nil
}

func snapshotReader(workingDirectory string) func(struct{}, copilot.ToolInvocation) (string, error) {
	outputDirectory := filepath.Join(workingDirectory, ".playwright-mcp")
	existing := map[string]struct{}{}
	if entries, err := os.ReadDir(outputDirectory); err == nil {
		for _, entry := range entries {
			if strings.HasPrefix(entry.Name(), "page-") && strings.HasSuffix(entry.Name(), ".yml") {
				existing[filepath.Join(outputDirectory, entry.Name())] = struct{}{}
			}
		}
	}

	return func(_ struct{}, _ copilot.ToolInvocation) (string, error) {
		entries, err := os.ReadDir(outputDirectory)
		if err != nil {
			return "", fmt.Errorf("No current-run Playwright snapshot is available. Call browser_navigate first.")
		}
		type candidate struct {
			path string
			mod  time.Time
		}
		var candidates []candidate
		for _, entry := range entries {
			path := filepath.Join(outputDirectory, entry.Name())
			if _, alreadyExisted := existing[path]; alreadyExisted ||
				entry.IsDir() ||
				entry.Type()&os.ModeSymlink != 0 ||
				!strings.HasPrefix(entry.Name(), "page-") ||
				!strings.HasSuffix(entry.Name(), ".yml") {
				continue
			}
			info, err := entry.Info()
			if err != nil || !info.Mode().IsRegular() || info.Size() == 0 || info.Size() > maxSnapshotBytes {
				continue
			}
			candidates = append(candidates, candidate{path, info.ModTime()})
		}
		if len(candidates) == 0 {
			return "", fmt.Errorf("No current-run Playwright snapshot is available. Call browser_navigate first.")
		}
		sort.Slice(candidates, func(i, j int) bool { return candidates[i].mod.Before(candidates[j].mod) })
		contents, err := os.ReadFile(candidates[len(candidates)-1].path)
		if err != nil {
			return "", err
		}
		return string(contents), nil
	}
}

func sameURL(requested, allowed string) bool {
	left, leftErr := url.Parse(requested)
	right, rightErr := url.Parse(allowed)
	if leftErr != nil || rightErr != nil {
		return false
	}
	userInfo := func(value *url.Userinfo) string {
		if value == nil {
			return ""
		}
		return value.String()
	}
	return strings.EqualFold(left.Scheme, right.Scheme) &&
		strings.EqualFold(left.Hostname(), right.Hostname()) &&
		left.Port() == right.Port() &&
		userInfo(left.User) == userInfo(right.User) &&
		left.EscapedPath() == right.EscapedPath() &&
		left.RawQuery == right.RawQuery &&
		left.Fragment == right.Fragment
}

func permissionForTarget(target string) copilot.PermissionHandlerFunc {
	return func(request copilot.PermissionRequest, _ copilot.PermissionInvocation) (rpc.PermissionDecision, error) {
		raw, err := json.Marshal(request)
		if err == nil {
			var value map[string]any
			if json.Unmarshal(raw, &value) == nil &&
				value["kind"] == "mcp" &&
				value["serverName"] == "playwright" {
				toolName, _ := value["toolName"].(string)
				args, _ := value["args"].(map[string]any)
				requested, _ := args["url"].(string)
				if (toolName == "browser_navigate" || toolName == "playwright-browser_navigate") && sameURL(requested, target) {
					return &rpc.PermissionDecisionApproveOnce{}, nil
				}
			}
		}
		feedback := "This workshop allows Playwright to navigate only to the exact requested target."
		return &rpc.PermissionDecisionReject{Feedback: &feedback}, nil
	}
}

func reportPrompt(target string) string {
	return fmt.Sprintf(`Prepare an evidence-based accessibility review of %s.
1. Use browser_navigate to open that exact URL.
2. Call read_latest_accessibility_snapshot to inspect its accessibility tree.
3. Identify three to five high-confidence issues supported by the snapshot.
4. Call accessibility_rule_lookup for each issue before recommending a fix.

Return only this structure:
# Accessibility review
## Finding 1: <short name>
- Evidence: <specific element or page structure observed in the browser>
- WCAG criterion: <criterion and title returned by the catalog>
- Recommended remediation: <specific implementation change>
Repeat the finding section as needed.
## Review limits
State that this is a focused review of browser-observable evidence, not a full WCAG conformance audit.
Do not invent evidence, report unsupported statistics, or claim the page is WCAG compliant.`, target)
}

func printResponse(session *copilot.Session, prompt string) error {
	response, err := session.SendAndWait(context.Background(), copilot.MessageOptions{Prompt: prompt})
	if err != nil {
		return err
	}
	if response == nil {
		return nil
	}
	if message, ok := response.Data.(*copilot.AssistantMessageData); ok {
		fmt.Println(message.Content)
		return nil
	}
	fmt.Printf("%v\n", response.Data)
	return nil
}

func main() {
	if len(os.Args) != 2 {
		fmt.Fprintln(os.Stderr, "Usage: go run . <http-or-https-url>")
		return
	}
	target := os.Args[1]
	if !strings.Contains(target, "://") {
		target = "https://" + target
	}
	parsed, err := url.ParseRequestURI(target)
	if err != nil || (parsed.Scheme != "http" && parsed.Scheme != "https") || parsed.Host == "" {
		fmt.Fprintln(os.Stderr, "Enter an absolute HTTP or HTTPS URL.")
		return
	}

	workingDirectory, err := os.Getwd()
	if err != nil {
		panic(err)
	}
	lookup := copilot.DefineTool("accessibility_rule_lookup", "Looks up read-only WCAG guidance maintained by this application.", accessibilityRuleLookup)
	lookup.SkipPermission = true
	readSnapshot := copilot.DefineTool("read_latest_accessibility_snapshot", "Reads the newest Playwright accessibility snapshot created during this run.", snapshotReader(workingDirectory))
	readSnapshot.SkipPermission = true

	client := copilot.NewClient(&copilot.ClientOptions{LogLevel: "error"})
	if err := client.Start(context.Background()); err != nil {
		panic(err)
	}
	defer client.Stop()
	session, err := client.CreateSession(context.Background(), &copilot.SessionConfig{
		Streaming:           copilot.Bool(true),
		Tools:               []copilot.Tool{lookup, readSnapshot},
		AvailableTools:      []string{"accessibility_rule_lookup", "read_latest_accessibility_snapshot", "playwright-browser_navigate"},
		OnPermissionRequest: permissionForTarget(target),
		MCPServers: map[string]copilot.MCPServerConfig{
			"playwright": copilot.MCPStdioServerConfig{
				Command:          "npx",
				Args:             []string{"-y", "@playwright/mcp@0.0.78", "--browser=msedge", "--output-dir", ".playwright-mcp", "--output-mode", "file"},
				WorkingDirectory: workingDirectory,
				Tools:            []string{"browser_navigate"},
			},
		},
	})
	if err != nil {
		panic(err)
	}
	defer session.Disconnect()
	if err := printResponse(session, reportPrompt(target)); err != nil {
		panic(err)
	}
}
