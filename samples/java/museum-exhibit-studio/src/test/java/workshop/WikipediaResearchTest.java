package workshop;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.github.copilot.rpc.PermissionInvocation;
import com.github.copilot.rpc.PermissionRequest;
import com.github.copilot.rpc.SessionConfig;
import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.InputStreamReader;
import java.io.OutputStreamWriter;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;

class WikipediaResearchTest {
    private static final List<String> FACTS =
            List.of("Apollo 11 launched July 16, 1969.");
    private static final ObjectMapper JSON = new ObjectMapper();

    @Test
    void researchConfigurationAllowsOnlyWikipediaReadTools() throws Exception {
        SessionConfig research =
                MuseumExhibitService.createResearchSessionConfiguration(" test-model ");

        assertEquals("museum-exhibit-studio-research", research.getClientName());
        assertEquals("test-model", research.getModel());
        assertFalse(research.isStreaming());
        assertEquals(
                List.of("wikipedia-search", "wikipedia-readArticle"),
                research.getAvailableTools());
        assertEquals(
                List.of("search", "readArticle"),
                research.getMcpServers().get("wikipedia").getTools());
        assertTrue(MuseumExhibitService.createSessionConfiguration(null)
                .getAvailableTools().isEmpty());

        PermissionRequest allowed = permissionRequest("wikipedia", "search");
        assertEquals(
                "approve-once",
                research.getOnPermissionRequest()
                        .handle(allowed, new PermissionInvocation())
                        .get()
                        .getKind());
        PermissionRequest denied = permissionRequest("wikipedia", "writeArticle");
        assertEquals(
                "reject",
                research.getOnPermissionRequest()
                        .handle(denied, new PermissionInvocation())
                        .get()
                        .getKind());
    }

    @Test
    void parsesMockResearchAndKeepsAdditionsSeparateUntilApproval() {
        FakeSession session =
                new FakeSession("```json\n" + validResponse() + "\n```", null);
        FakeClient client = new FakeClient(session);

        ResearchResult result = new MuseumExhibitService(client).research(FACTS, null);

        assertTrue(result.completed());
        assertEquals(FactReviewStatus.SUPPORTED, result.reviews().get(0).status());
        assertEquals(1, result.additions().size());
        assertFalse(result.additions().get(0).approved());
        assertEquals(1, result.consultedSources().size());
        assertTrue(session.prompt.indexOf("search first")
                < session.prompt.indexOf("readArticle"));
        assertEquals(45_000, session.timeoutMillis);
        assertTrue(session.disconnected);
        assertTrue(client.stopped);

        assertEquals(
                FACTS,
                MuseumExhibitService.applyApprovedAdditions(FACTS, result.additions()));
        ProposedAddition approved = result.additions().get(0).withApproved(true);
        assertEquals(
                List.of(FACTS.get(0), approved.fact()),
                MuseumExhibitService.applyApprovedAdditions(FACTS, List.of(approved)));
        assertEquals("Apollo 11", approved.sourceTitle());
        assertEquals("https://en.wikipedia.org/wiki/Apollo_11", approved.sourceUrl());
    }

    @Test
    void acceptsEmptySuggestionsWithoutInventingEvidence() {
        String response = """
                {"reviews":[{"fact":"Apollo 11 launched July 16, 1969.",
                "status":"not found","evidenceTitle":null,"evidenceUrl":null,
                "explanation":"The bounded search found no matching evidence."}],
                "additions":[],"consultedSources":[],"completed":true,"failureMessage":null}
                """;

        ResearchResult result = new MuseumExhibitService(
                new FakeClient(new FakeSession(response, null))).research(FACTS, null);

        assertTrue(result.completed());
        assertEquals(FactReviewStatus.NOT_FOUND, result.reviews().get(0).status());
        assertTrue(result.additions().isEmpty());
        assertTrue(result.consultedSources().isEmpty());
    }

    @Test
    void malformedProvenanceFallsBackToNotChecked() {
        String malformed = validResponse()
                .replace(
                        "https://en.wikipedia.org/wiki/Apollo_11",
                        "https://example.com/apollo");
        FakeSession session = new FakeSession(malformed, null);
        FakeClient client = new FakeClient(session);

        ResearchResult result = new MuseumExhibitService(client).research(FACTS, null);

        assertFalse(result.completed());
        assertEquals(FactReviewStatus.NOT_CHECKED, result.reviews().get(0).status());
        assertTrue(result.additions().isEmpty());
        assertTrue(result.failureMessage().contains("canonical Wikipedia URL"));
        assertTrue(session.disconnected);
        assertTrue(client.stopped);
    }

    @Test
    void retriesOneFormattingFailureWithoutCallingToolsAgain() {
        FakeSession session = new FakeSession(
                "I found supporting information.", validResponse(), null);
        ResearchResult result =
                new MuseumExhibitService(new FakeClient(session)).research(FACTS, null);

        assertTrue(result.completed());
        assertEquals(2, session.callCount);
        assertTrue(session.lastPrompt.contains("Do not call any tools again"));
        assertEquals(15_000, session.timeoutMillis);
    }

