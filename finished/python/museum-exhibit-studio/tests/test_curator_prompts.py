import unittest

from curator_prompts import (
    APOLLO_11_FACTS,
    MAXIMUM_FACT_COUNT,
    MAXIMUM_FACT_LENGTH,
    SYSTEM_MESSAGE,
    build_exhibit_prompt,
)


class CuratorPromptsTests(unittest.TestCase):
    def test_prompt_contains_facts_and_required_structure(self) -> None:
        prompt = build_exhibit_prompt(APOLLO_11_FACTS)
        for fact in APOLLO_11_FACTS:
            self.assertIn(fact, prompt)
        self.assertIn("# <an engaging exhibit title>", prompt)
        self.assertIn("## Narrative", prompt)
        self.assertIn("## Visitor questions", prompt)
        self.assertNotIn(APOLLO_11_FACTS[0], SYSTEM_MESSAGE)

    def test_rejects_empty_facts(self) -> None:
        with self.assertRaisesRegex(ValueError, "at least one approved fact"):
            build_exhibit_prompt([])

    def test_accepts_fact_limits(self) -> None:
        prompt = build_exhibit_prompt(
            ["a" * MAXIMUM_FACT_LENGTH] * MAXIMUM_FACT_COUNT
        )
        self.assertIn("a" * MAXIMUM_FACT_LENGTH, prompt)

    def test_rejects_fact_count_and_length_above_limits(self) -> None:
        with self.assertRaisesRegex(ValueError, "no more than 20"):
            build_exhibit_prompt(["Approved fact."] * (MAXIMUM_FACT_COUNT + 1))
        with self.assertRaisesRegex(ValueError, "500 characters or fewer"):
            build_exhibit_prompt(["a" * (MAXIMUM_FACT_LENGTH + 1)])


if __name__ == "__main__":
    unittest.main()
