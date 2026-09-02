# Validate the exhibit deterministically

> **Time:** 15 minutes
> **Goal:** Add the structural validator the finished application ships with, and print its result
> after every generated exhibit.

Previous: [Ground the exhibit in approved facts](museum-03-approved-facts.md)

The lesson 3 draft looked right. "Looked right" is not a result you can act on. This lesson adds
application code that answers the same questions the same way every time, with no model involved:

| Check | Rule |
|---|---|
| Title | Exactly one level-one Markdown title |
| Narrative | A `## Narrative` section exists |
| Narrative length | 100-140 words between the narrative heading and the questions heading |
| Visitor questions | A `## Visitor questions` section exists |
| Question count | Exactly three numbered items |
| Question form | Every numbered item ends with `?` |
| Vocabulary | None of `software`, `codebase`, `repository`, `terminal`, `GitHub Copilot` |

Each check reports its own measured value, not just pass or fail, so a failed run tells you what to
change.

Draw the boundary clearly before you write the code: these checks prove **shape**. A perfectly
structured exhibit can still claim that the crew planted a flag on the far side of the Moon.
Deterministic validation cannot detect that, which is why the CLI prints a standing disclaimer
underneath the result and why lesson 6 adds a human review step.

:::language dotnet
Create `museum-workshop-app/ExhibitValidator.cs`:

```csharp
using System.Text.RegularExpressions;

namespace MuseumExhibitStudio;

public sealed record TitleValidation(int TitleCount)
{
    public bool Present => TitleCount == 1;
    public bool Valid => Present;
}

public sealed record NarrativeValidation(bool Present, int WordCount)
{
    public bool WithinLimit => WordCount is >= 100 and <= 140;
    public bool Valid => Present && WithinLimit;
}

public sealed record VisitorQuestionsValidation(
    bool Present,
    int QuestionCount,
    bool AllItemsAreQuestions)
{
    public bool ExactlyThree => QuestionCount == 3;
    public bool Valid => Present && ExactlyThree && AllItemsAreQuestions;
}

public sealed record VocabularyValidation(IReadOnlyList<string> ProhibitedTerms)
{
    public bool Valid => ProhibitedTerms.Count == 0;
}

public sealed record ExhibitValidation(
    TitleValidation Title,
    NarrativeValidation Narrative,
    VisitorQuestionsValidation VisitorQuestions,
    VocabularyValidation Vocabulary,
    IReadOnlyList<string> Errors)
{
    public bool Valid => Errors.Count == 0;
}

public static partial class ExhibitValidator
{
    private static readonly string[] ProhibitedVocabulary =
    [
        "software",
        "codebase",
        "repository",
        "terminal",
        "GitHub Copilot"
    ];

    public static ExhibitValidation Validate(string content)
    {
        ArgumentNullException.ThrowIfNull(content);

        var lines = content.ReplaceLineEndings("\n").Split('\n');
        var titleCount = lines.Count(line => TitlePattern().IsMatch(line));
        var narrativeIndex = FindHeading(lines, "## Narrative");
        var questionsIndex = FindHeading(lines, "## Visitor questions");

        var narrative = narrativeIndex >= 0 && questionsIndex > narrativeIndex
            ? string.Join(' ', lines[(narrativeIndex + 1)..questionsIndex])
            : string.Empty;
        var narrativeWordCount = WordPattern().Matches(narrative).Count;

        var questions = questionsIndex >= 0
            ? lines[(questionsIndex + 1)..]
                .Select(line => QuestionPattern().Match(line))
                .Where(match => match.Success)
                .Select(match => match.Groups[1].Value.Trim())
                .ToArray()
            : [];

        var title = new TitleValidation(titleCount);
        var narrativeValidation = new NarrativeValidation(
            narrativeIndex >= 0,
            narrativeWordCount);
        var visitorQuestions = new VisitorQuestionsValidation(
            questionsIndex >= 0,
            questions.Length,
            questions.Length > 0 && questions.All(question => question.EndsWith('?')));
        var vocabulary = new VocabularyValidation(Array.AsReadOnly(
            ProhibitedVocabulary
                .Where(term => content.Contains(term, StringComparison.OrdinalIgnoreCase))
                .ToArray()));

        var errors = new List<string>();
        if (!title.Valid)
        {
            errors.Add("The exhibit must contain exactly one level-one title.");
        }
        if (!narrativeValidation.Present)
        {
            errors.Add("The exhibit must contain a Narrative section.");
        }
        if (!narrativeValidation.WithinLimit)
        {
            errors.Add($"The narrative must contain 100-140 words; found {narrativeWordCount}.");
        }
        if (!visitorQuestions.Present)
        {
            errors.Add("The exhibit must contain a Visitor questions section.");
        }
        if (!visitorQuestions.ExactlyThree)
        {
            errors.Add($"The exhibit must contain exactly three numbered questions; found {questions.Length}.");
        }
        if (!visitorQuestions.AllItemsAreQuestions)
        {
            errors.Add("Every numbered visitor item must end with a question mark.");
        }
        if (!vocabulary.Valid)
        {
            errors.Add($"The exhibit contains prohibited vocabulary: {string.Join(", ", vocabulary.ProhibitedTerms)}.");
        }

        return new ExhibitValidation(
            title,
            narrativeValidation,
            visitorQuestions,
            vocabulary,
            errors.AsReadOnly());
    }

    private static int FindHeading(string[] lines, string heading) =>
        Array.FindIndex(lines, line => line.Trim().Equals(heading, StringComparison.OrdinalIgnoreCase));

    [GeneratedRegex(@"^# [^#].*$")]
    private static partial Regex TitlePattern();

    [GeneratedRegex(@"\b[\p{L}\p{N}]+(?:['’-][\p{L}\p{N}]+)*\b")]
    private static partial Regex WordPattern();

    [GeneratedRegex(@"^\s*\d+\.\s+(.+?)\s*$")]
    private static partial Regex QuestionPattern();
}
```

