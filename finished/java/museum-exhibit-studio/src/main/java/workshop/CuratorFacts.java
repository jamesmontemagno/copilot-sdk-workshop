package workshop;

import com.github.copilot.rpc.ToolDefinition;

import java.util.ArrayList;
import java.util.List;
import java.util.Objects;

public final class CuratorFacts {
    public static final int MAXIMUM_FACT_COUNT = 20;
    public static final int MAXIMUM_FACT_LENGTH = 500;
    public static final String APPROVED_FACT_LOOKUP_NAME = "approved_fact_lookup";

    public static final List<String> apollo11Facts = List.of(
            "Apollo 11 launched July 16, 1969.",
            "It landed on the Moon July 20, 1969.",
            "Neil Armstrong and Buzz Aldrin walked on the Moon.",
            "Michael Collins remained in lunar orbit.",
            "The mission returned to Earth July 24, 1969.");

    public static final List<String> greatBarrierReefFacts = List.of(
            "The Great Barrier Reef lies off the coast of Queensland, Australia.",
            "It stretches for about 2,300 kilometres.",
            "It is made up of more than 2,900 individual reefs.",
            "It was added to the UNESCO World Heritage List in 1981.",
            "Rising sea temperatures have caused repeated coral bleaching events.");

    public static final List<String> terracottaArmyFacts = List.of(
            "The Terracotta Army was buried near the tomb of China's first emperor, Qin Shi Huang.",
            "Farmers digging a well discovered the site in 1974.",
            "The pits contain thousands of life-sized clay soldiers.",
            "Each figure was assembled from moulded parts and finished by hand.",
            "The site sits near the modern city of Xi'an in Shaanxi Province.");

    public static final List<FactSet> factSets = List.of(
            new FactSet("apollo11", "Apollo 11", apollo11Facts),
            new FactSet("reef", "Great Barrier Reef", greatBarrierReefFacts),
            new FactSet("terracotta", "Terracotta Army", terracottaArmyFacts));

    private CuratorFacts() {
    }

    public static List<String> boundFacts(Iterable<String> facts) {
        Objects.requireNonNull(facts, "facts");
        List<String> bounded = new ArrayList<>();
        for (String fact : facts) {
            if (fact == null) {
                continue;
            }
            String trimmed = fact.trim();
            if (!trimmed.isEmpty()) {
                bounded.add(trimmed);
            }
        }
        if (bounded.isEmpty()) {
            throw new IllegalArgumentException("Provide at least one approved fact.");
        }
        if (bounded.size() > MAXIMUM_FACT_COUNT) {
            throw new IllegalArgumentException("Provide no more than 20 approved facts.");
        }
        if (bounded.stream().anyMatch(fact -> fact.length() > MAXIMUM_FACT_LENGTH)) {
            throw new IllegalArgumentException("Each approved fact must be 500 characters or fewer.");
        }
        return List.copyOf(bounded);
    }

    // The application owns the approved facts. This tool is the only way the curator can read them.
    public static ToolDefinition approvedFactLookup(Iterable<String> facts) {
        return ToolDefinition.from(
                APPROVED_FACT_LOOKUP_NAME,
                "Returns the complete list of educator-approved facts this application holds "
                        + "for the current exhibit.",
                new ApprovedFactReader(facts)::read).skipPermission(true);
    }

    private static final class ApprovedFactReader {
        private final List<String> approvedFacts;

        private ApprovedFactReader(Iterable<String> facts) {
            this.approvedFacts = boundFacts(facts);
        }

        private String read() {
            StringBuilder builder = new StringBuilder();
            for (String fact : approvedFacts) {
                if (builder.length() > 0) {
                    builder.append('\n');
                }
                builder.append("- ").append(fact);
            }
            return builder.toString();
        }
    }

    public record FactSet(String key, String label, List<String> facts) {
        public FactSet {
            facts = List.copyOf(facts);
        }
    }
}
