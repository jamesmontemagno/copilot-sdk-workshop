package workshop;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Locale;
import java.util.regex.Pattern;

public final class ExhibitValidator {
    private static final List<String> PROHIBITED_VOCABULARY = List.of(
            "software", "codebase", "repository", "terminal", "GitHub Copilot");
    private static final Pattern TITLE_PATTERN = Pattern.compile("^# [^#].*$");
    private static final Pattern WORD_PATTERN =
            Pattern.compile("\\b[\\p{L}\\p{N}]+(?:['’\\-][\\p{L}\\p{N}]+)*\\b");
    private static final Pattern QUESTION_PATTERN = Pattern.compile("^\\s*\\d+\\.\\s+(.+?)\\s*$");

    private ExhibitValidator() {
    }

    public static ExhibitValidation validate(String content) {
        if (content == null) {
            throw new NullPointerException("content");
        }

        String[] lines = content.replace("\r\n", "\n").replace('\r', '\n').split("\n", -1);
        long titleCount = Arrays.stream(lines).filter(line -> TITLE_PATTERN.matcher(line).matches()).count();
        int narrativeIndex = findHeading(lines, "## Narrative");
        int questionsIndex = findHeading(lines, "## Visitor questions");
        String narrative = narrativeIndex >= 0 && questionsIndex > narrativeIndex
                ? String.join(" ", Arrays.copyOfRange(lines, narrativeIndex + 1, questionsIndex))
                : "";
        int narrativeWordCount = (int) WORD_PATTERN.matcher(narrative).results().count();

        List<String> questions = questionsIndex >= 0
                ? Arrays.stream(Arrays.copyOfRange(lines, questionsIndex + 1, lines.length))
                        .map(QUESTION_PATTERN::matcher)
                        .filter(java.util.regex.Matcher::matches)
                        .map(matcher -> matcher.group(1).trim())
                        .toList()
                : List.of();
        String normalized = content.toLowerCase(Locale.ROOT);
        List<String> prohibitedTerms = PROHIBITED_VOCABULARY.stream()
                .filter(term -> normalized.contains(term.toLowerCase(Locale.ROOT)))
                .toList();

        TitleValidation title = new TitleValidation(titleCount);
        NarrativeValidation narrativeValidation =
                new NarrativeValidation(narrativeIndex >= 0, narrativeWordCount);
        VisitorQuestionsValidation visitorQuestions = new VisitorQuestionsValidation(
                questionsIndex >= 0,
                questions.size(),
                !questions.isEmpty() && questions.stream().allMatch(question -> question.endsWith("?")));
        VocabularyValidation vocabulary = new VocabularyValidation(prohibitedTerms);

        List<String> errors = new ArrayList<>();
        if (!title.valid()) {
            errors.add("The exhibit must contain exactly one level-one title.");
        }
        if (!narrativeValidation.present()) {
            errors.add("The exhibit must contain a Narrative section.");
        }
        if (!narrativeValidation.withinLimit()) {
            errors.add("The narrative must contain 100-140 words; found " + narrativeWordCount + ".");
        }
        if (!visitorQuestions.present()) {
            errors.add("The exhibit must contain a Visitor questions section.");
        }
        if (!visitorQuestions.exactlyThree()) {
            errors.add("The exhibit must contain exactly three numbered questions; found "
                    + questions.size() + ".");
        }
        if (!visitorQuestions.allItemsAreQuestions()) {
            errors.add("Every numbered visitor item must end with a question mark.");
        }
        if (!vocabulary.valid()) {
            errors.add("The exhibit contains prohibited vocabulary: "
                    + String.join(", ", vocabulary.prohibitedTerms()) + ".");
        }

        return new ExhibitValidation(
                title,
                narrativeValidation,
                visitorQuestions,
                vocabulary,
                errors);
    }

    private static int findHeading(String[] lines, String heading) {
        for (int index = 0; index < lines.length; index++) {
            if (lines[index].trim().equalsIgnoreCase(heading)) {
                return index;
            }
        }
        return -1;
    }
}
