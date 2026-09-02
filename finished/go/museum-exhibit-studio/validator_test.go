package main

import (
	"fmt"
	"strings"
	"testing"
)

func TestValidateExhibit(t *testing.T) {
	tests := []struct {
		name      string
		content   string
		wantValid bool
		check     func(t *testing.T, validation ExhibitValidation)
	}{
		{name: "accepts complete exhibit", content: makeExhibit(110, 3, true), wantValid: true},
		{
			name: "counts lower word boundary", content: makeExhibit(100, 3, true), wantValid: true,
			check: func(t *testing.T, v ExhibitValidation) {
				if v.Narrative.WordCount != 100 {
					t.Errorf("word count = %d, want 100", v.Narrative.WordCount)
				}
			},
		},
		{name: "counts upper word boundary", content: makeExhibit(140, 3, true), wantValid: true},
		{
			name: "rejects 99 words", content: makeExhibit(99, 3, true),
			check: func(t *testing.T, v ExhibitValidation) {
				if v.Narrative.WithinLimit() {
					t.Error("NarrativeWithinLimit = true")
				}
			},
		},
		{name: "rejects 141 words", content: makeExhibit(141, 3, true)},
		{
			name: "rejects missing title", content: strings.Replace(makeExhibit(110, 3, true), "# A Journey\n", "", 1),
			check: func(t *testing.T, v ExhibitValidation) {
				if v.Title.Present() {
					t.Error("TitlePresent = true")
				}
			},
		},
		{name: "rejects two titles", content: "# Another Title\n" + makeExhibit(110, 3, true)},
		{
			name: "rejects missing narrative section", content: strings.Replace(makeExhibit(110, 3, true), "## Narrative", "## Story", 1),
			check: func(t *testing.T, v ExhibitValidation) {
				if v.Narrative.Present {
					t.Error("NarrativePresent = true")
				}
			},
		},
		{
			name: "rejects missing questions section", content: strings.Replace(makeExhibit(110, 3, true), "## Visitor questions", "## Prompts", 1),
			check: func(t *testing.T, v ExhibitValidation) {
				if v.VisitorQuestions.Present {
					t.Error("VisitorQuestionsPresent = true")
				}
			},
		},
		{name: "rejects two questions", content: makeExhibit(110, 2, true)},
		{name: "rejects four questions", content: makeExhibit(110, 4, true)},
		{
			name: "rejects item without question mark", content: makeExhibit(110, 3, false),
			check: func(t *testing.T, v ExhibitValidation) {
				if v.VisitorQuestions.AllItemsAreQuestions {
					t.Error("AllItemsAreQuestions = true")
				}
			},
		},
		{
			name:    "reports prohibited terms case insensitively",
			content: strings.Replace(makeExhibit(110, 3, true), "word1", "SOFTWARE", 1),
			check: func(t *testing.T, v ExhibitValidation) {
				if len(v.Vocabulary.ProhibitedTerms) != 1 || v.Vocabulary.ProhibitedTerms[0] != "software" {
					t.Errorf("ProhibitedTerms = %v", v.Vocabulary.ProhibitedTerms)
				}
			},
		},
	}

	for _, test := range tests {
		t.Run(test.name, func(t *testing.T) {
			validation := validateExhibit(test.content)
			if validation.Valid() != test.wantValid {
				t.Errorf("Valid = %t, want %t; errors: %v", validation.Valid(), test.wantValid, validation.Errors)
			}
			if test.check != nil {
				test.check(t, validation)
			}
		})
	}
}

func makeExhibit(wordCount, questionCount int, allQuestions bool) string {
	words := make([]string, wordCount)
	for index := range words {
		words[index] = fmt.Sprintf("word%d", index+1)
	}
	questions := make([]string, questionCount)
	for index := range questions {
		suffix := "?"
		if !allQuestions && index == questionCount-1 {
			suffix = "."
		}
		questions[index] = fmt.Sprintf("%d. Reflection question%s", index+1, suffix)
	}
	return "# A Journey\n## Narrative\n" + strings.Join(words, " ") +
		"\n## Visitor questions\n" + strings.Join(questions, "\n")
}
