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
