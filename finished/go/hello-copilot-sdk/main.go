package main

import (
	"bufio"
	"context"
	"fmt"
	"os"
	"strings"
	"sync/atomic"

	copilot "github.com/github/copilot-sdk/go"
)

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

func streamResponse(session *copilot.Session, prompt string) error {
	var receivedDelta atomic.Bool
	unsubscribe := session.On(func(event copilot.SessionEvent) {
		if delta, ok := event.Data.(*copilot.AssistantMessageDeltaData); ok && delta.DeltaContent != "" {
			receivedDelta.Store(true)
			fmt.Print(delta.DeltaContent)
		}
	})
	defer unsubscribe()

	response, err := session.SendAndWait(context.Background(), copilot.MessageOptions{Prompt: prompt})
	if err != nil {
		return err
	}
	if !receivedDelta.Load() && response != nil {
		if message, ok := response.Data.(*copilot.AssistantMessageData); ok {
			fmt.Print(message.Content)
		}
	}
	fmt.Println()
	return nil
}

func readQuestion() string {
	if question := strings.TrimSpace(strings.Join(os.Args[1:], " ")); question != "" {
		return question
	}
	fmt.Print("Accessibility question: ")
	question, _ := bufio.NewReader(os.Stdin).ReadString('\n')
	return strings.TrimSpace(question)
}

func main() {
	question := readQuestion()
	if question == "" {
		fmt.Fprintln(os.Stderr, "Enter an accessibility question to continue.")
		return
	}

	lookup := copilot.DefineTool(
		"accessibility_rule_lookup",
		"Looks up read-only WCAG guidance maintained by this application.",
		accessibilityRuleLookup,
	)
	lookup.SkipPermission = true

	client := copilot.NewClient(&copilot.ClientOptions{LogLevel: "error"})
	if err := client.Start(context.Background()); err != nil {
		panic(err)
	}
	defer client.Stop()

	session, err := client.CreateSession(context.Background(), &copilot.SessionConfig{
		Streaming:      copilot.Bool(true),
		Tools:          []copilot.Tool{lookup},
		AvailableTools: []string{"accessibility_rule_lookup"},
	})
	if err != nil {
		panic(err)
	}
	defer session.Disconnect()

	fmt.Println("\nCopilot:")
	if err := streamResponse(session, "Use accessibility_rule_lookup to answer this question: "+question); err != nil {
		panic(err)
	}
}
