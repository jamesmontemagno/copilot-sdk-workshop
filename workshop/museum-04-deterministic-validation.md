# Validate the exhibit deterministically

> **Time:** 25 minutes  
> **Goal:** Add a pure validator and prove valid and missing-Narrative behavior.

The validator checks one level-one title, both required sections, a 100-140-word narrative, exactly
three numbered questions ending in question marks, and prohibited software vocabulary. It has no SDK
dependency, so it is fast and deterministic.

The result composes `TitleValidation`, `NarrativeValidation`,
`VisitorQuestionsValidation`, and `VocabularyValidation`. Each component stores only observed
measurements; presence, limits, component validity, and overall validity are derived.

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

Create `museum-workshop-app/tests/ExhibitValidatorTests.cs`:

```csharp
using MuseumExhibitStudio;

namespace MuseumExhibitStudio.Tests;

public sealed class ExhibitValidatorTests
{
    [Fact]
    public void ValidateAcceptsACompleteExhibit()
    {
        var validation = ExhibitValidator.Validate(CreateExhibit(110, 3));

        Assert.True(validation.Valid);
        Assert.Equal(110, validation.Narrative.WordCount);
        Assert.Equal(3, validation.VisitorQuestions.QuestionCount);
    }

    [Fact]
    public void ValidateRejectsMissingTitle()
    {
        var validation = ExhibitValidator.Validate(
            CreateExhibit(110, 3).Replace("# A Journey\n", string.Empty));

        Assert.False(validation.Title.Present);
        Assert.False(validation.Valid);
    }

    [Theory]
    [InlineData(99)]
    [InlineData(141)]
    public void ValidateRejectsNarrativeOutsideLimit(int wordCount)
    {
        var validation = ExhibitValidator.Validate(CreateExhibit(wordCount, 3));

        Assert.False(validation.Narrative.WithinLimit);
        Assert.False(validation.Valid);
    }

    [Theory]
    [InlineData(2)]
    [InlineData(4)]
    public void ValidateRejectsWrongQuestionCount(int questionCount)
    {
        var validation = ExhibitValidator.Validate(CreateExhibit(110, questionCount));

        Assert.False(validation.VisitorQuestions.ExactlyThree);
        Assert.False(validation.Valid);
    }

    [Fact]
    public void ValidateRejectsItemsThatAreNotQuestions()
    {
        var validation = ExhibitValidator.Validate(
            CreateExhibit(110, 3).Replace("3. Reflection question?", "3. Reflection prompt."));

        Assert.False(validation.VisitorQuestions.AllItemsAreQuestions);
        Assert.False(validation.Valid);
    }

    [Fact]
    public void ValidateReportsProhibitedVocabulary()
    {
        var validation = ExhibitValidator.Validate(
            CreateExhibit(110, 3).Replace("word1", "software"));

        Assert.Contains("software", validation.Vocabulary.ProhibitedTerms);
        Assert.False(validation.Valid);
    }

    private static string CreateExhibit(int narrativeWordCount, int questionCount)
    {
        var narrative = string.Join(' ', Enumerable.Range(1, narrativeWordCount).Select(index => $"word{index}"));
        var questions = string.Join(
            '\n',
            Enumerable.Range(1, questionCount).Select(index => $"{index}. Reflection question?"));

        return $"""
            # A Journey
            ## Narrative
            {narrative}
            ## Visitor questions
            {questions}
            """;
    }
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

Create `museum-workshop-app/tests/validator.test.ts`:

```typescript
import assert from "node:assert/strict";
import test from "node:test";
import { validateExhibit } from "../src/validator.js";

test("validator accepts narrative boundaries", () => {
  for (const count of [100, 140]) {
    const result = validateExhibit(createExhibit(count, 3));
    assert.equal(result.valid, true);
    assert.equal(result.narrative.wordCount, count);
  }
});

test("validator rejects narrative outside boundaries", () => {
  for (const count of [99, 141]) {
    assert.equal(validateExhibit(createExhibit(count, 3)).narrative.withinLimit, false);
  }
});

test("validator requires exactly one title and both sections", () => {
  const valid = createExhibit(110, 3);
  assert.equal(validateExhibit(valid.replace("# A Journey\n", "")).title.present, false);
  assert.equal(validateExhibit(`${valid}\n# Another`).title.present, false);
  assert.equal(validateExhibit(valid.replace("## Narrative\n", "")).narrative.present, false);
  assert.equal(
    validateExhibit(valid.replace("## Visitor questions\n", "")).visitorQuestions.present,
    false,
  );
});

