using GitHub.Copilot;
using GitHub.Copilot.Rpc;

namespace MuseumExhibitStudio;

#pragma warning disable GHCP001 // Custom permission decisions are evaluation-only in SDK 1.0.11.

public static class WikipediaPermissionHandler
{
    private static readonly HashSet<string> AllowedTools =
    [
        "search",
        "readArticle"
    ];

    public static Func<PermissionRequest, PermissionInvocation, Task<PermissionDecision>> Create() =>
        (request, _) =>
        {
            var decision = request is PermissionRequestMcp { ServerName: "wikipedia" } wikipedia &&
                           IsAllowedTool(wikipedia)
                ? PermissionDecision.ApproveOnce()
                : PermissionDecision.Reject(
                    "Museum research permits only Wikipedia search and article retrieval.");

            return Task.FromResult(decision);
        };

    private static bool IsAllowedTool(PermissionRequestMcp request)
    {
        var toolName = request.ToolName.StartsWith(
            $"{request.ServerName}-",
            StringComparison.Ordinal)
            ? request.ToolName[(request.ServerName.Length + 1)..]
            : request.ToolName;
        return AllowedTools.Contains(toolName);
    }
}

#pragma warning restore GHCP001
