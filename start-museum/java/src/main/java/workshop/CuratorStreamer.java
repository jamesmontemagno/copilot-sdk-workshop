package workshop;

import com.github.copilot.CopilotSession;
import com.github.copilot.generated.AssistantMessageDeltaEvent;
import com.github.copilot.generated.AssistantMessageEvent;
import com.github.copilot.generated.SessionErrorEvent;
import com.github.copilot.generated.SessionIdleEvent;
import com.github.copilot.generated.ToolExecutionCompleteEvent;
import com.github.copilot.generated.ToolExecutionStartEvent;
import com.github.copilot.rpc.MessageOptions;

import java.io.Closeable;
import java.io.IOException;
import java.time.Duration;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.TimeoutException;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicReference;

public final class CuratorStreamer {
    public static final Duration GENERATION_TIMEOUT = Duration.ofSeconds(120);
    public static final Duration RESEARCH_TIMEOUT = Duration.ofSeconds(90);

    private CuratorStreamer() {
    }

    public static String streamExhibit(CopilotSession session, String prompt) throws Exception {
        return streamExhibit(session, prompt, GENERATION_TIMEOUT);
    }

    public static String streamExhibit(CopilotSession session, String prompt, Duration timeout) throws Exception {
        StringBuilder assistantText = new StringBuilder();
        AtomicBoolean receivedDelta = new AtomicBoolean(false);
        AtomicReference<String> sessionError = new AtomicReference<>();
        List<Closeable> subscriptions = new ArrayList<>();

        try {
            subscriptions.add(session.on(AssistantMessageDeltaEvent.class, event -> {
                String delta = event.getData() == null ? null : event.getData().deltaContent();
                if (delta != null && !delta.isEmpty()) {
                    receivedDelta.set(true);
                    synchronized (assistantText) {
                        assistantText.append(delta);
                    }
                    System.out.print(delta);
                }
            }));
            subscriptions.add(session.on(AssistantMessageEvent.class, event -> {
                String content = event.getData() == null ? null : event.getData().content();
                if (!receivedDelta.get() && content != null && !content.isEmpty()) {
                    synchronized (assistantText) {
                        if (assistantText.length() == 0) {
                            assistantText.append(content);
                            System.out.print(content);
                        }
                    }
                }
            }));
            subscriptions.add(session.on(ToolExecutionStartEvent.class, event -> {
                String toolName = event.getData() == null ? "unknown" : event.getData().toolName();
                System.out.println("\n[tool:start] " + (toolName == null ? "unknown" : toolName));
            }));
            subscriptions.add(session.on(ToolExecutionCompleteEvent.class, event -> {
                boolean success = event.getData() != null && Boolean.TRUE.equals(event.getData().success());
                System.out.println("[tool:done] success=" + success);
            }));
            subscriptions.add(session.on(SessionErrorEvent.class, event -> {
                String message = event.getData() == null ? "session error" : event.getData().message();
                sessionError.set(message == null || message.isBlank() ? "session error" : message);
            }));
            subscriptions.add(session.on(SessionIdleEvent.class, ignored -> System.out.println()));

            AssistantMessageEvent response = session.sendAndWait(
                    new MessageOptions().setPrompt(prompt),
                    timeout.toMillis()).get();
            if (sessionError.get() != null) {
                throw new IllegalStateException(sessionError.get());
            }
            if (response != null && response.getData() != null) {
                String content = response.getData().content();
                synchronized (assistantText) {
                    if (assistantText.length() == 0 && content != null && !content.isEmpty()) {
                        assistantText.append(content);
                        System.out.print(content);
                    }
                    return assistantText.toString();
                }
            }
            synchronized (assistantText) {
                return assistantText.toString();
            }
        } catch (ExecutionException exception) {
            Throwable root = rootCause(exception);
            if (root instanceof TimeoutException) {
                throw new TimeoutException("timeout after " + timeout.toMillis() + "ms");
            }
            if (sessionError.get() != null) {
                throw new IllegalStateException(sessionError.get(), root);
            }
            if (root instanceof Exception checked) {
                throw checked;
            }
            throw new IllegalStateException(root);
        } finally {
            closeAll(subscriptions);
        }
    }

    private static void closeAll(List<Closeable> subscriptions) throws IOException {
        IOException failure = null;
        for (int index = subscriptions.size() - 1; index >= 0; index--) {
            try {
                subscriptions.get(index).close();
            } catch (IOException exception) {
                if (failure == null) {
                    failure = exception;
                } else {
                    failure.addSuppressed(exception);
                }
            }
        }
        if (failure != null) {
            throw failure;
        }
    }

    private static Throwable rootCause(Throwable error) {
        Throwable current = error;
        while (current.getCause() != null) {
            current = current.getCause();
        }
        return current;
    }
}
