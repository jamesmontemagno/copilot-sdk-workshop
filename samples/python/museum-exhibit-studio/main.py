from __future__ import annotations

import asyncio
import os
import sys

from copilot import CopilotClient

from curator_prompts import APOLLO_11_FACTS, MAXIMUM_FACT_COUNT
from exhibit_validator import ExhibitValidation
from museum_exhibit_service import MuseumExhibitService, ResearchResult, Source

GROUNDING_DISCLAIMER = (
    "Structural checks do not prove factual grounding. "
    "Unsupported claims require human review or a separate evaluator."
)


def read_facts() -> list[str]:
    print("Enter one approved fact per line. Submit a blank line when finished:")
    facts: list[str] = []
    while fact := input().strip():
        facts.append(fact)
    return facts


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


def review_research(
    result: ResearchResult, remaining_fact_slots: int = MAXIMUM_FACT_COUNT
) -> list[str]:
    print("\nWikipedia fact review:")
    for review in result.reviews:
        print(f"- [{review.status}] {review.fact}")
        print(f"  {review.explanation}")
        if review.evidence_title and review.evidence_url:
            print(f"  Source: {review.evidence_title} — {review.evidence_url}")

    approved: list[str] = []
    for addition in result.additions:
        print(f"\nProposed addition: {addition.fact}")
        print(f"Source: {addition.source_title} — {addition.source_url}")
        if len(approved) >= remaining_fact_slots:
            print("Cannot approve this addition because the 20-fact limit is reached.")
            continue
        answer = input("Approve this addition? [y/N]: ").strip()
        if answer.casefold() == "y":
            approved.append(addition.fact)
    return approved


def print_sources(sources: tuple[Source, ...]) -> None:
    if not sources:
        return
    print("\nConsulted Wikipedia sources:")
    for source in sources:
        print(f"- {source.title}: {source.url}")


async def main() -> int:
    print("=== Museum Exhibit Studio ===")
    print("Approved Apollo 11 facts:")
    for index, fact in enumerate(APOLLO_11_FACTS, start=1):
        print(f"{index}. {fact}")

    use_defaults = input("\nUse these facts? [Y/n]: ").strip()
    facts = read_facts() if use_defaults.casefold() == "n" else list(APOLLO_11_FACTS)
    consulted_sources: tuple[Source, ...] = ()

    try:
        run_research = input("Run Wikipedia research? [y/N]: ").strip()
        if run_research.casefold() == "y":
            research = await MuseumExhibitService(CopilotClient()).research(
                facts, os.getenv("COPILOT_MODEL")
            )
            if research.completed:
                facts.extend(
                    review_research(
                        research,
                        remaining_fact_slots=MAXIMUM_FACT_COUNT - len(facts),
                    )
                )
                consulted_sources = research.consulted_sources
            else:
                print(
                    "Wikipedia research was not completed. "
                    "Generating from the original approved facts only."
                )

        studio = MuseumExhibitService(CopilotClient())
        result = await studio.generate(facts, os.getenv("COPILOT_MODEL"))
        print(f"\n{result.content}\n")
        print_validation(result.validation)
        print_sources(consulted_sources)
        return 0
    except TimeoutError:
        print("The curator did not respond within two minutes. Try again.", file=sys.stderr)
        return 1
    except Exception as error:
        print(f"Could not generate the exhibit: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
