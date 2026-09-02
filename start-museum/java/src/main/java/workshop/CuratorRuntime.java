package workshop;

import com.github.copilot.CopilotClient;
import com.github.copilot.CopilotSession;
import com.github.copilot.rpc.MessageOptions;
import com.github.copilot.rpc.SessionConfig;

interface CuratorSession {
    String sendAndWait(String prompt, long timeoutMillis) throws Exception;

    void disconnect();
}

interface CuratorClient extends AutoCloseable {
    void start() throws Exception;

    CuratorSession createSession(SessionConfig configuration) throws Exception;

    void stop() throws Exception;

    @Override
    void close();
}

final class CopilotCuratorClient implements CuratorClient {
    private final CopilotClient client = new CopilotClient();

    @Override
    public void start() throws Exception {
        client.start().get();
    }

    @Override
    public CuratorSession createSession(SessionConfig configuration) throws Exception {
        return new CopilotCuratorSession(client.createSession(configuration).get());
    }

    @Override
    public void stop() throws Exception {
        client.stop().get();
    }

    @Override
    public void close() {
        client.close();
    }

    private record CopilotCuratorSession(CopilotSession session) implements CuratorSession {
        @Override
        public String sendAndWait(String prompt, long timeoutMillis) throws Exception {
            var response = session.sendAndWait(
                    new MessageOptions().setPrompt(prompt), timeoutMillis).get();
            return response == null || response.getData() == null
                    ? null
                    : response.getData().content();
        }

        @Override
        public void disconnect() {
            session.close();
        }
    }
}
