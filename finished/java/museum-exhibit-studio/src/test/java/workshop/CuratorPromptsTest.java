package workshop;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.Collections;
import java.util.List;
import org.junit.jupiter.api.Test;

class CuratorPromptsTest {
    @Test
    void promptContainsFactsAndRequiredStructure() {
        String prompt = CuratorPrompts.buildExhibitPrompt(CuratorPrompts.APOLLO_11_FACTS);

        CuratorPrompts.APOLLO_11_FACTS.forEach(fact -> assertTrue(prompt.contains(fact)));
        assertTrue(prompt.contains("# <an engaging exhibit title>"));
        assertTrue(prompt.contains("## Narrative"));
        assertTrue(prompt.contains("## Visitor questions"));
        assertFalse(CuratorPrompts.SYSTEM_MESSAGE.contains(CuratorPrompts.APOLLO_11_FACTS.get(0)));
    }

    @Test
    void promptRejectsEmptyFacts() {
        assertThrows(IllegalArgumentException.class,
                () -> CuratorPrompts.buildExhibitPrompt(Collections.emptyList()));
    }

    @Test
    void promptBoundsFactInput() {
        assertThrows(IllegalArgumentException.class,
                () -> CuratorPrompts.buildExhibitPrompt(
                        Collections.nCopies(CuratorPrompts.MAXIMUM_FACT_COUNT + 1, "Approved fact.")));
        assertThrows(IllegalArgumentException.class,
                () -> CuratorPrompts.buildExhibitPrompt(
                        List.of("a".repeat(CuratorPrompts.MAXIMUM_FACT_LENGTH + 1))));
    }
}