test("validator requires exactly three numbered questions ending in question marks", () => {
  assert.equal(validateExhibit(createExhibit(110, 2)).visitorQuestions.exactlyThree, false);
  assert.equal(validateExhibit(createExhibit(110, 4)).visitorQuestions.exactlyThree, false);
  assert.equal(
    validateExhibit(createExhibit(110, 3).replace("3. Reflection question?", "3. Reflection prompt."))
      .visitorQuestions.allItemsAreQuestions,
    false,
  );
});

test("validator reports every prohibited term case-insensitively", () => {
  const result = validateExhibit(
    createExhibit(105, 3).replace(
      "word1 word2 word3 word4 word5",
      "SOFTWARE codebase repository terminal GitHub Copilot",
    ),
  );
  assert.deepEqual(result.vocabulary.prohibitedTerms, [
    "software", "codebase", "repository", "terminal", "GitHub Copilot",
  ]);
  assert.equal(result.valid, false);
});

function createExhibit(narrativeWordCount: number, questionCount: number): string {
  const narrative = Array.from({ length: narrativeWordCount }, (_, index) => `word${index + 1}`).join(" ");
  const questions = Array.from({ length: questionCount }, (_, index) => `${index + 1}. Reflection question?`).join("\n");
  return `# A Journey\n## Narrative\n${narrative}\n## Visitor questions\n${questions}`;
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

Create `museum-workshop-app/tests/test_exhibit_validator.py`:

```python
import unittest

from exhibit_validator import validate_exhibit


def create_exhibit(word_count: int, question_count: int = 3) -> str:
    narrative = " ".join(f"word{index}" for index in range(1, word_count + 1))
    questions = "\n".join(
        f"{index}. Reflection question?" for index in range(1, question_count + 1)
    )
    return (
        f"# A Journey\n## Narrative\n{narrative}\n"
        f"## Visitor questions\n{questions}"
    )


class ExhibitValidatorTests(unittest.TestCase):
    def test_accepts_complete_exhibit_at_both_word_boundaries(self) -> None:
        for word_count in (100, 140):
            with self.subTest(word_count=word_count):
                validation = validate_exhibit(create_exhibit(word_count))
                self.assertTrue(validation.valid)
                self.assertEqual(word_count, validation.narrative.word_count)

    def test_rejects_word_counts_outside_boundaries(self) -> None:
        for word_count in (99, 141):
            with self.subTest(word_count=word_count):
                self.assertFalse(
                    validate_exhibit(create_exhibit(word_count)).narrative.within_limit
                )

    def test_requires_exactly_one_title_and_both_sections(self) -> None:
        exhibit = create_exhibit(110)
        self.assertFalse(validate_exhibit(exhibit.replace("# A Journey\n", "")).valid)
        self.assertFalse(validate_exhibit(f"# Extra\n{exhibit}").valid)
        self.assertFalse(validate_exhibit(exhibit.replace("## Narrative", "Narrative")).valid)
        self.assertFalse(
            validate_exhibit(
                exhibit.replace("## Visitor questions", "Visitor questions")
            ).valid
        )

    def test_requires_exactly_three_numbered_questions(self) -> None:
        for count in (2, 4):
            with self.subTest(count=count):
                self.assertFalse(
                    validate_exhibit(
                        create_exhibit(110, count)
                    ).visitor_questions.exactly_three
                )

    def test_requires_every_numbered_item_to_end_in_question_mark(self) -> None:
        exhibit = create_exhibit(110).replace(
            "3. Reflection question?", "3. Reflection prompt."
        )
        self.assertFalse(
            validate_exhibit(exhibit).visitor_questions.all_items_are_questions
        )

    def test_rejects_prohibited_vocabulary_case_insensitively(self) -> None:
        validation = validate_exhibit(
            create_exhibit(110).replace("word1", "GITHUB COPILOT")
        )
        self.assertIn("GitHub Copilot", validation.vocabulary.prohibited_terms)
        self.assertFalse(validation.valid)


if __name__ == "__main__":
    unittest.main()
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

Create `museum-workshop-app/validator_test.go`:

```go
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
```
:::

:::language rust
Append the following validator and result type to `museum-workshop-app/src/lib.rs`:

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

Create `museum-workshop-app/tests/validator.rs`:

```rust
use museum_exhibit_studio::validate_exhibit;

fn valid() -> String {
    let words = (1..=110).map(|i| format!("word{i}")).collect::<Vec<_>>().join(" ");
    format!("# A Journey\n## Narrative\n{words}\n## Visitor questions\n\
1. What do you notice?\n2. What would you ask?\n3. What will you remember?")
}

#[test]
fn valid_and_missing_narrative() {
    assert!(validate_exhibit(&valid()).is_valid());
    let result = validate_exhibit(&valid().replacen("## Narrative\n", "", 1));
    assert!(!result.narrative.present);
    assert!(!result.is_valid());
}
```
:::

:::language java
Create `museum-workshop-app/src/main/java/workshop/TitleValidation.java`:

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

Create `museum-workshop-app/src/main/java/workshop/NarrativeValidation.java`:

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

Create `museum-workshop-app/src/main/java/workshop/VisitorQuestionsValidation.java`:

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

Create `museum-workshop-app/src/main/java/workshop/VocabularyValidation.java`:

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

Create `museum-workshop-app/src/main/java/workshop/ExhibitValidation.java`:

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

Create `museum-workshop-app/src/test/java/workshop/ExhibitValidatorTest.java`:

```java
package workshop;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.stream.IntStream;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;

class ExhibitValidatorTest {
    @Test
    void acceptsCompleteExhibit() {
        ExhibitValidation validation = ExhibitValidator.validate(createExhibit(110, 3));

        assertTrue(validation.valid());
        assertEquals(110, validation.narrative().wordCount());
        assertEquals(3, validation.visitorQuestions().questionCount());
    }

    @Test
    void rejectsMissingOrMultipleTitle() {
        assertFalse(ExhibitValidator.validate(
                createExhibit(110, 3).replace("# A Journey\n", "")).title().present());
        assertFalse(ExhibitValidator.validate(
                createExhibit(110, 3) + "\n# Another title").title().present());
    }

    @ParameterizedTest
    @ValueSource(ints = {99, 141})
    void rejectsNarrativeOutsideLimit(int words) {
        ExhibitValidation validation = ExhibitValidator.validate(createExhibit(words, 3));
        assertFalse(validation.narrative().withinLimit());
        assertFalse(validation.valid());
    }

    @ParameterizedTest
    @ValueSource(ints = {2, 4})
    void rejectsWrongQuestionCount(int count) {
        assertFalse(ExhibitValidator.validate(createExhibit(110, count))
                .visitorQuestions().exactlyThree());
    }

    @Test
    void rejectsItemsThatAreNotQuestions() {
        ExhibitValidation validation = ExhibitValidator.validate(
                createExhibit(110, 3).replace("3. Reflection question?", "3. Reflection prompt."));
        assertFalse(validation.visitorQuestions().allItemsAreQuestions());
        assertFalse(validation.valid());
    }

    @Test
    void reportsProhibitedVocabularyAndMissingSections() {
        ExhibitValidation prohibited = ExhibitValidator.validate(
                createExhibit(110, 3).replace("word1", "software"));
        assertTrue(prohibited.vocabulary().prohibitedTerms().contains("software"));
        assertFalse(prohibited.valid());

        ExhibitValidation missing = ExhibitValidator.validate("# Title\n" + "word ".repeat(110));
        assertFalse(missing.narrative().present());
        assertFalse(missing.visitorQuestions().present());
        assertFalse(missing.valid());
    }

    private static String createExhibit(int wordCount, int questionCount) {
        String narrative = IntStream.rangeClosed(1, wordCount)
                .mapToObj(index -> "word" + index)
                .reduce((left, right) -> left + " " + right)
                .orElse("");
        String questions = IntStream.rangeClosed(1, questionCount)
                .mapToObj(index -> index + ". Reflection question?")
                .reduce((left, right) -> left + "\n" + right)
                .orElse("");
        return "# A Journey\n## Narrative\n%s\n## Visitor questions\n%s"
                .formatted(narrative, questions);
    }
}
```
:::

## Preserve the factual-grounding boundary

Passing these checks does **not** prove that every sentence came from the approved facts. Every
application track will display:

> Structural checks do not prove factual grounding. Unsupported claims require human review or a
> separate evaluator.

Do not turn that disclaimer into a success-shaped "grounded" boolean.

## Run it

:::language dotnet
```bash
dotnet test museum-workshop-app/tests/museum-exhibit-studio.Tests.csproj
```
:::
:::language nodejs
```bash
npm --prefix museum-workshop-app test
```
:::
:::language python
```bash
PYTHONPATH=museum-workshop-app museum-workshop-app/.venv/bin/python -m unittest discover -s museum-workshop-app/tests -p test_exhibit_validator.py
```
:::
:::language go
```bash
go -C museum-workshop-app test -run ValidateExhibit ./...
```
:::
:::language rust
```bash
cargo test --manifest-path museum-workshop-app/Cargo.toml --locked --test validator
```
:::
:::language java
```bash
mvn -f museum-workshop-app/pom.xml -Dtest=ExhibitValidatorTest test
```
:::

Pass condition: valid output passes; deleting `## Narrative` makes both the section flag and overall
result false.

## Check your understanding

1. Which exhibit claims can code determine?
2. Why does structural validity not prove factual grounding?
3. Why is the validator independent from the SDK?
