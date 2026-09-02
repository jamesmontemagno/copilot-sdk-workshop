package main

import (
	"strings"
	"testing"
)

func TestBuildExhibitPrompt(t *testing.T) {
	tests := []struct {
		name    string
		facts   []string
		want    []string
		wantErr string
	}{
		{
			name:  "includes trimmed facts and structure",
			facts: []string{" First approved fact. ", "", "Second approved fact."},
			want: []string{
				"- First approved fact.",
				"- Second approved fact.",
				"# <an engaging exhibit title>",
				"## Narrative",
				"## Visitor questions",
			},
		},
		{name: "rejects empty", facts: []string{" ", "\t"}, wantErr: "at least one"},
		{name: "allows maximum count", facts: repeatedFacts(maximumFactCount), want: []string{"- Approved fact."}},
		{name: "rejects too many", facts: repeatedFacts(maximumFactCount + 1), wantErr: "no more than 20"},
		{name: "allows maximum length", facts: []string{strings.Repeat("é", maximumFactLength)}, want: []string{strings.Repeat("é", maximumFactLength)}},
		{name: "rejects long fact", facts: []string{strings.Repeat("é", maximumFactLength+1)}, wantErr: "500 characters or fewer"},
	}

	for _, test := range tests {
		t.Run(test.name, func(t *testing.T) {
			prompt, err := buildExhibitPrompt(test.facts)
			if test.wantErr != "" {
				if err == nil || !strings.Contains(err.Error(), test.wantErr) {
					t.Fatalf("buildExhibitPrompt() error = %v, want containing %q", err, test.wantErr)
				}
				return
			}
			if err != nil {
				t.Fatalf("buildExhibitPrompt() unexpected error: %v", err)
			}
			for _, want := range test.want {
				if !strings.Contains(prompt, want) {
					t.Errorf("prompt does not contain %q", want)
				}
			}
		})
	}
}

func TestSystemMessageIsSeparateFromTaskFacts(t *testing.T) {
	if strings.Contains(curatorSystemMessage, apollo11Facts[0]) {
		t.Fatal("system message must not contain task facts")
	}
	prompt, err := buildExhibitPrompt(apollo11Facts)
	if err != nil {
		t.Fatal(err)
	}
	for _, fact := range apollo11Facts {
		if !strings.Contains(prompt, fact) {
			t.Errorf("task prompt does not contain %q", fact)
		}
	}
}

func repeatedFacts(count int) []string {
	facts := make([]string, count)
	for index := range facts {
		facts[index] = "Approved fact."
	}
	return facts
}