Replace `museum-workshop-app/Program.cs`:

```csharp
using MuseumExhibitStudio;

Console.WriteLine("=== Museum Exhibit Studio ===");
Console.WriteLine("Curator policy: replace-mode system message, no tools allowed.");
Console.WriteLine("Approved Apollo 11 facts:");
for (var index = 0; index < CuratorPrompts.Apollo11Facts.Count; index++)
{
    Console.WriteLine($"{index + 1}. {CuratorPrompts.Apollo11Facts[index]}");
}

var prompt = CuratorPrompts.BuildExhibitPrompt(CuratorPrompts.Apollo11Facts);
Console.WriteLine("\nBounded prompt sent to the curator:");
Console.WriteLine("--------");
Console.WriteLine(prompt);
Console.WriteLine("--------");

await using var client = new CopilotCuratorClient();
await client.StartAsync();
try
{
    await using var session = await client.CreateSessionAsync(
        MuseumExhibitService.CreateSessionConfiguration(
            Environment.GetEnvironmentVariable("COPILOT_MODEL")));
    var content = await session.SendAndWaitAsync(prompt, TimeSpan.FromMinutes(2)) ?? string.Empty;
    Console.WriteLine($"\n{content}\n");
    PrintValidation(ExhibitValidator.Validate(content));
}
finally
{
    await client.StopAsync();
}

static void PrintValidation(ExhibitValidation validation)
{
    Console.WriteLine(validation.Valid
        ? "Structural checks passed."
        : "Structural checks found issues:");

    Console.WriteLine($"- One level-one title: {validation.Title.Present}");
    Console.WriteLine($"- Narrative section: {validation.Narrative.Present}");
    Console.WriteLine(
        $"- Narrative length: {validation.Narrative.WordCount} words " +
        $"(within 100-140: {validation.Narrative.WithinLimit})");
    Console.WriteLine($"- Visitor questions section: {validation.VisitorQuestions.Present}");
    Console.WriteLine(
        $"- Numbered questions: {validation.VisitorQuestions.QuestionCount} " +
        $"(exactly three: {validation.VisitorQuestions.ExactlyThree})");
    Console.WriteLine($"- Every item is a question: {validation.VisitorQuestions.AllItemsAreQuestions}");

    foreach (var error in validation.Errors)
    {
        Console.WriteLine($"  - {error}");
    }

    Console.WriteLine(
        "\nStructural checks do not prove factual grounding. " +
        "Unsupported claims require human review or a separate evaluator.");
}
```
:::

:::language nodejs
Create `museum-workshop-app/src/validator.ts`:

```typescript
export class TitleValidation {
  constructor(readonly titleCount: number) {}
  get present(): boolean { return this.titleCount === 1; }
  get valid(): boolean { return this.present; }
}

export class NarrativeValidation {
  constructor(readonly present: boolean, readonly wordCount: number) {}
  get withinLimit(): boolean { return this.wordCount >= 100 && this.wordCount <= 140; }
  get valid(): boolean { return this.present && this.withinLimit; }
}

export class VisitorQuestionsValidation {
  constructor(
    readonly present: boolean,
    readonly questionCount: number,
    readonly allItemsAreQuestions: boolean,
  ) {}
  get exactlyThree(): boolean { return this.questionCount === 3; }
  get valid(): boolean { return this.present && this.exactlyThree && this.allItemsAreQuestions; }
}

export class VocabularyValidation {
  readonly prohibitedTerms: readonly string[];
  constructor(prohibitedTerms: readonly string[]) {
    this.prohibitedTerms = Object.freeze([...prohibitedTerms]);
  }
  get valid(): boolean { return this.prohibitedTerms.length === 0; }
}

export class ExhibitValidation {
  readonly errors: readonly string[];
  constructor(
    readonly title: TitleValidation,
    readonly narrative: NarrativeValidation,
    readonly visitorQuestions: VisitorQuestionsValidation,
    readonly vocabulary: VocabularyValidation,
    errors: readonly string[],
  ) {
    this.errors = Object.freeze([...errors]);
  }
  get valid(): boolean { return this.errors.length === 0; }
}

const prohibitedVocabulary = ["software", "codebase", "repository", "terminal", "GitHub Copilot"];
const titlePattern = /^# [^#].*$/;
const wordPattern = /\b[\p{L}\p{N}]+(?:['’-][\p{L}\p{N}]+)*\b/gu;
const questionPattern = /^\s*\d+\.\s+(.+?)\s*$/;

export function validateExhibit(content: string): ExhibitValidation {
  const lines = content.replace(/\r\n?/g, "\n").split("\n");
  const titleCount = lines.filter((line) => titlePattern.test(line)).length;
  const narrativeIndex = findHeading(lines, "## Narrative");
  const questionsIndex = findHeading(lines, "## Visitor questions");
  const narrative = narrativeIndex >= 0 && questionsIndex > narrativeIndex
    ? lines.slice(narrativeIndex + 1, questionsIndex).join(" ")
    : "";
  const narrativeWordCount = [...narrative.matchAll(wordPattern)].length;
  const questions = questionsIndex >= 0
    ? lines.slice(questionsIndex + 1)
      .map((line) => line.match(questionPattern)?.[1]?.trim())
      .filter((question): question is string => question !== undefined)
    : [];
  const title = new TitleValidation(titleCount);
  const narrativeValidation = new NarrativeValidation(
    narrativeIndex >= 0,
    narrativeWordCount,
  );
  const visitorQuestions = new VisitorQuestionsValidation(
    questionsIndex >= 0,
    questions.length,
    questions.length > 0 && questions.every((question) => question.endsWith("?")),
  );
  const vocabulary = new VocabularyValidation(prohibitedVocabulary.filter((term) =>
    content.toLocaleLowerCase().includes(term.toLocaleLowerCase())));
  const errors: string[] = [];

  if (!title.valid) errors.push("The exhibit must contain exactly one level-one title.");
  if (!narrativeValidation.present) errors.push("The exhibit must contain a Narrative section.");
  if (!narrativeValidation.withinLimit) errors.push(`The narrative must contain 100-140 words; found ${narrativeWordCount}.`);
  if (!visitorQuestions.present) errors.push("The exhibit must contain a Visitor questions section.");
  if (!visitorQuestions.exactlyThree) errors.push(`The exhibit must contain exactly three numbered questions; found ${questions.length}.`);
  if (!visitorQuestions.allItemsAreQuestions) errors.push("Every numbered visitor item must end with a question mark.");
  if (!vocabulary.valid) {
    errors.push(`The exhibit contains prohibited vocabulary: ${vocabulary.prohibitedTerms.join(", ")}.`);
  }

  return new ExhibitValidation(title, narrativeValidation, visitorQuestions, vocabulary, errors);
}

function findHeading(lines: string[], heading: string): number {
  const normalized = heading.toLocaleLowerCase();
  return lines.findIndex((line) => line.trim().toLocaleLowerCase() === normalized);
}
```

