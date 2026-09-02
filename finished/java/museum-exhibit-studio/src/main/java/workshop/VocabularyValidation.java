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
