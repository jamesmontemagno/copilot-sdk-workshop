package workshop;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.github.copilot.SystemMessageMode;
import com.github.copilot.rpc.SessionConfig;
import java.util.List;
import java.util.concurrent.TimeoutException;
import java.util.stream.IntStream;
import org.junit.jupiter.api.Test;

class MuseumExhibitServiceTest {
    @Test
    void configurationOwnsPromptAndHasNoTools() {
        SessionConfig configuration = MuseumExhibitService.createSessionConfiguration("test-model");

        assertEquals("museum-exhibit-studio", configuration.getClientName());
        assertEquals("test-model", configuration.getModel());
        assertTrue(configuration.getAvailableTools().isEmpty());
        assertFalse(configuration.isStreaming());
        assertNotNull(configuration.getOnPermissionRequest());
        assertEquals(SystemMessageMode.REPLACE, configuration.getSystemMessage().getMode());
        assertEquals(CuratorPrompts.SYSTEM_MESSAGE, configuration.getSystemMessage().getContent());
        assertEquals(120, MuseumExhibitService.GENERATION_TIMEOUT.toSeconds());
    }

    @Test
    void generateReturnsContentAndCleansUp() throws Exception {
        FakeSession session = new FakeSession(validExhibit(), null);
        FakeClient client = new FakeClient(session);

        var result = new MuseumExhibitService(client)
                .generate(CuratorPrompts.APOLLO_11_FACTS, null);

        assertTrue(result.validation().valid());
        assertTrue(result.validation().narrative().valid());
        assertTrue(client.started);
        assertTrue(client.stopped);
        assertTrue(session.disconnected);
        assertEquals(120_000, session.timeoutMillis);
        assertNotNull(client.configuration);
        CuratorPrompts.APOLLO_11_FACTS.forEach(
                fact -> assertTrue(session.prompt.contains(fact)));
    }

    @Test
    void invalidPromptNeverStartsClient() {
        FakeClient client = new FakeClient(new FakeSession(null, null));

        assertThrows(IllegalArgumentException.class,
                () -> new MuseumExhibitService(client).generate(List.of(), null));

        assertFalse(client.started);
    }

    @Test
    void generateRejectsEmptyResponseAndCleansUp() {
        FakeSession session = new FakeSession(" ", null);
        FakeClient client = new FakeClient(session);

        assertThrows(IllegalStateException.class,
                () -> new MuseumExhibitService(client)
                        .generate(CuratorPrompts.APOLLO_11_FACTS, null));

        assertTrue(client.stopped);
        assertTrue(session.disconnected);
    }

    @Test
    void generateCleansUpAfterSessionFailure() {
        FakeSession session = new FakeSession(null, new TimeoutException("Timed out."));
        FakeClient client = new FakeClient(session);

        assertThrows(TimeoutException.class,
                () -> new MuseumExhibitService(client)
                        .generate(CuratorPrompts.APOLLO_11_FACTS, null));

        assertTrue(client.stopped);
        assertTrue(session.disconnected);
    }

    @Test
    void clientStopsWhenStartupFails() {
        FakeClient client = new FakeClient(new FakeSession(null, null));
        client.startFailure = new IllegalStateException("Cannot start.");

        assertThrows(IllegalStateException.class,
                () -> new MuseumExhibitService(client)
                        .generate(CuratorPrompts.APOLLO_11_FACTS, null));

        assertTrue(client.stopped);
    }

    private static String validExhibit() {
        String narrative = IntStream.rangeClosed(1, 110)
                .mapToObj(index -> "word" + index)
                .reduce((left, right) -> left + " " + right)
                .orElseThrow();
        return """
                # A Journey
                ## Narrative
                %s
                ## Visitor questions
                1. What do you notice?
                2. What would you ask?
                3. What will you remember?
                """.formatted(narrative);
    }

    private static final class FakeClient implements CuratorClient {
        private final FakeSession session;
        private boolean started;
        private boolean stopped;
        private SessionConfig configuration;
        private Exception startFailure;

        private FakeClient(FakeSession session) {
            this.session = session;
        }

        @Override
        public void start() throws Exception {
            started = true;
            if (startFailure != null) {
                throw startFailure;
            }
        }

        @Override
        public CuratorSession createSession(SessionConfig configuration) {
            this.configuration = configuration;
            return session;
        }

        @Override
        public void stop() {
            stopped = true;
        }

        @Override
        public void close() {
        }
    }

    private static final class FakeSession implements CuratorSession {
        private final String content;
        private final Exception failure;
        private String prompt;
        private long timeoutMillis;
        private boolean disconnected;

        private FakeSession(String content, Exception failure) {
            this.content = content;
            this.failure = failure;
        }

        @Override
        public String sendAndWait(String prompt, long timeoutMillis) throws Exception {
            this.prompt = prompt;
            this.timeoutMillis = timeoutMillis;
            if (failure != null) {
                throw failure;
            }
            return content;
        }

        @Override
        public void disconnect() {
            disconnected = true;
        }
    }
}