Replace `museum-workshop-app/src/index.ts`:

```typescript
import { apollo11Facts, buildExhibitPrompt } from "./prompts.js";
import {
  createCopilotCuratorClient,
  createSessionConfiguration,
  type CuratorSession,
} from "./service.js";
import { validateExhibit, type ExhibitValidation } from "./validator.js";

console.log("=== Museum Exhibit Studio ===");
console.log("Curator policy: replace-mode system message, no tools allowed.");
console.log("Approved Apollo 11 facts:");
apollo11Facts.forEach((fact, index) => console.log(`${index + 1}. ${fact}`));

const prompt = buildExhibitPrompt(apollo11Facts);
console.log("\nBounded prompt sent to the curator:");
console.log("--------");
console.log(prompt);
console.log("--------");

const client = createCopilotCuratorClient();
let session: CuratorSession | undefined;
await client.start();
try {
  session = await client.createSession(
    createSessionConfiguration(process.env.COPILOT_MODEL),
  );
  const response = await session.sendAndWait(prompt, 120_000);
  const content = response?.data.content ?? "";
  console.log(`\n${content}\n`);
  printValidation(validateExhibit(content));
} finally {
  await session?.disconnect();
  await client.stop();
}

function printValidation(validation: ExhibitValidation): void {
  console.log(validation.valid ? "Structural checks passed." : "Structural checks found issues:");
  console.log(`- One level-one title: ${validation.title.present}`);
  console.log(`- Narrative section: ${validation.narrative.present}`);
  console.log(`- Narrative length: ${validation.narrative.wordCount} words (within 100-140: ${validation.narrative.withinLimit})`);
  console.log(`- Visitor questions section: ${validation.visitorQuestions.present}`);
  console.log(`- Numbered questions: ${validation.visitorQuestions.questionCount} (exactly three: ${validation.visitorQuestions.exactlyThree})`);
  console.log(`- Every item is a question: ${validation.visitorQuestions.allItemsAreQuestions}`);
  validation.errors.forEach((error) => console.log(`  - ${error}`));
  console.log("\nStructural checks do not prove factual grounding. Unsupported claims require human review or a separate evaluator.");
}
```
:::

