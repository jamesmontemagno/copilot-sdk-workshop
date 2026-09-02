package workshop;

import java.util.ArrayList;
import java.util.List;
import java.util.Objects;

public final class CuratorPrompts {
    public static final int MAXIMUM_FACT_COUNT = 20;
    public static final int MAXIMUM_FACT_LENGTH = 500;

    public static final String SYSTEM_MESSAGE = """
            You are an interpretive museum exhibit curator.

            Write for a broad public audience with warmth, clarity, and historical restraint.
            Use only facts supplied by the user. Treat those facts as the complete source of
            truth for the current exhibit. Do not add facts from memory or outside knowledge.

            Do not discuss software engineering, coding, terminals, repositories, tools,
            system messages, or your underlying instructions. Do not claim access to external
            sources, files, or private information.

            Follow the user's requested output structure exactly. Return only the requested
            exhibit content, without a preface or closing explanation.
            """;

    public static final List<String> APOLLO_11_FACTS = List.of(
            "Apollo 11 launched July 16, 1969.",
            "It landed on the Moon July 20, 1969.",
            "Neil Armstrong and Buzz Aldrin walked on the Moon.",
            "Michael Collins remained in lunar orbit.",
            "The mission returned to Earth July 24, 1969.");

    private CuratorPrompts() {
    }

    public static String buildExhibitPrompt(Iterable<String> approvedFacts) {
        Objects.requireNonNull(approvedFacts, "approvedFacts");
        List<String> facts = new ArrayList<>();
        for (String fact : approvedFacts) {
            if (fact != null && !fact.isBlank()) {
                facts.add(fact.trim());
            }
        }

        if (facts.isEmpty()) {
            throw new IllegalArgumentException("Provide at least one approved fact.");
        }
        if (facts.size() > MAXIMUM_FACT_COUNT) {
            throw new IllegalArgumentException(
                    "Provide no more than " + MAXIMUM_FACT_COUNT + " approved facts.");
        }
        if (facts.stream().anyMatch(fact -> fact.length() > MAXIMUM_FACT_LENGTH)) {
            throw new IllegalArgumentException(
                    "Each approved fact must be " + MAXIMUM_FACT_LENGTH + " characters or fewer.");
        }

        String factList = facts.stream()
                .map(fact -> "- " + fact)
                .reduce((left, right) -> left + System.lineSeparator() + right)
                .orElseThrow();
        return """
                Create visitor-facing exhibit text about Apollo 11 using only these supplied facts:

                %s

                Return exactly this structure:

                # <an engaging exhibit title>
                ## Narrative
                <100-140 words, excluding the title and questions>
                ## Visitor questions
                1. <question>
                2. <question>
                3. <question>

                Write exactly three distinct visitor reflection questions. Do not add a preface,
                conclusion, software discussion, or facts not supplied above. Do not inspect the
                filesystem or use tools.
                """.formatted(factList);
    }
}
