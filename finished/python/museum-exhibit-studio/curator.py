from __future__ import annotations

import asyncio
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any

from copilot import CopilotSession, MCPStdioServerConfig, define_tool
from copilot.rpc import PermissionDecision, PermissionDecisionApproveOnce, PermissionDecisionReject
from copilot.session_events import (
    AssistantMessageData,
    AssistantMessageDeltaData,
    SessionErrorData,
    SessionIdleData,
    ToolExecutionCompleteData,
    ToolExecutionStartData,
)

GENERATION_TIMEOUT_SECONDS = 120
RESEARCH_TIMEOUT_SECONDS = 90
MAXIMUM_FACT_COUNT = 20
MAXIMUM_FACT_LENGTH = 500
EXHIBIT_FILE_NAME = "exhibit.html"
APPROVED_FACT_LOOKUP_NAME = "approved_fact_lookup"
WIKIPEDIA_TOOLS = ["wikipedia-search", "wikipedia-readArticle"]

apollo11_facts = (
    "Apollo 11 launched July 16, 1969.",
    "It landed on the Moon July 20, 1969.",
    "Neil Armstrong and Buzz Aldrin walked on the Moon.",
    "Michael Collins remained in lunar orbit.",
    "The mission returned to Earth July 24, 1969.",
)

great_barrier_reef_facts = (
    "The Great Barrier Reef lies off the coast of Queensland, Australia.",
    "It stretches for about 2,300 kilometres.",
    "It is made up of more than 2,900 individual reefs.",
    "It was added to the UNESCO World Heritage List in 1981.",
    "Rising sea temperatures have caused repeated coral bleaching events.",
)

terracotta_army_facts = (
    "The Terracotta Army was buried near the tomb of China's first emperor, Qin Shi Huang.",
    "Farmers digging a well discovered the site in 1974.",
    "The pits contain thousands of life-sized clay soldiers.",
    "Each figure was assembled from moulded parts and finished by hand.",
    "The site sits near the modern city of Xi'an in Shaanxi Province.",
)


@dataclass(frozen=True)
class FactSet:
    key: str
    label: str
    facts: tuple[str, ...]


FACT_SETS = (
    FactSet("apollo11", "Apollo 11", apollo11_facts),
    FactSet("reef", "Great Barrier Reef", great_barrier_reef_facts),
    FactSet("terracotta", "Terracotta Army", terracotta_army_facts),
)


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


@dataclass(frozen=True)
class Source:
    title: str
    url: str


@dataclass(frozen=True)
class ExtractedSources:
    body: str
    sources: tuple[Source, ...]


PROHIBITED_VOCABULARY = (
    "software",
    "codebase",
    "repository",
    "terminal",
    "GitHub Copilot",
)
_TITLE_PATTERN = re.compile(r"^# [^#].*$")
_WORD_PATTERN = re.compile(r"[^\W_]+(?:['\u2019-][^\W_]+)*", re.UNICODE)
_QUESTION_PATTERN = re.compile(r"^\s*\d+\.\s+(.+?)\s*$")
_SOURCE_HEADING_PATTERN = re.compile(r"(?im)^##\s+Sources\s*$")
_SOURCE_LINE_PATTERN = re.compile(r"^\s*-\s*(.+):\s*(https://\S+)\s*$")


def bound_facts(facts: Iterable[str]) -> list[str]:
    bounded = [fact.strip() for fact in facts if fact.strip()]
    if not bounded:
        raise ValueError("Provide at least one approved fact.")
    if len(bounded) > MAXIMUM_FACT_COUNT:
        raise ValueError("Provide no more than 20 approved facts.")
    if any(len(fact) > MAXIMUM_FACT_LENGTH for fact in bounded):
        raise ValueError("Each approved fact must be 500 characters or fewer.")
    return bounded


# The application owns the approved facts. This tool is the only way the curator can read them.
def create_approved_fact_lookup(facts: Iterable[str]):
    approved_facts = bound_facts(facts)

    @define_tool(
        name=APPROVED_FACT_LOOKUP_NAME,
        description=(
            "Returns the complete list of educator-approved facts this application holds "
            "for the current exhibit."
        ),
        skip_permission=True,
    )
    def approved_fact_lookup() -> list[str]:
        return list(approved_facts)

    return approved_fact_lookup


async def stream_exhibit(
    session: CopilotSession,
    prompt: str,
    timeout: float = GENERATION_TIMEOUT_SECONDS,
) -> str:
    done = asyncio.Event()
    chunks: list[str] = []
    error: RuntimeError | None = None
    received_delta = False

    def on_event(event: Any) -> None:
        nonlocal error, received_delta
        match event.data:
            case AssistantMessageDeltaData(delta_content=delta) if delta:
                received_delta = True
                chunks.append(delta)
                print(delta, end="", flush=True)
            case AssistantMessageData(content=content) if content and not received_delta:
                chunks.append(content)
                print(content, end="", flush=True)
            case ToolExecutionStartData(tool_name=name):
                print(f"\n[tool:start] {name}")
            case ToolExecutionCompleteData(success=success):
                print(f"[tool:done] success={_format_bool(success)}")
            case SessionErrorData(message=message):
                error = RuntimeError(message)
                done.set()
            case SessionIdleData():
                print()
                done.set()

    unsubscribe = session.on(on_event)
    try:
        await session.send(prompt)
        try:
            await asyncio.wait_for(done.wait(), timeout=timeout)
        except TimeoutError as timeout_error:
            raise TimeoutError("session response timeout") from timeout_error
        if error is not None:
            raise error
        return "".join(chunks)
    finally:
        unsubscribe()