:::language python
Create `museum-workshop-app/exhibit_validator.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
import re

PROHIBITED_VOCABULARY = (
    "software",
    "codebase",
    "repository",
    "terminal",
    "GitHub Copilot",
)

_TITLE_PATTERN = re.compile(r"^# [^#].*$")
_WORD_PATTERN = re.compile(r"[^\W_]+(?:['’-][^\W_]+)*", re.UNICODE)
_QUESTION_PATTERN = re.compile(r"^\s*\d+\.\s+(.+?)\s*$")


@dataclass(frozen=True)
class TitleValidation:
    title_count: int

    @property
    def present(self) -> bool:
        return self.title_count == 1

    @property
    def valid(self) -> bool:
        return self.present


@dataclass(frozen=True)
class NarrativeValidation:
    present: bool
    word_count: int

    @property
    def within_limit(self) -> bool:
        return 100 <= self.word_count <= 140

    @property
    def valid(self) -> bool:
        return self.present and self.within_limit


@dataclass(frozen=True)
class VisitorQuestionsValidation:
    present: bool
    question_count: int
    all_items_are_questions: bool

    @property
    def exactly_three(self) -> bool:
        return self.question_count == 3

    @property
    def valid(self) -> bool:
        return self.present and self.exactly_three and self.all_items_are_questions


@dataclass(frozen=True)
class VocabularyValidation:
    prohibited_terms: tuple[str, ...]

    @property
    def valid(self) -> bool:
        return not self.prohibited_terms


@dataclass(frozen=True)
class ExhibitValidation:
    title: TitleValidation
    narrative: NarrativeValidation
    visitor_questions: VisitorQuestionsValidation
    vocabulary: VocabularyValidation
    errors: tuple[str, ...]

    @property
    def valid(self) -> bool:
        return not self.errors


def validate_exhibit(content: str) -> ExhibitValidation:
    if content is None:
        raise TypeError("content cannot be None")

    lines = content.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    title_count = sum(bool(_TITLE_PATTERN.fullmatch(line)) for line in lines)
    narrative_index = _find_heading(lines, "## Narrative")
    questions_index = _find_heading(lines, "## Visitor questions")

    narrative = (
        " ".join(lines[narrative_index + 1 : questions_index])
        if narrative_index >= 0 and questions_index > narrative_index
        else ""
    )
    narrative_word_count = len(_WORD_PATTERN.findall(narrative))
    questions = (
        tuple(
            match.group(1).strip()
            for line in lines[questions_index + 1 :]
            if (match := _QUESTION_PATTERN.fullmatch(line))
        )
        if questions_index >= 0
        else ()
    )
    title = TitleValidation(title_count)
    narrative_validation = NarrativeValidation(
        present=narrative_index >= 0,
        word_count=narrative_word_count,
    )
    visitor_questions = VisitorQuestionsValidation(
        present=questions_index >= 0,
        question_count=len(questions),
        all_items_are_questions=bool(questions)
        and all(question.endswith("?") for question in questions),
    )
    vocabulary = VocabularyValidation(
        tuple(
            term
            for term in PROHIBITED_VOCABULARY
            if term.casefold() in content.casefold()
        )
    )

    errors: list[str] = []
    if not title.valid:
        errors.append("The exhibit must contain exactly one level-one title.")
    if not narrative_validation.present:
        errors.append("The exhibit must contain a Narrative section.")
    if not narrative_validation.within_limit:
        errors.append(
            f"The narrative must contain 100-140 words; found {narrative_word_count}."
        )
    if not visitor_questions.present:
        errors.append("The exhibit must contain a Visitor questions section.")
    if not visitor_questions.exactly_three:
        errors.append(
            "The exhibit must contain exactly three numbered questions; "
            f"found {len(questions)}."
        )
    if not visitor_questions.all_items_are_questions:
        errors.append("Every numbered visitor item must end with a question mark.")
    if not vocabulary.valid:
        errors.append(
            "The exhibit contains prohibited vocabulary: "
            f"{', '.join(vocabulary.prohibited_terms)}."
        )

    return ExhibitValidation(
        title=title,
        narrative=narrative_validation,
        visitor_questions=visitor_questions,
        vocabulary=vocabulary,
        errors=tuple(errors),
    )


def _find_heading(lines: list[str], heading: str) -> int:
    expected = heading.casefold()
    return next(
        (index for index, line in enumerate(lines) if line.strip().casefold() == expected),
        -1,
    )
```

Replace `museum-workshop-app/main.py`:

```python
from __future__ import annotations

import asyncio
import os

from copilot import CopilotClient

from curator_prompts import APOLLO_11_FACTS, build_exhibit_prompt
from exhibit_validator import ExhibitValidation, validate_exhibit
from museum_exhibit_service import create_session_configuration

GROUNDING_DISCLAIMER = (
    "Structural checks do not prove factual grounding. "
    "Unsupported claims require human review or a separate evaluator."
)


def print_validation(validation: ExhibitValidation) -> None:
    print(
        "Structural checks passed."
        if validation.valid
        else "Structural checks found issues:"
    )
    print(f"- One level-one title: {validation.title.present}")
    print(f"- Narrative section: {validation.narrative.present}")
    print(
        f"- Narrative length: {validation.narrative.word_count} words "
        f"(within 100-140: {validation.narrative.within_limit})"
    )
    print(f"- Visitor questions section: {validation.visitor_questions.present}")
    print(
        f"- Numbered questions: {validation.visitor_questions.question_count} "
        f"(exactly three: {validation.visitor_questions.exactly_three})"
    )
    print(
        "- Every item is a question: "
        f"{validation.visitor_questions.all_items_are_questions}"
    )
    for error in validation.errors:
        print(f"  - {error}")
    print(f"\n{GROUNDING_DISCLAIMER}")


async def main() -> None:
    print("=== Museum Exhibit Studio ===")
    print("Curator policy: replace-mode system message, no tools allowed.")
    print("Approved Apollo 11 facts:")
    for index, fact in enumerate(APOLLO_11_FACTS, start=1):
        print(f"{index}. {fact}")

    prompt = build_exhibit_prompt(APOLLO_11_FACTS)
    print("\nBounded prompt sent to the curator:")
    print("--------")
    print(prompt)
    print("--------")

    client = CopilotClient()
    session = None
    await client.start()
    try:
        session = await client.create_session(
            **create_session_configuration(os.getenv("COPILOT_MODEL"))
        )
        response = await session.send_and_wait(prompt, timeout=120.0)
        content = response.data.content or ""
        print(f"\n{content}\n")
        print_validation(validate_exhibit(content))
    finally:
        if session is not None:
            await session.disconnect()
        await client.stop()


if __name__ == "__main__":
    asyncio.run(main())
```
:::

