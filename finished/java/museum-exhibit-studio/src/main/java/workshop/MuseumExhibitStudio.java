package workshop;

import java.util.ArrayList;
import java.util.List;
import java.util.Scanner;
import java.util.concurrent.TimeoutException;

public final class MuseumExhibitStudio {
    private MuseumExhibitStudio() {
    }

    public static void main(String[] args) {
        System.out.println("=== Museum Exhibit Studio ===");
        System.out.println("Approved Apollo 11 facts:");
        for (int index = 0; index < CuratorPrompts.APOLLO_11_FACTS.size(); index++) {
            System.out.printf("%d. %s%n", index + 1, CuratorPrompts.APOLLO_11_FACTS.get(index));
        }

        Scanner input = new Scanner(System.in);
        System.out.print("\nUse these facts? [Y/n]: ");
        String choice = input.hasNextLine() ? input.nextLine().trim() : "";
        List<String> facts = choice.equalsIgnoreCase("n")
                ? readFacts(input)
                : CuratorPrompts.APOLLO_11_FACTS;

        List<ProposedAddition> additions = List.of();
        List<ResearchSource> sources = List.of();
        System.out.print("\nRun Wikipedia research? [y/N]: ");
        String researchChoice = input.hasNextLine() ? input.nextLine().trim() : "";
        if (researchChoice.equalsIgnoreCase("y")) {
            try (var researchClient = new CopilotCuratorClient()) {
                ResearchResult research = new MuseumExhibitService(researchClient)
                        .research(facts, System.getenv("COPILOT_MODEL"));
                printResearch(research);
                if (research.completed()) {
                    additions = approveAdditions(input, research.additions());
                    sources = research.consultedSources();
                } else {
                    System.out.println(
                            "Wikipedia research was not completed. "
                                    + "Generating from the original approved facts only.");
                    if (research.failureMessage() != null) {
                        System.out.println("Research error: " + research.failureMessage());
                    }
                }
            }
        }

        List<String> approvedFacts =
                MuseumExhibitService.applyApprovedAdditions(facts, additions);
        try (var generationClient = new CopilotCuratorClient()) {
            var studio = new MuseumExhibitService(generationClient);
            var result = studio.generate(approvedFacts, System.getenv("COPILOT_MODEL"));
            System.out.printf("%n%s%n%n", result.content());
            printValidation(result.validation());
            printSources(sources);
        } catch (Exception exception) {
            if (hasCause(exception, TimeoutException.class)) {
                System.err.println("The curator did not respond within two minutes. Try again.");
            } else {
                System.err.println("Could not generate the exhibit: " + rootMessage(exception));
            }
            System.exit(1);
        }
    }

    private static void printResearch(ResearchResult research) {
        System.out.println("\nWikipedia fact review:");
        for (FactReview review : research.reviews()) {
            System.out.printf("- [%s] %s%n", review.status(), review.fact());
            System.out.println("  " + review.explanation());
            if (review.evidenceTitle() != null && review.evidenceUrl() != null) {
                System.out.printf(
                        "  Source: %s (%s)%n",
                        review.evidenceTitle(),
                        review.evidenceUrl());
            }
        }
    }

    private static List<ProposedAddition> approveAdditions(
            Scanner input, List<ProposedAddition> proposedAdditions) {
        if (proposedAdditions.isEmpty()) {
            System.out.println("\nWikipedia proposed no additions.");
            return List.of();
        }

        List<ProposedAddition> decisions = new ArrayList<>();
        System.out.println("\nProposed additions:");
        for (ProposedAddition addition : proposedAdditions) {
            System.out.println("- " + addition.fact());
            System.out.printf(
                    "  Source: %s (%s)%n",
                    addition.sourceTitle(),
                    addition.sourceUrl());
            System.out.print("  Approve this addition? [y/N]: ");
            String approval = input.hasNextLine() ? input.nextLine().trim() : "";
            decisions.add(addition.withApproved(approval.equalsIgnoreCase("y")));
        }
        return List.copyOf(decisions);
    }

    private static void printSources(List<ResearchSource> sources) {
        if (sources.isEmpty()) {
            return;
        }
        System.out.println("\nConsulted Wikipedia sources:");
        sources.forEach(source ->
                System.out.printf("- %s: %s%n", source.title(), source.url()));
    }

    private static List<String> readFacts(Scanner input) {
        System.out.println("Enter one approved fact per line. Submit a blank line when finished:");
        List<String> facts = new ArrayList<>();
        while (input.hasNextLine()) {
            String fact = input.nextLine();
            if (fact.isBlank()) {
                break;
            }
            facts.add(fact.trim());
        }
        return facts;
    }

    private static void printValidation(ExhibitValidation validation) {
        System.out.println(validation.valid()
                ? "Structural checks passed."
                : "Structural checks found issues:");
        System.out.println("- One level-one title: " + validation.title().present());
        System.out.println("- Narrative section: " + validation.narrative().present());
        System.out.printf(
                "- Narrative length: %d words (within 100-140: %s)%n",
                validation.narrative().wordCount(),
                validation.narrative().withinLimit());
        System.out.println(
                "- Visitor questions section: " + validation.visitorQuestions().present());
        System.out.printf(
                "- Numbered questions: %d (exactly three: %s)%n",
                validation.visitorQuestions().questionCount(),
                validation.visitorQuestions().exactlyThree());
        System.out.println(
                "- Every item is a question: "
                        + validation.visitorQuestions().allItemsAreQuestions());
        validation.errors().forEach(error -> System.out.println("  - " + error));
        System.out.println("""

                Structural checks do not prove factual grounding. Unsupported claims require \
                human review or a separate evaluator.""");
    }

    private static boolean hasCause(Throwable error, Class<? extends Throwable> type) {
        Throwable current = error;
        while (current != null) {
            if (type.isInstance(current)) {
                return true;
            }
            current = current.getCause();
        }
        return false;
    }

    private static String rootMessage(Throwable error) {
        Throwable current = error;
        while (current.getCause() != null) {
            current = current.getCause();
        }
        return current.getMessage() == null
                ? current.getClass().getSimpleName()
                : current.getMessage();
    }
}
