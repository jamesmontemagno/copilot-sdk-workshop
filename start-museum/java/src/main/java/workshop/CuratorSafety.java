package workshop;

import com.github.copilot.rpc.McpStdioServerConfig;
import com.github.copilot.rpc.PermissionHandler;
import com.github.copilot.rpc.PermissionRequest;
import com.github.copilot.rpc.PermissionRequestResult;

import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.CompletableFuture;
import java.util.regex.Pattern;

public final class CuratorSafety {
    public static final List<String> WIKIPEDIA_TOOLS = List.of(
            "wikipedia-search",
            "wikipedia-readArticle");
    public static final String EXHIBIT_FILE_NAME = "exhibit.html";

    private static final Set<String> WIKIPEDIA_TOOL_NAMES = Set.of(
            "search",
            "readArticle",
            "wikipedia-search",
            "wikipedia-readArticle");
    private static final String WIKIPEDIA_REJECTION =
            "This session allows only the scoped Wikipedia search and article tools.";
    private static final String EXHIBIT_WRITE_REJECTION =
            "This session allows writing only exhibit.html in the application working directory.";
    private static final Pattern SOURCES_HEADING = Pattern.compile("(?im)^##\\s+Sources\\s*$");
    private static final Pattern SOURCE_LINE = Pattern.compile("^\\s*-\\s*(.+?):\\s*(https://\\S+)\\s*$");

    private CuratorSafety() {
    }

    public static McpStdioServerConfig wikipediaServer() {
        // SessionConfig should place this config in a map entry keyed "wikipedia".
        return new McpStdioServerConfig()
                .setCommand("npx")
                .setArgs(List.of("-y", "wikipedia-mcp@1.0.3"))
                .setWorkingDirectory(Path.of("").toAbsolutePath().normalize().toString())
                .setTools(List.of("search", "readArticle"));
    }

    public static PermissionHandler wikipediaPermissionHandler() {
        return (request, ignored) -> CompletableFuture.completedFuture(
                isAllowedWikipediaRequest(request)
                        ? PermissionRequestResult.approveOnce()
                        : PermissionRequestResult.reject(WIKIPEDIA_REJECTION));
    }

    public static SourceExtraction extractSources(String content) {
        if (content == null || content.isBlank()) {
            return new SourceExtraction("", List.of());
        }

        var matcher = SOURCES_HEADING.matcher(content);
        int headingStart = -1;
        int headingEnd = -1;
        while (matcher.find()) {
            headingStart = matcher.start();
            headingEnd = matcher.end();
        }
        if (headingStart < 0) {
            return new SourceExtraction(content.strip(), List.of());
        }

        String body = content.substring(0, headingStart).strip();
        String sourcesText = content.substring(headingEnd);
        List<Source> sources = new ArrayList<>();
        sourcesText.lines().forEach(line -> {
            var sourceMatcher = SOURCE_LINE.matcher(line);
            if (sourceMatcher.matches()) {
                String title = sourceMatcher.group(1).trim();
                String url = sourceMatcher.group(2).trim();
                if (!title.isEmpty() && !url.isEmpty()) {
                    sources.add(new Source(title, url));
                }
            }
        });
        return new SourceExtraction(body, sources);
    }

    public static PermissionHandler exhibitWritePermission(Path workingDirectory) {
        Path applicationDirectory = workingDirectory.toAbsolutePath().normalize();
        return (request, ignored) -> CompletableFuture.completedFuture(
                request != null
                        && "write".equals(request.getKind())
                        && isExhibitWrite(request.getExtensionData(), applicationDirectory)
                        ? PermissionRequestResult.approveOnce()
                        : PermissionRequestResult.reject(EXHIBIT_WRITE_REJECTION));
    }

    private static boolean isAllowedWikipediaRequest(PermissionRequest request) {
        if (request == null || !"mcp".equals(request.getKind()) || request.getExtensionData() == null) {
            return false;
        }
        Map<String, Object> details = request.getExtensionData();
        return "wikipedia".equals(details.get("serverName"))
                && details.get("toolName") instanceof String toolName
                && WIKIPEDIA_TOOL_NAMES.contains(toolName);
    }

    private static boolean isExhibitWrite(Map<String, Object> request, Path workingDirectory) {
        // Current Java SDK releases may not surface write-request fields; see
        // https://github.com/github/copilot-sdk/issues/2273. Missing fields stay denied.
        if (request == null || !(request.get("fileName") instanceof String fileName)) {
            return false;
        }
        Path candidate = Path.of(fileName);
        if (!candidate.isAbsolute()) {
            candidate = workingDirectory.resolve(candidate);
        }
        return candidate.normalize().equals(
                workingDirectory.resolve(EXHIBIT_FILE_NAME).normalize());
    }

    public record Source(String title, String url) {
    }

    public record SourceExtraction(String body, List<Source> sources) {
        public SourceExtraction {
            sources = List.copyOf(sources);
        }
    }
}