:::language go
Create `museum-workshop-app/validator.go`:

```go
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
```

Replace `museum-workshop-app/main.go`:

```go
package main

import (
	"context"
	"errors"
	"fmt"
	"os"
	"time"
)

func main() {
	fmt.Println("=== Museum Exhibit Studio ===")
	fmt.Println("Curator policy: replace-mode system message, no tools allowed.")
	fmt.Println("Approved Apollo 11 facts:")
	for index, fact := range apollo11Facts {
		fmt.Printf("%d. %s\n", index+1, fact)
	}

	if err := draftExhibit(); err != nil {
		fmt.Fprintln(os.Stderr, "Could not generate the exhibit:", err)
		os.Exit(1)
	}
}

func draftExhibit() (err error) {
	prompt, err := buildExhibitPrompt(apollo11Facts)
	if err != nil {
		return err
	}
	fmt.Println("\nBounded prompt sent to the curator:")
	fmt.Println("--------")
	fmt.Println(prompt)
	fmt.Println("--------")

	ctx := context.Background()
	client := newCopilotCuratorClient()
	if err = client.Start(ctx); err != nil {
		return err
	}
	defer func() { err = errors.Join(err, client.Stop()) }()

	session, err := client.CreateSession(ctx, createSessionConfiguration(os.Getenv("COPILOT_MODEL")))
	if err != nil {
		return err
	}
	defer func() { err = errors.Join(err, session.Disconnect()) }()

	generationContext, cancel := context.WithTimeout(ctx, 2*time.Minute)
	defer cancel()
	content, err := session.SendAndWait(generationContext, prompt)
	if err != nil {
		return err
	}
	fmt.Printf("\n%s\n\n", content)
	printValidation(validateExhibit(content))
	return nil
}

func printValidation(validation ExhibitValidation) {
	if validation.Valid() {
		fmt.Println("Structural checks passed.")
	} else {
		fmt.Println("Structural checks found issues:")
	}
	fmt.Printf("- One level-one title: %t\n", validation.Title.Present())
	fmt.Printf("- Narrative section: %t\n", validation.Narrative.Present)
	fmt.Printf("- Narrative length: %d words (within 100-140: %t)\n", validation.Narrative.WordCount, validation.Narrative.WithinLimit())
	fmt.Printf("- Visitor questions section: %t\n", validation.VisitorQuestions.Present)
	fmt.Printf("- Numbered questions: %d (exactly three: %t)\n", validation.VisitorQuestions.QuestionCount, validation.VisitorQuestions.ExactlyThree())
	fmt.Printf("- Every item is a question: %t\n", validation.VisitorQuestions.AllItemsAreQuestions)
	for _, message := range validation.Errors {
		fmt.Println("  -", message)
	}
	fmt.Println("\nStructural checks do not prove factual grounding. Unsupported claims require human review or a separate evaluator.")
}
```
:::

:::language rust
Add the validator to `museum-workshop-app/src/lib.rs`, below `build_exhibit_prompt`:

