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