    @Test
    void timeoutAndStartupFailureReturnIncompleteResearch() {
        FakeClient timeoutClient = new FakeClient(
                new FakeSession(null, new TimeoutException("Research timed out.")));
        ResearchResult timeout =
                new MuseumExhibitService(timeoutClient).research(FACTS, null);
        assertFalse(timeout.completed());
        assertEquals(FactReviewStatus.NOT_CHECKED, timeout.reviews().get(0).status());
        assertTrue(timeoutClient.session.disconnected);
        assertTrue(timeoutClient.stopped);

        FakeClient startupClient = new FakeClient(new FakeSession(null, null));
        startupClient.startFailure = new IllegalStateException("Cannot start.");
        ResearchResult startup =
                new MuseumExhibitService(startupClient).research(FACTS, null);
        assertFalse(startup.completed());
        assertTrue(startup.failureMessage().contains("Cannot start."));
        assertTrue(startupClient.stopped);
    }

    @ParameterizedTest
    @ValueSource(strings = {"supported", "contradicted", "not found", "not checked"})
    void acceptsEveryDocumentedReviewStatus(String status) {
        String response =
                validResponse().replace("\"supported\"", "\"" + status + "\"");
        ResearchResult result = new MuseumExhibitService(
                new FakeClient(new FakeSession(response, null))).research(FACTS, null);
        assertTrue(result.completed());
        assertEquals(status, result.reviews().get(0).status().toString());
    }

    @Test
    void mockMcpExposesOnlyReadToolsAndRequiresSearchFirst() throws Exception {
        Path fixture = Path.of(
                System.getProperty("basedir"),
                "src",
                "test",
                "resources",
                "mock-wikipedia-mcp.mjs");
        Process process = new ProcessBuilder("node", fixture.toString()).start();
        try (BufferedWriter writer =
                        new BufferedWriter(new OutputStreamWriter(process.getOutputStream()));
                BufferedReader reader =
                        new BufferedReader(new InputStreamReader(process.getInputStream()))) {
            JsonNode tools = request(
                    writer,
                    reader,
                    """
                    {"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}
                    """);
            assertEquals(
                    List.of("search", "readArticle"),
                    tools.path("result").path("tools").findValuesAsText("name"));

            JsonNode earlyRead = request(
                    writer,
                    reader,
                    """
                    {"jsonrpc":"2.0","id":2,"method":"tools/call",
                    "params":{"name":"readArticle","arguments":{"title":"Apollo 11"}}}
                    """);
            assertEquals(
                    "search must run first",
                    earlyRead.path("error").path("message").textValue());

            request(
                    writer,
                    reader,
                    """
                    {"jsonrpc":"2.0","id":3,"method":"tools/call",
                    "params":{"name":"search","arguments":{"query":"Apollo 11"}}}
                    """);
            JsonNode article = request(
                    writer,
                    reader,
                    """
                    {"jsonrpc":"2.0","id":4,"method":"tools/call",
                    "params":{"name":"readArticle","arguments":{"title":"Apollo 11"}}}
                    """);
            assertTrue(article.path("result").path("content").get(0).path("text")
                    .textValue()
                    .contains("July 16, 1969"));
        } finally {
            process.getOutputStream().close();
            assertTrue(process.waitFor(5, TimeUnit.SECONDS));
        }
    }

    private static JsonNode request(
            BufferedWriter writer, BufferedReader reader, String request) throws Exception {
        writer.write(request.replace("\n", ""));
        writer.newLine();
        writer.flush();
        return JSON.readTree(reader.readLine());
    }

    private static PermissionRequest permissionRequest(String server, String tool) {
        PermissionRequest request = new PermissionRequest();
        request.setKind("mcp");
        request.setExtensionData(Map.of("serverName", server, "toolName", tool));
        return request;
    }

    private static String validResponse() {
        return """
                {"reviews":[{"fact":"Apollo 11 launched July 16, 1969.",
                "status":"supported","evidenceTitle":"Apollo 11",
                "evidenceUrl":"https://en.wikipedia.org/wiki/Apollo_11",
                "explanation":"The article gives the launch date."}],
                "additions":[{"fact":"Apollo 11 carried three astronauts.",
                "sourceTitle":"Apollo 11",
                "sourceUrl":"https://en.wikipedia.org/wiki/Apollo_11",
                "approved":false}],
                "consultedSources":[{"title":"Apollo 11",
                "url":"https://en.wikipedia.org/wiki/Apollo_11"}],
                "completed":true,"failureMessage":null}
                """;
    }

    private static final class FakeClient implements CuratorClient {
        private final FakeSession session;
        private boolean stopped;
        private Exception startFailure;

        private FakeClient(FakeSession session) {
            this.session = session;
        }

        @Override
        public void start() throws Exception {
            if (startFailure != null) {
                throw startFailure;
            }
        }

        @Override
        public CuratorSession createSession(SessionConfig configuration) {
            assertNotNull(configuration.getMcpServers().get("wikipedia"));
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
        private final String response;
        private final String correctedResponse;
        private final Exception failure;
        private String prompt;
        private String lastPrompt;
        private long timeoutMillis;
        private boolean disconnected;
        private int callCount;

        private FakeSession(String response, Exception failure) {
            this(response, response, failure);
        }

        private FakeSession(
                String response, String correctedResponse, Exception failure) {
            this.response = response;
            this.correctedResponse = correctedResponse;
            this.failure = failure;
        }

        @Override
        public String sendAndWait(String prompt, long timeoutMillis) throws Exception {
            callCount++;
            if (callCount == 1) {
                this.prompt = prompt;
            }
            this.lastPrompt = prompt;
            this.timeoutMillis = timeoutMillis;
            if (failure != null) {
                throw failure;
            }
            return callCount == 1 ? response : correctedResponse;
        }

        @Override
        public void disconnect() {
            disconnected = true;
        }
    }
}