```rust
const PROHIBITED_VOCABULARY: [&str; 5] = [
    "software",
    "codebase",
    "repository",
    "terminal",
    "GitHub Copilot",
];

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct TitleValidation {
    pub title_count: usize,
}

impl TitleValidation {
    pub fn is_present(&self) -> bool {
        self.title_count == 1
    }

    pub fn is_valid(&self) -> bool {
        self.is_present()
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct NarrativeValidation {
    pub present: bool,
    pub word_count: usize,
}

impl NarrativeValidation {
    pub fn is_within_limit(&self) -> bool {
        (100..=140).contains(&self.word_count)
    }

    pub fn is_valid(&self) -> bool {
        self.present && self.is_within_limit()
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct VisitorQuestionsValidation {
    pub present: bool,
    pub question_count: usize,
    pub all_items_are_questions: bool,
}

impl VisitorQuestionsValidation {
    pub fn has_exactly_three(&self) -> bool {
        self.question_count == 3
    }

    pub fn is_valid(&self) -> bool {
        self.present && self.has_exactly_three() && self.all_items_are_questions
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct VocabularyValidation {
    pub prohibited_terms: Vec<&'static str>,
}

impl VocabularyValidation {
    pub fn is_valid(&self) -> bool {
        self.prohibited_terms.is_empty()
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ExhibitValidation {
    pub title: TitleValidation,
    pub narrative: NarrativeValidation,
    pub visitor_questions: VisitorQuestionsValidation,
    pub vocabulary: VocabularyValidation,
    pub errors: Vec<String>,
}

impl ExhibitValidation {
    pub fn is_valid(&self) -> bool {
        self.errors.is_empty()
    }
}

pub fn validate_exhibit(content: &str) -> ExhibitValidation {
    let lines: Vec<&str> = content.lines().collect();
    let title_count = lines
        .iter()
        .filter(|line| {
            line.strip_prefix("# ")
                .is_some_and(|title| !title.is_empty() && !title.starts_with('#'))
        })
        .count();
    let narrative_index = find_heading(&lines, "## Narrative");
    let questions_index = find_heading(&lines, "## Visitor questions");
    let narrative = match (narrative_index, questions_index) {
        (Some(start), Some(end)) if end > start => lines[start + 1..end].join(" "),
        _ => String::new(),
    };
    let narrative_word_count = count_words(&narrative);
    let questions: Vec<&str> = questions_index
        .map(|index| {
            lines[index + 1..]
                .iter()
                .filter_map(|line| numbered_item(line))
                .collect()
        })
        .unwrap_or_default();
    let lower_content = content.to_lowercase();
    let prohibited_terms: Vec<&'static str> = PROHIBITED_VOCABULARY
        .iter()
        .copied()
        .filter(|term| lower_content.contains(&term.to_lowercase()))
        .collect();

    let title = TitleValidation { title_count };
    let narrative_validation = NarrativeValidation {
        present: narrative_index.is_some(),
        word_count: narrative_word_count,
    };
    let visitor_questions = VisitorQuestionsValidation {
        present: questions_index.is_some(),
        question_count: questions.len(),
        all_items_are_questions: !questions.is_empty()
            && questions.iter().all(|question| question.ends_with('?')),
    };
    let vocabulary = VocabularyValidation { prohibited_terms };
    let mut errors = Vec::new();
    if !title.is_valid() {
        errors.push("The exhibit must contain exactly one level-one title.".to_owned());
    }
    if !narrative_validation.present {
        errors.push("The exhibit must contain a Narrative section.".to_owned());
    }
    if !narrative_validation.is_within_limit() {
        errors.push(format!(
            "The narrative must contain 100-140 words; found {narrative_word_count}."
        ));
    }
    if !visitor_questions.present {
        errors.push("The exhibit must contain a Visitor questions section.".to_owned());
    }
    if !visitor_questions.has_exactly_three() {
        errors.push(format!(
            "The exhibit must contain exactly three numbered questions; found {}.",
            questions.len()
        ));
    }
    if !visitor_questions.all_items_are_questions {
        errors.push("Every numbered visitor item must end with a question mark.".to_owned());
    }
    if !vocabulary.is_valid() {
        errors.push(format!(
            "The exhibit contains prohibited vocabulary: {}.",
            vocabulary.prohibited_terms.join(", ")
        ));
    }

    ExhibitValidation {
        title,
        narrative: narrative_validation,
        visitor_questions,
        vocabulary,
        errors,
    }
}

fn find_heading(lines: &[&str], heading: &str) -> Option<usize> {
    lines
        .iter()
        .position(|line| line.trim().eq_ignore_ascii_case(heading))
}

fn numbered_item(line: &str) -> Option<&str> {
    let trimmed = line.trim_start();
    let digit_count = trimmed.chars().take_while(char::is_ascii_digit).count();
    if digit_count == 0 {
        return None;
    }
    let remainder = &trimmed[digit_count..];
    let item = remainder.strip_prefix(". ")?.trim();
    (!item.is_empty()).then_some(item)
}

fn count_words(text: &str) -> usize {
    text.split(|character: char| {
        !(character.is_alphanumeric() || matches!(character, '\'' | '’' | '-'))
    })
    .filter(|word| word.chars().any(char::is_alphanumeric))
    .count()
}
```

Replace `museum-workshop-app/src/main.rs`:

```rust
use std::time::Duration;

use museum_exhibit_studio::{
    APOLLO_11_FACTS, CopilotCuratorClient, CuratorClient, CuratorSession, ExhibitValidation,
    RuntimeError, build_exhibit_prompt, create_session_configuration, validate_exhibit,
};

fn print_validation(validation: &ExhibitValidation) {
    println!(
        "{}",
        if validation.is_valid() {
            "Structural checks passed."
        } else {
            "Structural checks found issues:"
        }
    );
    println!("- One level-one title: {}", validation.title.is_present());
    println!("- Narrative section: {}", validation.narrative.present);
    println!(
        "- Narrative length: {} words (within 100-140: {})",
        validation.narrative.word_count,
        validation.narrative.is_within_limit()
    );
    println!(
        "- Visitor questions section: {}",
        validation.visitor_questions.present
    );
    println!(
        "- Numbered questions: {} (exactly three: {})",
        validation.visitor_questions.question_count,
        validation.visitor_questions.has_exactly_three()
    );
    println!(
        "- Every item is a question: {}",
        validation.visitor_questions.all_items_are_questions
    );
    for error in &validation.errors {
        println!("  - {error}");
    }
    println!(
        "\nStructural checks do not prove factual grounding. Unsupported claims require human review or a separate evaluator."
    );
}

async fn draft_exhibit() -> Result<(), RuntimeError> {
    let facts: Vec<String> = APOLLO_11_FACTS.map(str::to_owned).to_vec();
    let prompt = build_exhibit_prompt(&facts)?;
    println!("\nBounded prompt sent to the curator:");
    println!("--------");
    println!("{prompt}");
    println!("--------");

    let mut client = CopilotCuratorClient::new();
    client.start().await?;
    let mut session = client
        .create_session(create_session_configuration(
            std::env::var("COPILOT_MODEL").ok().as_deref(),
        ))
        .await?;
    let response = session
        .send_and_wait(prompt, Duration::from_secs(120))
        .await;
    session.disconnect().await?;
    client.stop().await?;

    let content = response?.unwrap_or_default();
    println!("\n{content}\n");
    print_validation(&validate_exhibit(&content));
    Ok(())
}

#[tokio::main]
async fn main() {
    println!("=== Museum Exhibit Studio ===");
    println!("Curator policy: replace-mode system message, no tools allowed.");
    println!("Approved Apollo 11 facts:");
    for (index, fact) in APOLLO_11_FACTS.iter().enumerate() {
        println!("{}. {fact}", index + 1);
    }

    if let Err(error) = draft_exhibit().await {
        eprintln!("Could not generate the exhibit: {error}");
        std::process::exit(1);
    }
}
```
:::

