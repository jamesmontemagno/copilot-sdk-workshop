package workshop;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Locale;
import java.util.regex.Pattern;

public final class CuratorValidation {
    private static final List<String> PROHIBITED_VOCABULARY = List.of(
            "software", "codebase", "repository", "terminal", "GitHub Copilot");
    private static final Pattern TITLE_PATTERN = Pattern.compile("^# [^#].*$");
    private static final Pattern WORD_PATTERN =
            Pattern.compile("\\b[\\p{L}\\p{N}]+(?:['’\\-][\\p{L}\\p{N}]+)*\\b");
    private static final Pattern QUESTION_PATTERN = Pattern.compile("^\\s*\\d+\\.\\s+(.+?)\\s*$");

    private CuratorValidation() {
    }

    public static ExhibitValidation validateExhibit(String content) {
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

    public static String formatValidation(ExhibitValidation validation) {
        StringBuilder report = new StringBuilder();
        report.append(validation.valid()
                ? "Structural checks passed."
                : "Structural checks found issues:").append(System.lineSeparator());
        report.append("- One level-one title: ").append(validation.title().present()).append(System.lineSeparator());
        report.append("- Narrative section: ").append(validation.narrative().present()).append(System.lineSeparator());
        report.append("- Narrative length: ").append(validation.narrative().wordCount())
                .append(" words (within 100-140: ").append(validation.narrative().withinLimit())
                .append(")").append(System.lineSeparator());
        report.append("- Visitor questions section: ")
                .append(validation.visitorQuestions().present()).append(System.lineSeparator());
        report.append("- Numbered questions: ").append(validation.visitorQuestions().questionCount())
                .append(" (exactly three: ").append(validation.visitorQuestions().exactlyThree())
                .append(")").append(System.lineSeparator());
        report.append("- Every item is a question: ")
                .append(validation.visitorQuestions().allItemsAreQuestions()).append(System.lineSeparator());
        report.append("- Prohibited vocabulary: ")
                .append(validation.vocabulary().prohibitedTerms().isEmpty()
                        ? "none"
                        : String.join(", ", validation.vocabulary().prohibitedTerms()))
                .append(System.lineSeparator());
        validation.errors().forEach(error -> report.append("  - ").append(error).append(System.lineSeparator()));
        report.append(System.lineSeparator())
                .append("Structural checks do not prove factual grounding. Unsupported claims require human review or a separate evaluator.");
        return report.toString();
    }

    private static int findHeading(String[] lines, String heading) {
        for (int index = 0; index < lines.length; index++) {
            if (lines[index].trim().equalsIgnoreCase(heading)) {
                return index;
            }
        }
        return -1;
    }

    public record TitleValidation(long titleCount) {
        public boolean present() {
            return titleCount == 1;
        }

        public boolean valid() {
            return present();
        }
    }

    public record NarrativeValidation(boolean present, int wordCount) {
        public boolean withinLimit() {
            return wordCount >= 100 && wordCount <= 140;
        }

        public boolean valid() {
            return present && withinLimit();
        }
    }

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

    public record VocabularyValidation(List<String> prohibitedTerms) {
        public VocabularyValidation {
            prohibitedTerms = List.copyOf(prohibitedTerms);
        }

        public boolean valid() {
            return prohibitedTerms.isEmpty();
        }
    }

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
}
