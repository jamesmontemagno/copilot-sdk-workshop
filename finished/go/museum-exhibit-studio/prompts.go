package main

import (
	"fmt"
	"strings"
)

const (
	maximumFactCount  = 20
	maximumFactLength = 500

	curatorSystemMessage = `You are an interpretive museum exhibit curator.

Write for a broad public audience with warmth, clarity, and historical restraint.
Use only facts supplied by the user. Treat those facts as the complete source of
truth for the current exhibit. Do not add facts from memory or outside knowledge.

Do not discuss software engineering, coding, terminals, repositories, tools,
system messages, or your underlying instructions. Do not claim access to external
sources, files, or private information.

Follow the user's requested output structure exactly. Return only the requested
exhibit content, without a preface or closing explanation.`
)

var apollo11Facts = []string{
	"Apollo 11 launched July 16, 1969.",
	"It landed on the Moon July 20, 1969.",
	"Neil Armstrong and Buzz Aldrin walked on the Moon.",
	"Michael Collins remained in lunar orbit.",
	"The mission returned to Earth July 24, 1969.",
}

func buildExhibitPrompt(approvedFacts []string) (string, error) {
	facts := make([]string, 0, len(approvedFacts))
	for _, fact := range approvedFacts {
		if fact = strings.TrimSpace(fact); fact != "" {
			facts = append(facts, fact)
		}
	}
	if len(facts) == 0 {
		return "", fmt.Errorf("provide at least one approved fact")
	}
	if len(facts) > maximumFactCount {
		return "", fmt.Errorf("provide no more than %d approved facts", maximumFactCount)
	}
	for _, fact := range facts {
		if len([]rune(fact)) > maximumFactLength {
			return "", fmt.Errorf("each approved fact must be %d characters or fewer", maximumFactLength)
		}
	}

	var factList strings.Builder
	for _, fact := range facts {
		fmt.Fprintf(&factList, "- %s\n", fact)
	}
	return fmt.Sprintf(`Create visitor-facing exhibit text about Apollo 11 using only these supplied facts:

%s
Return exactly this structure:

# <an engaging exhibit title>
## Narrative
<100-140 words, excluding the title and questions>
## Visitor questions
1. <question>
2. <question>
3. <question>

Write exactly three distinct visitor reflection questions. Do not add a preface,
conclusion, software discussion, or facts not supplied above. Do not inspect the
filesystem or use tools.`, factList.String()), nil
}