:::language java
Create the five result records under `museum-workshop-app/src/main/java/workshop/`.

`TitleValidation.java`:

```java
package workshop;

public record TitleValidation(long titleCount) {
    public boolean present() {
        return titleCount == 1;
    }

    public boolean valid() {
        return present();
    }
}
```

`NarrativeValidation.java`:

```java
package workshop;

public record NarrativeValidation(boolean present, int wordCount) {
    public boolean withinLimit() {
        return wordCount >= 100 && wordCount <= 140;
    }

    public boolean valid() {
        return present && withinLimit();
    }
}
```

`VisitorQuestionsValidation.java`:

```java
package workshop;

public record VisitorQuestionsValidation(
        boolean present,
        int questionCount,
        boolean allItemsAreQuestions) {
    public boolean exactlyThree() {
        return questionCount == 3;
    }

    public boolean valid() {
        return present && exactlyThree() && allItemsAreQuestions;
    }
}
```

`VocabularyValidation.java`:

```java
package workshop;

import java.util.List;

public record VocabularyValidation(List<String> prohibitedTerms) {
    public VocabularyValidation {
        prohibitedTerms = List.copyOf(prohibitedTerms);
    }

    public boolean valid() {
        return prohibitedTerms.isEmpty();
    }
}
```

`ExhibitValidation.java`:

```java
package workshop;

import java.util.List;

public record ExhibitValidation(
        TitleValidation title,
        NarrativeValidation narrative,
        VisitorQuestionsValidation visitorQuestions,
        VocabularyValidation vocabulary,
        List<String> errors) {
    public ExhibitValidation {
        errors = List.copyOf(errors);
    }

    public boolean valid() {
        return errors.isEmpty();
    }
}
```

Create `museum-workshop-app/src/main/java/workshop/ExhibitValidator.java`:

```java
package workshop;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Locale;
import java.util.regex.Pattern;

public final class ExhibitValidator {
    private static final List<String> PROHIBITED_VOCABULARY = List.of(
            "software", "codebase", "repository", "terminal", "GitHub Copilot");
    private static final Pattern TITLE_PATTERN = Pattern.compile("^# [^#].*$");
    private static final Pattern WORD_PATTERN =
            Pattern.compile("\\b[\\p{L}\\p{N}]+(?:['’\\-][\\p{L}\\p{N}]+)*\\b");
    private static final Pattern QUESTION_PATTERN = Pattern.compile("^\\s*\\d+\\.\\s+(.+?)\\s*$");

    private ExhibitValidator() {
    }

    public static ExhibitValidation validate(String content) {
        if (content == null) {
            throw new NullPointerException("content");
        }

        String[] lines = content.replace("\r\n", "\n").replace('\r', '\n').split("\n", -1);
        long titleCount = Arrays.stream(lines).filter(line -> TITLE_PATTERN.matcher(line).matches()).count();
        int narrativeIndex = findHeading(lines, "## Narrative");
        int questionsIndex = findHeading(lines, "## Visitor questions");
        String narrative = narrativeIndex >= 0 && questionsIndex > narrativeIndex
                ? String.join(" ", Arrays.copyOfRange(lines, narrativeIndex + 1, questionsIndex))
                : "";
        int narrativeWordCount = (int) WORD_PATTERN.matcher(narrative).results().count();

        List<String> questions = questionsIndex >= 0
                ? Arrays.stream(Arrays.copyOfRange(lines, questionsIndex + 1, lines.length))
                        .map(QUESTION_PATTERN::matcher)
                        .filter(java.util.regex.Matcher::matches)
                        .map(matcher -> matcher.group(1).trim())
                        .toList()
                : List.of();
        String normalized = content.toLowerCase(Locale.ROOT);
        List<String> prohibitedTerms = PROHIBITED_VOCABULARY.stream()
                .filter(term -> normalized.contains(term.toLowerCase(Locale.ROOT)))
                .toList();

        TitleValidation title = new TitleValidation(titleCount);
        NarrativeValidation narrativeValidation =
                new NarrativeValidation(narrativeIndex >= 0, narrativeWordCount);
        VisitorQuestionsValidation visitorQuestions = new VisitorQuestionsValidation(
                questionsIndex >= 0,
                questions.size(),
                !questions.isEmpty() && questions.stream().allMatch(question -> question.endsWith("?")));
        VocabularyValidation vocabulary = new VocabularyValidation(prohibitedTerms);

        List<String> errors = new ArrayList<>();
        if (!title.valid()) {
            errors.add("The exhibit must contain exactly one level-one title.");
        }
        if (!narrativeValidation.present()) {
            errors.add("The exhibit must contain a Narrative section.");
        }
        if (!narrativeValidation.withinLimit()) {
            errors.add("The narrative must contain 100-140 words; found " + narrativeWordCount + ".");
        }
        if (!visitorQuestions.present()) {
            errors.add("The exhibit must contain a Visitor questions section.");
        }
        if (!visitorQuestions.exactlyThree()) {
            errors.add("The exhibit must contain exactly three numbered questions; found "
                    + questions.size() + ".");
        }
        if (!visitorQuestions.allItemsAreQuestions()) {
            errors.add("Every numbered visitor item must end with a question mark.");
        }
        if (!vocabulary.valid()) {
            errors.add("The exhibit contains prohibited vocabulary: "
                    + String.join(", ", vocabulary.prohibitedTerms()) + ".");
        }

        return new ExhibitValidation(
                title,
                narrativeValidation,
                visitorQuestions,
                vocabulary,
                errors);
    }

    private static int findHeading(String[] lines, String heading) {
        for (int index = 0; index < lines.length; index++) {
            if (lines[index].trim().equalsIgnoreCase(heading)) {
                return index;
            }
        }
        return -1;
    }
}
```

