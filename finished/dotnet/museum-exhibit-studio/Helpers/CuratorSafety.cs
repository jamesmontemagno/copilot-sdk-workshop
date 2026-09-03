using GitHub.Copilot;
using GitHub.Copilot.Rpc;

namespace MuseumExhibitStudio.Helpers;

#pragma warning disable GHCP001 // Custom permission decisions are evaluation-only in SDK 1.0.11.

public sealed record ResearchSource(string Title, string Url);

public sealed record ExtractedSources(string Body, IReadOnlyList<ResearchSource> Sources);

public static class CuratorSafety
{
    public const string ExhibitFileName = "exhibit.html";

    public static IReadOnlyList<string> WikipediaTools { get; } =
    [
        "wikipedia-search",
        "wikipedia-readArticle"
    ];

    private static readonly HashSet<string> AllowedWikipediaToolNames =
    [
        "search",
        "readArticle",
        "wikipedia-search",
        "wikipedia-readArticle"
    ];

    // Return this config as the "wikipedia" value in SessionConfig.McpServers.
    public static McpStdioServerConfig WikipediaServer() => new()
    {
        Command = "npx",
        Args = ["-y", "wikipedia-mcp@1.0.3"],
        WorkingDirectory = Directory.GetCurrentDirectory(),
        Tools = ["search", "readArticle"]
    };

    public static Func<PermissionRequest, PermissionInvocation, Task<PermissionDecision>> WikipediaPermissionHandler() =>
        (request, _) =>
        {
            var decision = request is PermissionRequestMcp { ServerName: "wikipedia" } wikipedia &&
                           AllowedWikipediaToolNames.Contains(wikipedia.ToolName)
                ? PermissionDecision.ApproveOnce()
                : PermissionDecision.Reject(
                    "This session allows only the scoped Wikipedia search and article tools.");

            return Task.FromResult(decision);
        };

    public static ExtractedSources ExtractSources(string content)
    {
        if (string.IsNullOrEmpty(content))
        {
            return new ExtractedSources(string.Empty, []);
        }

        var lines = content.ReplaceLineEndings("\n").Split('\n');
        var sourcesIndex = Array.FindLastIndex(
            lines,
            line => line.Trim().Equals("## Sources", StringComparison.OrdinalIgnoreCase));

        if (sourcesIndex < 0)
        {
            return new ExtractedSources(content.Trim(), []);
        }

        var body = string.Join('\n', lines[..sourcesIndex]).Trim();
        var sources = new List<ResearchSource>();

        foreach (var line in lines[(sourcesIndex + 1)..])
        {
            var trimmed = line.Trim();
            if (!trimmed.StartsWith("- ", StringComparison.Ordinal))
            {
                continue;
            }

            var item = trimmed[2..].Trim();
            var separatorIndex = item.IndexOf(": https://", StringComparison.OrdinalIgnoreCase);
            if (separatorIndex <= 0)
            {
                continue;
            }

            var title = item[..separatorIndex].Trim();
            var url = item[(separatorIndex + 2)..].Trim();
            if (title.Length == 0 || !url.StartsWith("https://", StringComparison.OrdinalIgnoreCase))
            {
                continue;
            }

            sources.Add(new ResearchSource(title, url));
        }

        return new ExtractedSources(body, sources.AsReadOnly());
    }

    public static Func<PermissionRequest, PermissionInvocation, Task<PermissionDecision>> ExhibitWritePermission(
        string workingDirectory)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(workingDirectory);

        var normalizedWorkingDirectory = Path.GetFullPath(workingDirectory);
        var allowedPath = Path.GetFullPath(Path.Combine(normalizedWorkingDirectory, ExhibitFileName));

        return (request, _) =>
        {
            var decision = request is PermissionRequestWrite write &&
                           IsAllowedExhibitPath(write.FileName, normalizedWorkingDirectory, allowedPath)
                ? PermissionDecision.ApproveOnce()
                : PermissionDecision.Reject(
                    "This session allows writing only exhibit.html in the application working directory.");

            return Task.FromResult(decision);
        };
    }

    private static bool IsAllowedExhibitPath(
        string fileName,
        string workingDirectory,
        string allowedPath)
    {
        if (string.IsNullOrWhiteSpace(fileName))
        {
            return false;
        }

        var requestedPath = Path.IsPathRooted(fileName)
            ? Path.GetFullPath(fileName)
            : Path.GetFullPath(Path.Combine(workingDirectory, fileName));

        return requestedPath.Equals(allowedPath, StringComparison.OrdinalIgnoreCase);
    }
}

#pragma warning restore GHCP001