def validate_exhibit(content: str) -> ExhibitValidation:
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
    narrative_validation = NarrativeValidation(narrative_index >= 0, narrative_word_count)
    visitor_questions = VisitorQuestionsValidation(
        questions_index >= 0,
        len(questions),
        bool(questions) and all(question.endswith("?") for question in questions),
    )
    vocabulary = VocabularyValidation(
        tuple(term for term in PROHIBITED_VOCABULARY if term.casefold() in content.casefold())
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


def format_validation(validation: ExhibitValidation) -> str:
    lines = [
        "Structural checks passed." if validation.valid else "Structural checks found issues:",
        f"- One level-one title: {_format_bool(validation.title.present)}",
        f"- Narrative section: {_format_bool(validation.narrative.present)}",
        "- Narrative length: "
        f"{validation.narrative.word_count} words "
        f"(within 100-140: {_format_bool(validation.narrative.within_limit)})",
        f"- Visitor questions section: {_format_bool(validation.visitor_questions.present)}",
        "- Numbered questions: "
        f"{validation.visitor_questions.question_count} "
        f"(exactly three: {_format_bool(validation.visitor_questions.exactly_three)})",
        "- Every item is a question: "
        f"{_format_bool(validation.visitor_questions.all_items_are_questions)}",
        "- Prohibited vocabulary: "
        f"{', '.join(validation.vocabulary.prohibited_terms) if validation.vocabulary.prohibited_terms else 'none'}",
    ]
    lines.extend(f"  - {message}" for message in validation.errors)
    lines.append("")
    lines.append(
        "Structural checks do not prove factual grounding. Unsupported claims require "
        "human review or a separate evaluator."
    )
    return "\n".join(lines)


def wikipedia_server() -> MCPStdioServerConfig:
    # SessionConfig expects this under mcp_servers={"wikipedia": wikipedia_server()}.
    return MCPStdioServerConfig(
        command="npx",
        args=["-y", "wikipedia-mcp@1.0.3"],
        working_directory=str(Path.cwd()),
        tools=["search", "readArticle"],
    )


def wikipedia_permission_handler() -> Callable[[Any, Any], PermissionDecision]:
    allowed_tools = {"search", "readArticle", "wikipedia-search", "wikipedia-readArticle"}

    def handler(request: Any, _invocation: Any) -> PermissionDecision:
        server_name = getattr(request, "server_name", getattr(request, "serverName", None))
        tool_name = getattr(request, "tool_name", getattr(request, "toolName", None))
        if (
            getattr(request, "kind", None) == "mcp"
            and server_name == "wikipedia"
            and tool_name in allowed_tools
        ):
            return PermissionDecisionApproveOnce()
        return PermissionDecisionReject(
            feedback="This session allows only the scoped Wikipedia search and article tools."
        )

    return handler


def extract_sources(content: str) -> ExtractedSources:
    matches = list(_SOURCE_HEADING_PATTERN.finditer(content))
    if not matches:
        return ExtractedSources(content.strip(), ())

    heading = matches[-1]
    body = content[: heading.start()].rstrip()
    source_lines = content[heading.end() :].splitlines()
    sources: list[Source] = []
    for line in source_lines:
        match = _SOURCE_LINE_PATTERN.fullmatch(line)
        if match:
            title, url = match.groups()
            sources.append(Source(title.strip(), url.strip()))
    return ExtractedSources(body, tuple(sources))


def exhibit_write_permission(working_directory: str) -> Callable[[Any, Any], PermissionDecision]:
    root = Path(working_directory).resolve()
    exhibit_path = (root / EXHIBIT_FILE_NAME).resolve()

    def handler(request: Any, _invocation: Any) -> PermissionDecision:
        file_name = getattr(request, "file_name", getattr(request, "fileName", None))
        if getattr(request, "kind", None) == "write" and isinstance(file_name, str):
            candidate = Path(file_name)
            candidate = candidate if candidate.is_absolute() else root / candidate
            if candidate.resolve() == exhibit_path:
                return PermissionDecisionApproveOnce()
        return PermissionDecisionReject(
            feedback="This session allows writing only exhibit.html in the application working directory."
        )

    return handler


def ask_line(question: str) -> str:
    return input(question).strip()


def ask_yes_no(question: str, default_yes: bool) -> bool:
    prompt = " [Y/n]: " if default_yes else " [y/N]: "
    answer = input(f"{question}{prompt}").strip().casefold()
    if not answer:
        return default_yes
    return answer == "y" or answer == "yes"


def read_facts() -> list[str]:
    print("Enter one approved fact per line. Submit a blank line when finished:")
    facts: list[str] = []
    while True:
        fact = input().strip()
        if not fact:
            return facts
        facts.append(fact)


def _find_heading(lines: list[str], heading: str) -> int:
    expected = heading.casefold()
    return next(
        (index for index, line in enumerate(lines) if line.strip().casefold() == expected),
        -1,
    )


def _format_bool(value: bool) -> str:
    return "true" if value else "false"
