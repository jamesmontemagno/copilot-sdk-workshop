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
