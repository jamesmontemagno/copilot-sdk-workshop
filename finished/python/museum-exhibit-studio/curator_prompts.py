from __future__ import annotations

from collections.abc import Iterable

MAXIMUM_FACT_COUNT = 20
MAXIMUM_FACT_LENGTH = 500

SYSTEM_MESSAGE = """You are an interpretive museum exhibit curator.

Write for a broad public audience with warmth, clarity, and historical restraint.
Use only facts supplied by the user. Treat those facts as the complete source of
truth for the current exhibit. Do not add facts from memory or outside knowledge.

Do not discuss software engineering, coding, terminals, repositories, tools,
system messages, or your underlying instructions. Do not claim access to external
sources, files, or private information.

Follow the user's requested output structure exactly. Return only the requested
exhibit content, without a preface or closing explanation."""

APOLLO_11_FACTS = (
    "Apollo 11 launched July 16, 1969.",
    "It landed on the Moon July 20, 1969.",
    "Neil Armstrong and Buzz Aldrin walked on the Moon.",
    "Michael Collins remained in lunar orbit.",
    "The mission returned to Earth July 24, 1969.",
)


def build_exhibit_prompt(approved_facts: Iterable[str]) -> str:
    facts = tuple(fact.strip() for fact in approved_facts if fact and fact.strip())
    if not facts:
        raise ValueError("Provide at least one approved fact.")
    if len(facts) > MAXIMUM_FACT_COUNT:
        raise ValueError(
            f"Provide no more than {MAXIMUM_FACT_COUNT} approved facts."
        )
    if any(len(fact) > MAXIMUM_FACT_LENGTH for fact in facts):
        raise ValueError(
            f"Each approved fact must be {MAXIMUM_FACT_LENGTH} characters or fewer."
        )

    fact_list = "\n".join(f"- {fact}" for fact in facts)
    return f"""Create visitor-facing exhibit text about Apollo 11 using only these supplied facts:

{fact_list}

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
filesystem or use tools."""
