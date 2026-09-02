using System.Text.Json;
using GitHub.Copilot;
using GitHub.Copilot.Rpc;

namespace HelloCopilotSDK.Helpers;

#pragma warning disable GHCP001 // Custom permission decisions are evaluation-only in SDK 1.0.7.

public static class WorkshopPermissionHandler
{
    public static Func<PermissionRequest, PermissionInvocation, Task<PermissionDecision>> CreateForTarget(
        Uri allowedTarget)
    {
        ArgumentNullException.ThrowIfNull(allowedTarget);

        return (request, _) =>
        {
            var decision = request switch
            {
                PermissionRequestMcp { ServerName: "playwright" } navigation
                    when IsPlaywrightTool(navigation, "browser_navigate") &&
                         IsNavigationToTarget(navigation.Args, allowedTarget) =>
                    PermissionDecision.ApproveOnce(),
                _ => PermissionDecision.Reject(
                    "This workshop allows Playwright to navigate only to the exact requested target.")
            };

            return Task.FromResult(decision);
        };
    }

    private static bool IsPlaywrightTool(PermissionRequestMcp request, string toolName) =>
        request.ToolName.Equals(toolName, StringComparison.Ordinal) ||
        request.ToolName.Equals($"{request.ServerName}-{toolName}", StringComparison.Ordinal);

    private static bool IsNavigationToTarget(JsonElement? arguments, Uri allowedTarget)
    {
        if (arguments is not { ValueKind: JsonValueKind.Object } value ||
            !value.TryGetProperty("url", out var urlValue) ||
            urlValue.ValueKind is not JsonValueKind.String ||
            !Uri.TryCreate(urlValue.GetString(), UriKind.Absolute, out var requestedTarget))
        {
            return false;
        }

        return requestedTarget.Scheme.Equals(allowedTarget.Scheme, StringComparison.OrdinalIgnoreCase) &&
               requestedTarget.IdnHost.Equals(allowedTarget.IdnHost, StringComparison.OrdinalIgnoreCase) &&
               requestedTarget.Port == allowedTarget.Port &&
               requestedTarget.UserInfo.Equals(allowedTarget.UserInfo, StringComparison.Ordinal) &&
               requestedTarget.GetComponents(
                   UriComponents.PathAndQuery | UriComponents.Fragment,
                   UriFormat.UriEscaped).Equals(
                       allowedTarget.GetComponents(
                           UriComponents.PathAndQuery | UriComponents.Fragment,
                           UriFormat.UriEscaped),
                       StringComparison.Ordinal);
    }
}

#pragma warning restore GHCP001
