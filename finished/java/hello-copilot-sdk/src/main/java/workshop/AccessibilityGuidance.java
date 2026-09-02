package workshop;

import com.github.copilot.CopilotClient;
import com.github.copilot.generated.AssistantMessageDeltaEvent;
import com.github.copilot.generated.AssistantMessageEvent;
import com.github.copilot.rpc.MessageOptions;
import com.github.copilot.rpc.PermissionHandler;
import com.github.copilot.rpc.SessionConfig;
import com.github.copilot.rpc.ToolDefinition;
import com.github.copilot.tool.Param;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.util.List;
import java.util.concurrent.atomic.AtomicBoolean;

public final class AccessibilityGuidance {
    private AccessibilityGuidance() {
    }

    public static void main(String[] args) throws Exception {
        String question = readQuestion(args);
        if (question.isBlank()) {
            System.err.println("Enter an accessibility question to continue.");
            return;
        }

        var lookup = ToolDefinition.from(
                "accessibility_rule_lookup",
                "Looks up read-only WCAG guidance maintained by this application.",
                Param.of(String.class, "query", "The accessibility issue or WCAG criterion to look up."),
                AccessibilityGuidance::lookupRule).skipPermission(true);
        var config = new SessionConfig()
                .setStreaming(true)
                .setTools(List.of(lookup))
                .setAvailableTools(List.of("accessibility_rule_lookup"))
                .setOnPermissionRequest(PermissionHandler.APPROVE_ALL);

        try (var client = new CopilotClient()) {
            client.start().get();
            try (var session = client.createSession(config).get()) {
                var receivedDelta = new AtomicBoolean(false);
                try (var deltaSubscription = session.on(AssistantMessageDeltaEvent.class, event -> {
                    String delta = event.getData().deltaContent();
                    if (delta != null && !delta.isEmpty()) {
                        receivedDelta.set(true);
                        System.out.print(delta);
                    }
                }); var messageSubscription = session.on(AssistantMessageEvent.class, event -> {
                    String content = event.getData().content();
                    if (!receivedDelta.get() && content != null && !content.isEmpty()) {
                        System.out.print(content);
                    }
                })) {
                    System.out.println("\nCopilot:");
                    session.sendAndWait(new MessageOptions()
                            .setPrompt("Use accessibility_rule_lookup to answer this question: " + question))
                            .get();
                    System.out.println();
                }
            }
        }
    }

    private static String readQuestion(String[] args) throws Exception {
        String question = String.join(" ", args).trim();
        if (!question.isEmpty()) {
            return question;
        }

        System.out.print("Accessibility question: ");
        String answer = new BufferedReader(new InputStreamReader(System.in)).readLine();
        return answer == null ? "" : answer.trim();
    }

    private static String lookupRule(String query) {
        String normalized = query.toLowerCase(java.util.Locale.ROOT);
        if (normalized.contains("4.1.2") || normalized.contains("accessible name")) {
            return """
                    {"criterion":"4.1.2","title":"Name, Role, Value","recommendation":"Associate each input with a visible label."}""";
        }
        return """
                {"criterion":"No exact match","recommendation":"Verify the evidence and consult the WCAG reference."}""";
    }
}
