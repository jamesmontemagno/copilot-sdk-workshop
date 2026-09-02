package workshop;

public record VisitorQuestionsValidation(
        boolean present,
        int questionCount,
        boolean allItemsAreQuestions) {
    public boolean exactlyThree() {
        return questionCount == 3;
    }

    public boolean valid() {
        return present && exactlyThree() && allItemsAreQuestions;
    }
}
