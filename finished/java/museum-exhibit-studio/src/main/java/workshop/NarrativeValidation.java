package workshop;

public record NarrativeValidation(boolean present, int wordCount) {
    public boolean withinLimit() {
        return wordCount >= 100 && wordCount <= 140;
    }

    public boolean valid() {
        return present && withinLimit();
    }
}
