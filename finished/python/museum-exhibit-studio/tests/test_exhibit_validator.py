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