Replace `museum-workshop-app/src/main/java/workshop/MuseumExhibitStudio.java`:

```java
package workshop;

public final class MuseumExhibitStudio {
    private MuseumExhibitStudio() {
    }

    public static void main(String[] args) throws Exception {
        System.out.println("=== Museum Exhibit Studio ===");
        System.out.println("Curator policy: replace-mode system message, no tools allowed.");
        System.out.println("Approved Apollo 11 facts:");
        for (int index = 0; index < CuratorPrompts.APOLLO_11_FACTS.size(); index++) {
            System.out.printf("%d. %s%n", index + 1, CuratorPrompts.APOLLO_11_FACTS.get(index));
        }

        String prompt = CuratorPrompts.buildExhibitPrompt(CuratorPrompts.APOLLO_11_FACTS);
        System.out.println("\nBounded prompt sent to the curator:");
        System.out.println("--------");
        System.out.println(prompt);
        System.out.println("--------");

        try (CuratorClient client = new CopilotCuratorClient()) {
            client.start();
            CuratorSession session = null;
            try {
                session = client.createSession(
                        MuseumExhibitService.createSessionConfiguration(
                                System.getenv("COPILOT_MODEL")));
                String content = session.sendAndWait(prompt, 120_000L);
                System.out.printf("%n%s%n%n", content);
                printValidation(ExhibitValidator.validate(content == null ? "" : content));
            } finally {
                if (session != null) {
                    session.disconnect();
                }
                client.stop();
            }
        }
    }

    private static void printValidation(ExhibitValidation validation) {
        System.out.println(validation.valid()
                ? "Structural checks passed."
                : "Structural checks found issues:");
        System.out.println("- One level-one title: " + validation.title().present());
        System.out.println("- Narrative section: " + validation.narrative().present());
        System.out.printf(
                "- Narrative length: %d words (within 100-140: %s)%n",
                validation.narrative().wordCount(),
                validation.narrative().withinLimit());
        System.out.println(
                "- Visitor questions section: " + validation.visitorQuestions().present());
        System.out.printf(
                "- Numbered questions: %d (exactly three: %s)%n",
                validation.visitorQuestions().questionCount(),
                validation.visitorQuestions().exactlyThree());
        System.out.println(
                "- Every item is a question: "
                        + validation.visitorQuestions().allItemsAreQuestions());
        validation.errors().forEach(error -> System.out.println("  - " + error));
        System.out.println("""

                Structural checks do not prove factual grounding. Unsupported claims require \
                human review or a separate evaluator.""");
    }
}
```
:::

## Run it

Build, then run. The run contacts a model and needs an authenticated GitHub Copilot CLI.

:::language dotnet
```bash
dotnet build museum-workshop-app
dotnet run --project museum-workshop-app
```
:::
:::language nodejs
```bash
npm --prefix museum-workshop-app run build
npm --prefix museum-workshop-app start
```
:::
:::language python
```bash
museum-workshop-app/.venv/bin/python -m py_compile museum-workshop-app/*.py
museum-workshop-app/.venv/bin/python museum-workshop-app/main.py
```
:::
:::language go
```bash
go -C museum-workshop-app build -mod=readonly ./...
go -C museum-workshop-app run .
```
:::
:::language rust
```bash
cargo check --manifest-path museum-workshop-app/Cargo.toml
cargo run --manifest-path museum-workshop-app/Cargo.toml
```
:::
:::language java
```bash
mvn -f museum-workshop-app/pom.xml compile
mvn -f museum-workshop-app/pom.xml compile exec:java
```
:::

After the exhibit, the run now prints a measured result:

```text
Structural checks passed.
- One level-one title: True
- Narrative section: True
- Narrative length: 126 words (within 100-140: True)
- Visitor questions section: True
- Numbered questions: 3 (exactly three: True)
- Every item is a question: True

Structural checks do not prove factual grounding. Unsupported claims require human review
or a separate evaluator.
```

Boolean spelling differs by language (`True`, `true`); the lines and their order do not.

A failing run is just as useful, and it names the measurement that missed:

```text
Structural checks found issues:
- One level-one title: True
- Narrative section: True
- Narrative length: 168 words (within 100-140: False)
- Visitor questions section: True
- Numbered questions: 4 (exactly three: False)
- Every item is a question: True
  - The narrative must contain 100-140 words; found 168.
  - The exhibit must contain exactly three numbered questions; found 4.
```

Run it a second time. The exhibit text changes; the checks stay comparable, because nothing in the
validator asks a model anything.

## Check your understanding

1. The validator reports `Narrative length: 126 words` instead of only `passed`. What can you do
   with the number that you cannot do with the verdict?
2. The prohibited vocabulary list contains `repository` and `terminal`. Which lesson 1 artifact
   already asked the curator to avoid those words, and why is this check still worth having?
3. An exhibit passes every check and states that the crew planted a flag on the far side of the
   Moon. Which line of the printed output is the honest answer to that situation?

Continue to [Own the lifecycle](museum-05-lifecycle.md).
