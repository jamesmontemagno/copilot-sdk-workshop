# Step 4: Connect an external tool safely

> **Time:** 20 minutes

## What you'll connect

You'll start Playwright through MCP, limit navigation to the workshop target you provide, inspect
its accessibility tree, and report the page title.

## Meet MCP and its trust boundary

The [**Model Context Protocol (MCP)**](https://github.com/github/copilot-sdk/blob/main/docs/features/mcp.md)
is a standard way to connect an agent to reusable capabilities implemented outside your
application. In this workshop, the SDK starts the Playwright MCP server as a separate `npx`
process. Playwright handles browser automation, while your application configures the connection.

The process boundary is also a **trust boundary**. A
[permission handler](https://github.com/github/copilot-sdk/blob/main/docs/hooks/pre-tool-use.md) is
a callback the runtime invokes before a requested action runs, and it decides whether each external
action may proceed.

| Question | Local WCAG tool | Playwright MCP |
|---|---|---|
| Who implements it? | This application | External Playwright package |
| Where does it run? | Same application process | Separate Node.js process |
| What is it best for? | App-owned data and deterministic logic | Reusable browser capability |
| How is trust handled here? | Read-only tool skips permission | Tool list and custom handler restrict access |

The WCAG lookup and narrow snapshot reader stay in process.
`CopilotSession -> Playwright MCP -> browser` crosses a process boundary.

## Put Playwright behind guardrails

The browser argument uses Microsoft Edge, the workshop default. If you prepared Google Chrome
instead, use `--browser=chrome`.

The session tool allowlist keeps unrelated runtime tools out. The MCP server's tool list exposes
only navigation. In Playwright MCP 0.0.78, navigation writes its automatic accessibility tree to
`.playwright-mcp/`. The application snapshot reader accepts no arguments and reads only the newest
Playwright snapshot created after the session started.

`browser_snapshot` stays off both allowlists because its optional `filename` argument can write a
file. The runtime can automatically allow MCP tools annotated as read-only without calling your
permission delegate, so a handler cannot reliably sanitize that argument. Removing the tool closes
the capability instead of relying on a prompt.

The reader accepts no path. It ignores pre-existing files, nested files, symbolic links, empty
files, and snapshots larger than 1 MB. Navigation is approved only when the complete canonical URL
matches the target supplied at startup. Scheme and host use URL-standard case-insensitive
comparison. Path, query, and fragment must match case-sensitively.

The handler returns exactly one decision per request, and this one needs two of the available
kinds. `approve-once` allows this single request. `reject` denies it and can forward a feedback
message to the model, so a refused call comes back with a reason instead of as a silent failure.
Two more kinds exist for situations this workshop does not reach: `user-not-available` denies
because no user is present to confirm, and `no-result` declines to respond at all so another
connected client can answer the request instead. Wider approval scopes — `approve-for-session`,
`approve-for-location`, and `approve-permanently` — remember a decision beyond this one call. Each
SDK spells all of these with its own naming convention.

:::language dotnet
## Wire up scoped Playwright access in C#

### 1. Accept one controlled target

At the top of `Program.cs`, after the `using` statements and before the banner, insert:

```csharp
if (args.Length is not 1 ||
    !Uri.TryCreate(args[0], UriKind.Absolute, out var targetUri) ||
    targetUri.Scheme is not ("http" or "https"))
{
    Console.Error.WriteLine("Usage: dotnet run -- <http-or-https-url>");
    return;
}
```

### 2. Inspect the prebuilt permission handler

Open `Helpers/WorkshopPermissionHandler.cs`. The prebuilt handler returns a one-time
approval only for exact-target navigation. Every other external request is rejected.

```csharp
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
```

The .NET SDK currently prefixes MCP permission tool names with the server name (for example,
`playwright-browser_navigate`), while MCP configuration uses `browser_navigate`.
`IsPlaywrightTool` accepts those two exact forms rather than using a broad wildcard.

> **SDK note:** version 1.0.7 ships `PermissionHandler.ApproveAll`, but no built-in scoped handler.
> The starter therefore includes a hand-written delegate. `PermissionDecision` is currently marked
> evaluation-only, so that one helper contains a localized `GHCP001` suppression.

### 3. Inspect the prebuilt snapshot-reader boundary

Open `Helpers/PlaywrightSnapshotReader.cs`. The reader captures existing snapshots when
the tool is created, accepts no model-supplied arguments, selects only a new direct child named
`page-*.yml`, rejects symbolic links and oversized files, then returns the text.

```csharp
public static AIFunction CreateTool(string workingDirectory)
{
    ArgumentException.ThrowIfNullOrWhiteSpace(workingDirectory);

    var outputDirectory = Path.GetFullPath(Path.Combine(workingDirectory, ".playwright-mcp"));
    var existingSnapshots = Directory.Exists(outputDirectory)
        ? Directory.EnumerateFiles(outputDirectory, "page-*.yml", SearchOption.TopDirectoryOnly)
            .Select(Path.GetFullPath)
            .ToHashSet(PathComparer)
        : new HashSet<string>(PathComparer);

    return CopilotTool.DefineTool(
        () => Task.FromResult(ReadLatestSnapshot(outputDirectory, existingSnapshots)),
        toolOptions: new CopilotToolOptions { SkipPermission = true },
        factoryOptions: new AIFunctionFactoryOptions
        {
            Name = "read_latest_accessibility_snapshot",
            Description = "Reads the newest Playwright accessibility snapshot created during this run."
        });
}
```

The adapter skips permission because it is read-only, uses application-selected storage, and is
implemented by the application. That is a narrower capability than a general file reader.

### 4. Add Playwright MCP and scoped permissions

Replace the session configuration with:

```csharp
var workingDirectory = Directory.GetCurrentDirectory();

await using var session = await client.CreateSessionAsync(new SessionConfig
{
    Streaming = true,
    OnPermissionRequest = WorkshopPermissionHandler.CreateForTarget(targetUri),
    Tools =
    [
        AccessibilityRuleCatalog.CreateLookupTool(),
        PlaywrightSnapshotReader.CreateTool(workingDirectory)
    ],
    AvailableTools =
    [
        "accessibility_rule_lookup",
        "read_latest_accessibility_snapshot",
        "playwright-browser_navigate"
    ],
    McpServers = new Dictionary<string, McpServerConfig>
    {
        ["playwright"] = new McpStdioServerConfig
        {
            Command = "npx",
            Args = ["-y", "@playwright/mcp@0.0.78", "--browser=msedge", "--output-dir", ".playwright-mcp", "--output-mode", "file"],
            WorkingDirectory = workingDirectory,
            Tools = ["browser_navigate"]
        }
    }
});
```

### 5. Request browser evidence

Replace the final send call:

```csharp
Console.WriteLine($"\nInspecting: {targetUri.AbsoluteUri}\n");
await ResponseStreamer.SendAndPrintAsync(
    session,
    $"""
    Use browser_navigate to open {targetUri.AbsoluteUri}.
    Then use read_latest_accessibility_snapshot and report the page title
    plus one sentence describing its main content.
    """);
```

## Run it

```bash
dotnet run -- "{{TARGET_APP_URL}}"
```

The first run may take longer while `npx` starts Playwright.

Look for:

```text
[tool:start] playwright-browser_navigate
[tool:done] success=...
[tool:start] read_latest_accessibility_snapshot
[tool:done] success=True

Page title: Blazor Accessibility Target
```

<details>
<summary>Troubleshooting this run</summary>

| Symptom | Fix |
|---|---|
| `npx` cannot be started | Rerun the preflight MCP command and verify Node.js is on `PATH`. |
| Playwright cannot find a browser | Install Edge or Chrome, or configure an installed browser as described by Playwright MCP. |
| A permission is rejected | Use the exact target URL above. The handler intentionally denies other URLs and tools. |
| No current-run snapshot is available | Keep the prompt order: call `browser_navigate` before `read_latest_accessibility_snapshot`. |
| The compiler cannot find the permission helper | Confirm `using HelloCopilotSDK.Helpers;` is present and the helper file is in the project. |

</details>

<details>
<summary>Complete Step 4 implementation</summary>

Compare your work with this complete Step 4 implementation.

```csharp
using GitHub.Copilot;
using HelloCopilotSDK.Helpers;

if (args.Length is not 1 ||
    !Uri.TryCreate(args[0], UriKind.Absolute, out var targetUri) ||
    targetUri.Scheme is not ("http" or "https"))
{
    Console.Error.WriteLine("Usage: dotnet run -- <http-or-https-url>");
    return;
}

Console.WriteLine("=== Scoped Playwright MCP access ===\n");

await using var client = new CopilotClient();
await client.StartAsync();

var ping = await client.PingAsync("workshop");
Console.WriteLine($"Connected to the Copilot runtime: {ping.Message}\n");

var workingDirectory = Directory.GetCurrentDirectory();

await using var session = await client.CreateSessionAsync(new SessionConfig
{
    Streaming = true,
    OnPermissionRequest = WorkshopPermissionHandler.CreateForTarget(targetUri),
    Tools =
    [
        AccessibilityRuleCatalog.CreateLookupTool(),
        PlaywrightSnapshotReader.CreateTool(workingDirectory)
    ],
    AvailableTools =
    [
        "accessibility_rule_lookup",
        "read_latest_accessibility_snapshot",
        "playwright-browser_navigate"
    ],
    McpServers = new Dictionary<string, McpServerConfig>
    {
        ["playwright"] = new McpStdioServerConfig
        {
            Command = "npx",
            Args = ["-y", "@playwright/mcp@0.0.78", "--browser=msedge", "--output-dir", ".playwright-mcp", "--output-mode", "file"],
            WorkingDirectory = workingDirectory,
            Tools = ["browser_navigate"]
        }
    }
});

Console.WriteLine($"Inspecting: {targetUri.AbsoluteUri}\n");
await ResponseStreamer.SendAndPrintAsync(
    session,
    $"""
    Use browser_navigate to open {targetUri.AbsoluteUri}.
    Then use read_latest_accessibility_snapshot and return the page title
    plus one sentence describing its main content.
    """);
```

</details>
:::

:::language nodejs
## Wire up scoped Playwright access in TypeScript

### 1. Accept one controlled target

At the top of `src/index.ts`, replace the entrypoint setup with:

```typescript
import { CopilotClient } from "@github/copilot-sdk";
import {
  accessibilityRuleLookup,
  createSnapshotReader,
  permissionForTarget,
  streamResponse,
} from "./workshop.js";

const input = process.argv[2];
if (!input) throw new Error("Usage: npm start -- <http-or-https-url>");
const target = new URL(input.includes("://") ? input : `https://${input}`);
if (!["http:", "https:"].includes(target.protocol)) {
  throw new Error("Enter an absolute HTTP or HTTPS URL.");
}
```

### 2. Inspect the prebuilt permission handler

Open `src/workshop.ts`. The prebuilt handler approves only exact-target Playwright navigation:

```typescript
export function permissionForTarget(target: URL): PermissionHandler {
  return (request) => {
    if (
      request.kind === "mcp" &&
      request.serverName === "playwright" &&
      (request.toolName === "browser_navigate" ||
        request.toolName === "playwright-browser_navigate") &&
      typeof request.args?.url === "string" &&
      sameUrl(new URL(request.args.url), target)
    ) {
      return { kind: "approve-once" };
    }
    return {
      kind: "reject",
      feedback:
        "This workshop allows Playwright to navigate only to the exact requested target.",
    };
  };
}

function sameUrl(requested: URL, allowed: URL): boolean {
  return (
    requested.protocol.toLowerCase() === allowed.protocol.toLowerCase() &&
    requested.hostname.toLowerCase() === allowed.hostname.toLowerCase() &&
    requested.port === allowed.port &&
    requested.username === allowed.username &&
    requested.password === allowed.password &&
    requested.pathname === allowed.pathname &&
    requested.search === allowed.search &&
    requested.hash === allowed.hash
  );
}
```

Accept both `browser_navigate` and `playwright-browser_navigate` because the runtime may prefix the
server name on permission requests.

### 3. Inspect the prebuilt snapshot-reader boundary

Still in `src/workshop.ts`, the snapshot reader captures existing files at creation
time and accepts no model-supplied path:

```typescript
export function createSnapshotReader(workingDirectory: string) {
  const outputDirectory = resolve(workingDirectory, ".playwright-mcp");
  const existingSnapshots = safeSnapshotNames(outputDirectory).then(
    (names) => new Set(names.map((name) => resolve(outputDirectory, name))),
  );
  return defineTool("read_latest_accessibility_snapshot", {
    description:
      "Reads the newest Playwright accessibility snapshot created during this run.",
    parameters: z.object({}),
    skipPermission: true,
    handler: async () => {
      const baseline = await existingSnapshots;
      const candidates = await Promise.all(
        (await safeSnapshotNames(outputDirectory)).map(async (name) => {
          const path = resolve(outputDirectory, name);
          const details = await lstat(path);
          return { path, details };
        }),
      );
      const snapshot = candidates
        .filter(
          ({ path, details }) =>
            !baseline.has(path) &&
            !details.isSymbolicLink() &&
            details.isFile() &&
            details.size > 0 &&
            details.size <= maxSnapshotBytes,
        )
        .sort((left, right) => right.details.mtimeMs - left.details.mtimeMs)[0];
      if (!snapshot) {
        throw new Error(
          "No current-run Playwright snapshot is available. Call browser_navigate first.",
        );
      }
      return readFile(snapshot.path, "utf8");
    },
  });
}
```

### 4. Add Playwright MCP and scoped permissions

In `src/index.ts`, create the session with the three-tool allowlist and Playwright MCP:

```typescript
const client = new CopilotClient();
await client.start();
try {
  const session = await client.createSession({
    streaming: true,
    onPermissionRequest: permissionForTarget(target),
    tools: [accessibilityRuleLookup, createSnapshotReader(process.cwd())],
    availableTools: [
      "accessibility_rule_lookup",
      "read_latest_accessibility_snapshot",
      "playwright-browser_navigate",
    ],
    mcpServers: {
      playwright: {
        command: "npx",
        args: ["-y", "@playwright/mcp@0.0.78", "--browser=msedge", "--output-dir", ".playwright-mcp", "--output-mode", "file"],
        workingDirectory: process.cwd(),
        tools: ["browser_navigate"],
      },
    },
  });
  try {
    await streamResponse(
      session,
      `Use browser_navigate to open ${target.href}, then read_latest_accessibility_snapshot and report the page title.`,
    );
  } finally {
    await session.disconnect();
  }
} finally {
  await client.stop();
}
```

`availableTools` uses the runtime-prefixed MCP name `playwright-browser_navigate`, while the MCP
server config still lists bare `browser_navigate`.

## Run it

```bash
npm start -- "{{TARGET_APP_URL}}"
```

The first run may take longer while `npx` starts Playwright.

Look for:

```text
[tool:start] playwright-browser_navigate
[tool:done] success=...
[tool:start] read_latest_accessibility_snapshot
[tool:done] success=true

Page title: Blazor Accessibility Target
```

<details>
<summary>Troubleshooting this run</summary>

| Symptom | Fix |
|---|---|
| `npx` cannot be started | Rerun the preflight MCP command and verify Node.js is on `PATH`. |
| Playwright cannot find a browser | Install Edge or Chrome, or configure an installed browser as described by Playwright MCP. |
| A permission is rejected | Use the exact target URL above. The handler intentionally denies other URLs and tools. |
| No current-run snapshot is available | Keep the prompt order: call `browser_navigate` before `read_latest_accessibility_snapshot`. |
| TypeScript cannot resolve helpers | Confirm the import path ends with `.js` and run `npm install` in the starter directory. |

</details>

<details>
<summary>Complete Step 4 implementation</summary>

Compare your work with this complete Step 4 implementation.

`src/index.ts`:

```typescript
import { CopilotClient } from "@github/copilot-sdk";
import { accessibilityRuleLookup, createSnapshotReader, permissionForTarget, streamResponse } from "./workshop.js";

const input = process.argv[2];
if (!input) throw new Error("Usage: npm start -- <http-or-https-url>");
const target = new URL(input.includes("://") ? input : `https://${input}`);
if (!["http:", "https:"].includes(target.protocol)) throw new Error("Enter an absolute HTTP or HTTPS URL.");
const client = new CopilotClient();
await client.start();
try {
  const session = await client.createSession({
    streaming: true,
    onPermissionRequest: permissionForTarget(target),
    tools: [accessibilityRuleLookup, createSnapshotReader(process.cwd())],
    availableTools: ["accessibility_rule_lookup", "read_latest_accessibility_snapshot", "playwright-browser_navigate"],
    mcpServers: { playwright: { command: "npx", args: ["-y", "@playwright/mcp@0.0.78", "--browser=msedge", "--output-dir", ".playwright-mcp", "--output-mode", "file"], workingDirectory: process.cwd(), tools: ["browser_navigate"] } },
  });
  try {
    await streamResponse(session, `Use browser_navigate to open ${target.href}, then read_latest_accessibility_snapshot and report the page title.`);
  } finally {
    await session.disconnect();
  }
} finally {
  await client.stop();
}
```

</details>
:::

:::language python
## Wire up scoped Playwright access in Python

### 1. Accept one controlled target

At the top of `main.py`, validate the startup URL:

```python
import asyncio
import sys
from urllib.parse import urlsplit

from copilot import CopilotClient
from copilot.session_events import (
    AssistantMessageData,
    AssistantMessageDeltaData,
    SessionErrorData,
    SessionIdleData,
)

from workshop import (
    accessibility_rule_lookup,
    create_snapshot_reader,
    permission_for_target,
)


async def main() -> None:
    if len(sys.argv) != 2:
        raise ValueError("Usage: python main.py <http-or-https-url>")
    target = sys.argv[1]
    if urlsplit(target).scheme not in {"http", "https"}:
        raise ValueError("Enter an absolute HTTP or HTTPS URL.")
```

### 2. Inspect the prebuilt permission handler

Open `workshop.py`. The prebuilt handler approves only exact-target Playwright navigation:

```python
def permission_for_target(target: str):
    def handler(request, _invocation):
        if (
            getattr(request, "kind", None) == "mcp"
            and request.server_name == "playwright"
            and request.tool_name
            in {"browser_navigate", "playwright-browser_navigate"}
            and isinstance(request.args, dict)
            and isinstance(request.args.get("url"), str)
            and _same_url(request.args["url"], target)
        ):
            return PermissionDecisionApproveOnce()
        return PermissionDecisionReject(
            feedback=(
                "This workshop allows Playwright to navigate only to the exact requested target."
            )
        )

    return handler


def _same_url(requested: str, allowed: str) -> bool:
    left, right = urlsplit(requested), urlsplit(allowed)
    return (
        left.scheme.lower(),
        left.hostname.lower() if left.hostname else "",
        left.port,
        left.username,
        left.password,
        left.path,
        left.query,
        left.fragment,
    ) == (
        right.scheme.lower(),
        right.hostname.lower() if right.hostname else "",
        right.port,
        right.username,
        right.password,
        right.path,
        right.query,
        right.fragment,
    )
```

### 3. Inspect the prebuilt snapshot-reader boundary

Still in `workshop.py`, the snapshot reader captures existing files at creation time
and accepts no model-supplied path:

```python
def create_snapshot_reader(working_directory: str):
    output_directory = Path(working_directory, ".playwright-mcp").resolve()
    existing = (
        {path.resolve() for path in output_directory.glob("page-*.yml")}
        if output_directory.is_dir()
        else set()
    )

    @define_tool(
        name="read_latest_accessibility_snapshot",
        description=(
            "Reads the newest Playwright accessibility snapshot created during this run."
        ),
        skip_permission=True,
    )
    def read_latest_accessibility_snapshot() -> str:
        candidates = [
            path
            for path in output_directory.glob("page-*.yml")
            if path.resolve() not in existing
            and not path.is_symlink()
            and path.is_file()
            and 0 < path.stat().st_size <= MAX_SNAPSHOT_BYTES
        ]
        if not candidates:
            raise FileNotFoundError(
                "No current-run Playwright snapshot is available. Call browser_navigate first."
            )
        return max(candidates, key=lambda path: path.stat().st_mtime).read_text(
            encoding="utf-8"
        )

    return read_latest_accessibility_snapshot
```

### 4. Add Playwright MCP and scoped permissions

Replace the session creation block in `main.py`:

```python
    async with CopilotClient() as client:
        async with await client.create_session(
            streaming=True,
            on_permission_request=permission_for_target(target),
            tools=[accessibility_rule_lookup, create_snapshot_reader(".")],
            available_tools=[
                "accessibility_rule_lookup",
                "read_latest_accessibility_snapshot",
                "playwright-browser_navigate",
            ],
            mcp_servers={
                "playwright": {
                    "command": "npx",
                    "args": ["-y", "@playwright/mcp@0.0.78", "--browser=msedge", "--output-dir", ".playwright-mcp", "--output-mode", "file"],
                    "working_directory": ".",
                    "tools": ["browser_navigate"],
                }
            },
        ) as session:
            done = asyncio.Event()
            error: RuntimeError | None = None
            received_delta = False

            def on_event(event) -> None:
                nonlocal error, received_delta
                match event.data:
                    case AssistantMessageDeltaData(delta_content=delta) if delta:
                        received_delta = True
                        print(delta, end="", flush=True)
                    case AssistantMessageData(content=content) if content and not received_delta:
                        print(content)
                    case SessionErrorData(message=message):
                        error = RuntimeError(message)
                        done.set()
                    case SessionIdleData():
                        done.set()

            session.on(on_event)
            await session.send(
                f"Use browser_navigate to open {target}, then "
                "read_latest_accessibility_snapshot and report the page title."
            )
            await done.wait()
            if error is not None:
                raise error
```

`available_tools` uses the runtime-prefixed MCP name `playwright-browser_navigate`, while the MCP
server config still lists bare `browser_navigate`.

## Run it

```bash
python main.py "{{TARGET_APP_URL}}"
```

The first run may take longer while `npx` starts Playwright.

Look for navigation and snapshot activity, then a page title such as:

```text
Page title: Blazor Accessibility Target
```

<details>
<summary>Troubleshooting this run</summary>

| Symptom | Fix |
|---|---|
| `npx` cannot be started | Rerun the preflight MCP command and verify Node.js is on `PATH`. |
| Playwright cannot find a browser | Install Edge or Chrome, or configure an installed browser as described by Playwright MCP. |
| A permission is rejected | Use the exact target URL above. The handler intentionally denies other URLs and tools. |
| No current-run snapshot is available | Keep the prompt order: call `browser_navigate` before `read_latest_accessibility_snapshot`. |
| Import errors for workshop helpers | Activate the preflight virtual environment and confirm `workshop.py` is beside `main.py`. |

</details>

<details>
<summary>Complete Step 4 implementation</summary>

Compare your work with this complete Step 4 implementation.

`main.py`:

```python
import asyncio
import sys
from urllib.parse import urlsplit

from copilot import CopilotClient
from copilot.session_events import AssistantMessageData, AssistantMessageDeltaData, SessionErrorData, SessionIdleData

from workshop import accessibility_rule_lookup, create_snapshot_reader, permission_for_target


async def main() -> None:
    if len(sys.argv) != 2:
        raise ValueError("Usage: python main.py <http-or-https-url>")
    target = sys.argv[1]
    if urlsplit(target).scheme not in {"http", "https"}:
        raise ValueError("Enter an absolute HTTP or HTTPS URL.")
    async with CopilotClient() as client:
        async with await client.create_session(
            streaming=True,
            on_permission_request=permission_for_target(target),
            tools=[accessibility_rule_lookup, create_snapshot_reader(".")],
            available_tools=["accessibility_rule_lookup", "read_latest_accessibility_snapshot", "playwright-browser_navigate"],
            mcp_servers={"playwright": {"command": "npx", "args": ["-y", "@playwright/mcp@0.0.78", "--browser=msedge", "--output-dir", ".playwright-mcp", "--output-mode", "file"], "working_directory": ".", "tools": ["browser_navigate"]}},
        ) as session:
            done = asyncio.Event()
            error: RuntimeError | None = None
            received_delta = False

            def on_event(event) -> None:
                nonlocal error, received_delta
                match event.data:
                    case AssistantMessageDeltaData(delta_content=delta) if delta:
                        received_delta = True
                        print(delta, end="", flush=True)
                    case AssistantMessageData(content=content) if content and not received_delta:
                        print(content)
                    case SessionErrorData(message=message):
                        error = RuntimeError(message)
                        done.set()
                    case SessionIdleData():
                        done.set()

            session.on(on_event)
            await session.send(f"Use browser_navigate to open {target}, then read_latest_accessibility_snapshot and report the page title.")
            await done.wait()
            if error is not None:
                raise error


if __name__ == "__main__":
    asyncio.run(main())
```

</details>
:::

:::language go
## Wire up scoped Playwright access in Go

### 1. Accept one controlled target

At the start of `main` in `main.go`, validate the startup URL:

```go
if len(os.Args) != 2 {
	fmt.Fprintln(os.Stderr, "Usage: go run . <http-or-https-url>")
	return
}
target := os.Args[1]
if !strings.Contains(target, "://") {
	target = "https://" + target
}
parsed, err := url.ParseRequestURI(target)
if err != nil || parsed.Host == "" || (parsed.Scheme != "http" && parsed.Scheme != "https") {
	fmt.Fprintln(os.Stderr, "Enter an absolute HTTP or HTTPS URL.")
	return
}
```

### 2. Add the permission handler

Before `main`, add exact-URL matching and the permission handler:

```go
func sameURL(requested, allowed string) bool {
	left, leftErr := url.Parse(requested)
	right, rightErr := url.Parse(allowed)
	userInfo := func(value *url.Userinfo) string {
		if value == nil {
			return ""
		}
		return value.String()
	}
	return leftErr == nil && rightErr == nil &&
		strings.EqualFold(left.Scheme, right.Scheme) &&
		strings.EqualFold(left.Hostname(), right.Hostname()) &&
		left.Port() == right.Port() &&
		userInfo(left.User) == userInfo(right.User) &&
		left.EscapedPath() == right.EscapedPath() &&
		left.RawQuery == right.RawQuery &&
		left.Fragment == right.Fragment
}

func permissionForTarget(target string) copilot.PermissionHandlerFunc {
	return func(request copilot.PermissionRequest, _ copilot.PermissionInvocation) (rpc.PermissionDecision, error) {
		raw, _ := json.Marshal(request)
		var value map[string]any
		if json.Unmarshal(raw, &value) == nil && value["kind"] == "mcp" && value["serverName"] == "playwright" {
			toolName, _ := value["toolName"].(string)
			args, _ := value["args"].(map[string]any)
			requested, _ := args["url"].(string)
			if (toolName == "browser_navigate" || toolName == "playwright-browser_navigate") && sameURL(requested, target) {
				return &rpc.PermissionDecisionApproveOnce{}, nil
			}
		}
		feedback := "This workshop allows Playwright to navigate only to the exact requested target."
		return &rpc.PermissionDecisionReject{Feedback: &feedback}, nil
	}
}
```

Accept both bare and prefixed Playwright tool names on the permission path.

### 3. Add the snapshot-reader boundary

Still before `main`, add the no-argument snapshot reader:

```go
const maxSnapshotBytes = 1_000_000

func snapshotReader(workingDirectory string) func(struct{}, copilot.ToolInvocation) (string, error) {
	outputDirectory := filepath.Join(workingDirectory, ".playwright-mcp")
	existing := map[string]struct{}{}
	if entries, err := os.ReadDir(outputDirectory); err == nil {
		for _, entry := range entries {
			if strings.HasPrefix(entry.Name(), "page-") && strings.HasSuffix(entry.Name(), ".yml") {
				existing[filepath.Join(outputDirectory, entry.Name())] = struct{}{}
			}
		}
	}

	return func(_ struct{}, _ copilot.ToolInvocation) (string, error) {
		entries, err := os.ReadDir(outputDirectory)
		if err != nil {
			return "", fmt.Errorf("No current-run Playwright snapshot is available. Call browser_navigate first.")
		}
		type candidate struct {
			path string
			mod  time.Time
		}
		var candidates []candidate
		for _, entry := range entries {
			path := filepath.Join(outputDirectory, entry.Name())
			info, err := entry.Info()
			if _, existed := existing[path]; existed || err != nil || entry.IsDir() ||
				entry.Type()&os.ModeSymlink != 0 || !info.Mode().IsRegular() ||
				info.Size() == 0 || info.Size() > maxSnapshotBytes ||
				!strings.HasPrefix(entry.Name(), "page-") || !strings.HasSuffix(entry.Name(), ".yml") {
				continue
			}
			candidates = append(candidates, candidate{path, info.ModTime()})
		}
		if len(candidates) == 0 {
			return "", fmt.Errorf("No current-run Playwright snapshot is available. Call browser_navigate first.")
		}
		sort.Slice(candidates, func(i, j int) bool { return candidates[i].mod.Before(candidates[j].mod) })
		contents, err := os.ReadFile(candidates[len(candidates)-1].path)
		return string(contents), err
	}
}
```

### 4. Add Playwright MCP and scoped permissions

In `main`, define both local tools and replace the session configuration:

```go
workingDirectory, err := os.Getwd()
if err != nil {
	panic(err)
}
lookup := copilot.DefineTool("accessibility_rule_lookup", "Looks up read-only WCAG guidance maintained by this application.", accessibilityRuleLookup)
lookup.SkipPermission = true
readSnapshot := copilot.DefineTool("read_latest_accessibility_snapshot", "Reads the newest Playwright accessibility snapshot created during this run.", snapshotReader(workingDirectory))
readSnapshot.SkipPermission = true

client := copilot.NewClient(&copilot.ClientOptions{LogLevel: "error"})
if err := client.Start(context.Background()); err != nil {
	panic(err)
}
defer client.Stop()
session, err := client.CreateSession(context.Background(), &copilot.SessionConfig{
	Streaming:           copilot.Bool(true),
	Tools:               []copilot.Tool{lookup, readSnapshot},
	AvailableTools:      []string{"accessibility_rule_lookup", "read_latest_accessibility_snapshot", "playwright-browser_navigate"},
	OnPermissionRequest: permissionForTarget(target),
	MCPServers: map[string]copilot.MCPServerConfig{
		"playwright": copilot.MCPStdioServerConfig{
			Command:          "npx",
			Args:             []string{"-y", "@playwright/mcp@0.0.78", "--browser=msedge", "--output-dir", ".playwright-mcp", "--output-mode", "file"},
			WorkingDirectory: workingDirectory,
			Tools:            []string{"browser_navigate"},
		},
	},
})
if err != nil {
	panic(err)
}
defer session.Disconnect()
if err := streamResponse(session, fmt.Sprintf("Use browser_navigate to open %s, then read_latest_accessibility_snapshot and report the page title.", target)); err != nil {
	panic(err)
}
```

Add the imports used by the new helpers: `encoding/json`, `net/url`, `path/filepath`, `sort`,
`time`, and `"github.com/github/copilot-sdk/go/rpc"`.

## Run it

```bash
go run . "{{TARGET_APP_URL}}"
```

The first run may take longer while `npx` starts Playwright.

Look for a page title such as:

```text
Page title: Blazor Accessibility Target
```

<details>
<summary>Troubleshooting this run</summary>

| Symptom | Fix |
|---|---|
| `npx` cannot be started | Rerun the preflight MCP command and verify Node.js is on `PATH`. |
| Playwright cannot find a browser | Install Edge or Chrome, or configure an installed browser as described by Playwright MCP. |
| A permission is rejected | Use the exact target URL above. The handler intentionally denies other URLs and tools. |
| No current-run snapshot is available | Keep the prompt order: call `browser_navigate` before `read_latest_accessibility_snapshot`. |
| Missing imports | Add `encoding/json`, `net/url`, `path/filepath`, `sort`, `time`, and the `rpc` package. |

</details>

<details>
<summary>Complete Step 4 implementation</summary>

Compare your work with this complete Step 4 implementation.

`main.go` session wiring:

```go
workingDirectory, err := os.Getwd()
if err != nil {
	panic(err)
}
lookup := copilot.DefineTool("accessibility_rule_lookup", "Looks up read-only WCAG guidance maintained by this application.", accessibilityRuleLookup)
lookup.SkipPermission = true
readSnapshot := copilot.DefineTool("read_latest_accessibility_snapshot", "Reads the newest Playwright accessibility snapshot created during this run.", snapshotReader(workingDirectory))
readSnapshot.SkipPermission = true

client := copilot.NewClient(&copilot.ClientOptions{LogLevel: "error"})
if err := client.Start(context.Background()); err != nil {
	panic(err)
}
defer client.Stop()
session, err := client.CreateSession(context.Background(), &copilot.SessionConfig{
	Streaming:           copilot.Bool(true),
	Tools:               []copilot.Tool{lookup, readSnapshot},
	AvailableTools:      []string{"accessibility_rule_lookup", "read_latest_accessibility_snapshot", "playwright-browser_navigate"},
	OnPermissionRequest: permissionForTarget(target),
	MCPServers: map[string]copilot.MCPServerConfig{
		"playwright": copilot.MCPStdioServerConfig{
			Command:          "npx",
			Args:             []string{"-y", "@playwright/mcp@0.0.78", "--browser=msedge", "--output-dir", ".playwright-mcp", "--output-mode", "file"},
			WorkingDirectory: workingDirectory,
			Tools:            []string{"browser_navigate"},
		},
	},
})
if err != nil {
	panic(err)
}
defer session.Disconnect()
if err := streamResponse(session, fmt.Sprintf("Use browser_navigate to open %s, then read_latest_accessibility_snapshot and report the page title.", target)); err != nil {
	panic(err)
}
```

</details>
:::

:::language rust
## Wire up scoped Playwright access in Rust

### 1. Accept one controlled target

At the start of `main` in `src/main.rs`, validate the startup URL:

```rust
let argument = std::env::args()
    .nth(1)
    .ok_or("Usage: cargo run -- <http-or-https-url>")?;
let target_text = if argument.contains("://") {
    argument
} else {
    format!("https://{argument}")
};
let target = Url::parse(&target_text)?;
if !matches!(target.scheme(), "http" | "https") || target.host_str().is_none() {
    return Err("Enter an absolute HTTP or HTTPS URL.".into());
}
```

### 2. Add the permission handler

Add the exact-target permission handler before `main`:

```rust
struct ScopedPermissions {
    target: Url,
}

fn permission_payload(
    extra: &serde_json::Value,
) -> Option<&serde_json::Map<String, serde_json::Value>> {
    match extra.get("permissionRequest") {
        Some(request) => request.as_object(),
        None => extra.as_object(),
    }
}

#[async_trait]
impl PermissionHandler for ScopedPermissions {
    async fn handle(
        &self,
        _session_id: SessionId,
        _request_id: RequestId,
        request: PermissionRequestData,
    ) -> PermissionResult {
        let payload = permission_payload(&request.extra);
        let server = payload
            .and_then(|payload| payload.get("serverName"))
            .and_then(serde_json::Value::as_str);
        let tool = payload
            .and_then(|payload| payload.get("toolName"))
            .and_then(serde_json::Value::as_str);
        let requested = payload
            .and_then(|payload| payload.get("args"))
            .and_then(|args| args.get("url"))
            .and_then(serde_json::Value::as_str)
            .and_then(|value| Url::parse(value).ok());
        if server == Some("playwright")
            && matches!(
                tool,
                Some("browser_navigate" | "playwright-browser_navigate")
            )
            && requested
                .as_ref()
                .is_some_and(|url| same_url(url, &self.target))
        {
            PermissionResult::approve_once()
        } else {
            PermissionResult::reject(Some(
                "This workshop allows Playwright to navigate only to the exact requested target."
                    .to_owned(),
            ))
        }
    }
}

fn same_url(left: &Url, right: &Url) -> bool {
    left.scheme().eq_ignore_ascii_case(right.scheme())
        && left
            .host_str()
            .unwrap_or_default()
            .eq_ignore_ascii_case(right.host_str().unwrap_or_default())
        && left.port() == right.port()
        && left.username() == right.username()
        && left.password() == right.password()
        && left.path() == right.path()
        && left.query() == right.query()
        && left.fragment() == right.fragment()
}
```

### 3. Add the snapshot-reader boundary

Add the no-argument snapshot reader before `main`:

```rust
const MAX_SNAPSHOT_BYTES: u64 = 1_000_000;

struct SnapshotReader {
    output_directory: PathBuf,
    existing: HashSet<PathBuf>,
}

impl SnapshotReader {
    fn new(working_directory: &Path) -> Self {
        let output_directory = working_directory.join(".playwright-mcp");
        let existing = std::fs::read_dir(&output_directory)
            .into_iter()
            .flatten()
            .flatten()
            .filter_map(|entry| {
                let name = entry.file_name();
                let name = name.to_string_lossy();
                (name.starts_with("page-") && name.ends_with(".yml")).then(|| entry.path())
            })
            .collect();
        Self {
            output_directory,
            existing,
        }
    }
}

#[async_trait]
impl ToolHandler for SnapshotReader {
    async fn call(&self, _invocation: ToolInvocation) -> Result<ToolResult, Error> {
        let entries =
            match std::fs::read_dir(&self.output_directory) {
                Ok(entries) => entries,
                Err(_) => return Ok(ToolResult::Text(
                    "No current-run Playwright snapshot is available. Call browser_navigate first."
                        .to_owned(),
                )),
            };
        let newest = entries
            .flatten()
            .filter_map(|entry| {
                let path = entry.path();
                let name = entry.file_name();
                let name = name.to_string_lossy();
                let metadata = std::fs::symlink_metadata(&path).ok()?;
                (!self.existing.contains(&path)
                    && name.starts_with("page-")
                    && name.ends_with(".yml")
                    && !metadata.file_type().is_symlink()
                    && metadata.is_file()
                    && metadata.len() > 0
                    && metadata.len() <= MAX_SNAPSHOT_BYTES)
                    .then_some((metadata.modified().unwrap_or(SystemTime::UNIX_EPOCH), path))
            })
            .max_by_key(|(modified, _)| *modified);
        let Some((_, path)) = newest else {
            return Ok(ToolResult::Text(
                "No current-run Playwright snapshot is available. Call browser_navigate first."
                    .to_owned(),
            ));
        };
        match std::fs::read_to_string(path) {
            Ok(contents) => Ok(ToolResult::Text(contents)),
            Err(_) => Ok(ToolResult::Text(
                "The current-run Playwright snapshot could not be read.".to_owned(),
            )),
        }
    }
}
```

### 4. Add Playwright MCP and scoped permissions

In `main`, define both local tools, configure MCP, and install the permission handler:

```rust
let working_directory = std::env::current_dir()?;
let lookup = Tool::new("accessibility_rule_lookup")
    .with_description("Looks up read-only WCAG guidance maintained by this application.")
    .with_parameters(schema_for::<LookupParams>())
    .with_skip_permission(true)
    .with_handler(Arc::new(AccessibilityRuleLookup));
let reader = Tool::new("read_latest_accessibility_snapshot")
    .with_description(
        "Reads the newest Playwright accessibility snapshot created during this run.",
    )
    .with_parameters(
        serde_json::json!({"type": "object", "properties": {}, "additionalProperties": false}),
    )
    .with_skip_permission(true)
    .with_handler(Arc::new(SnapshotReader::new(&working_directory)));

let mut config = SessionConfig::default();
config.streaming = Some(true);
config.tools = Some(vec![lookup, reader]);
config.available_tools = Some(vec![
    "accessibility_rule_lookup".to_owned(),
    "read_latest_accessibility_snapshot".to_owned(),
    "playwright-browser_navigate".to_owned(),
]);
config.mcp_servers = Some(IndexMap::from([(
    "playwright".to_owned(),
    McpServerConfig::Stdio(McpStdioServerConfig {
        command: "npx".to_owned(),
        args: vec![
            "-y".to_owned(),
            "@playwright/mcp@0.0.78".to_owned(),
            "--browser=msedge".to_owned(),
            "--output-dir".to_owned(),
            ".playwright-mcp".to_owned(),
            "--output-mode".to_owned(),
            "file".to_owned(),
        ],
        tools: Some(vec!["browser_navigate".to_owned()]),
        working_directory: Some(working_directory.display().to_string()),
        ..Default::default()
    }),
)]));
let config = config.with_permission_handler(Arc::new(ScopedPermissions {
    target: target.clone(),
}));

let client = Client::start(ClientOptions::default()).await?;
let session = client.create_session(config).await?;
stream_response!(
    session,
    format!(
        "Use browser_navigate to open {target}, then read_latest_accessibility_snapshot and report the page title."
    )
);
session.disconnect().await?;
client.stop().await?;
```

Add the imports used by the new helpers, including
`github_copilot_sdk::handler::{PermissionHandler, PermissionResult}`,
`McpServerConfig`, `McpStdioServerConfig`, `PermissionRequestData`, `RequestId`, `SessionId`,
`indexmap::IndexMap`, and `url::Url`.

## Run it

```bash
cargo run -- "{{TARGET_APP_URL}}"
```

The first run may take longer while `npx` starts Playwright.

Look for a page title such as:

```text
Page title: Blazor Accessibility Target
```

<details>
<summary>Troubleshooting this run</summary>

| Symptom | Fix |
|---|---|
| `npx` cannot be started | Rerun the preflight MCP command and verify Node.js is on `PATH`. |
| Playwright cannot find a browser | Install Edge or Chrome, or configure an installed browser as described by Playwright MCP. |
| A permission is rejected | Use the exact target URL above. The handler intentionally denies other URLs and tools. |
| No current-run snapshot is available | Keep the prompt order: call `browser_navigate` before `read_latest_accessibility_snapshot`. |
| Trait or type unresolved | Keep the permission, MCP, `IndexMap`, and `Url` imports shown above. |

</details>

<details>
<summary>Complete Step 4 implementation</summary>

Compare your work with this complete Step 4 implementation.

Session wiring from `src/main.rs`:

```rust
let mut config = SessionConfig::default();
config.streaming = Some(true);
config.tools = Some(vec![lookup, reader]);
config.available_tools = Some(vec![
    "accessibility_rule_lookup".to_owned(),
    "read_latest_accessibility_snapshot".to_owned(),
    "playwright-browser_navigate".to_owned(),
]);
config.mcp_servers = Some(IndexMap::from([(
    "playwright".to_owned(),
    McpServerConfig::Stdio(McpStdioServerConfig {
        command: "npx".to_owned(),
        args: vec![
            "-y".to_owned(),
            "@playwright/mcp@0.0.78".to_owned(),
            "--browser=msedge".to_owned(),
            "--output-dir".to_owned(),
            ".playwright-mcp".to_owned(),
            "--output-mode".to_owned(),
            "file".to_owned(),
        ],
        tools: Some(vec!["browser_navigate".to_owned()]),
        working_directory: Some(working_directory.display().to_string()),
        ..Default::default()
    }),
)]));
let config = config.with_permission_handler(Arc::new(ScopedPermissions {
    target: target.clone(),
}));

let client = Client::start(ClientOptions::default()).await?;
let session = client.create_session(config).await?;
stream_response!(session, mcp_safety_prompt(&target));
```

</details>
:::

:::language java
## Wire up scoped Playwright access in Java

### 1. Accept one controlled target

At the start of `main` in
`src/main/java/workshop/AccessibilityReport.java`, validate the startup URL:

```java
RunOptions options = parseRunOptions(args);
URI target = options.target();
Path workingDirectory = Path.of("").toAbsolutePath().normalize();
if (options.allowLocalDemoMcp()) {
    System.err.println("WARNING: Local demo fallback enabled. MCP request payload fields are unavailable, "
            + "so this run approves only the mcp permission kind, not an exact target. "
            + "Use only with the controlled workshop target.");
}
```

Add the parser helper:

```java
private static URI parseTarget(String value) throws URISyntaxException {
    String candidate = value.contains("://") ? value : "https://" + value;
    URI target = new URI(candidate);
    if (!target.isAbsolute()
            || target.getHost() == null
            || !("http".equalsIgnoreCase(target.getScheme())
                    || "https".equalsIgnoreCase(target.getScheme()))) {
        throw new IllegalArgumentException("Enter an absolute HTTP or HTTPS URL.");
    }
    return target;
}
```

### 2. Add the permission handler

Approve only exact-target Playwright navigation on the session configuration:

```java
.setOnPermissionRequest((request, ignored) -> {
    if ("mcp".equals(request.getKind())
            && isExactNavigation(request.getExtensionData(), target)) {
        return java.util.concurrent.CompletableFuture.completedFuture(
                PermissionRequestResult.approveOnce());
    }
    // SDK issue #2273 currently prevents inspecting MCP request fields for the exact check.
    if (options.allowLocalDemoMcp() && "mcp".equals(request.getKind())) {
        return java.util.concurrent.CompletableFuture.completedFuture(
                PermissionRequestResult.approveOnce());
    }
    return java.util.concurrent.CompletableFuture.completedFuture(
            PermissionRequestResult.reject(
                    "This workshop allows Playwright to navigate only to the exact requested target. "
                            + "MCP requests without target data remain denied unless the explicit "
                            + LOCAL_DEMO_MCP_FLAG + " local-demo fallback is enabled."));
})
```

> **Temporary Java SDK limitation and local-demo fallback:** By default this is fail-closed: it
> approves only an `mcp` request whose payload proves the configured Playwright navigation is the
> exact entered URL. Current Java SDK releases do not expose those MCP request fields
> ([github/copilot-sdk#2273](https://github.com/github/copilot-sdk/issues/2273)), so the
> default path rejects that request rather than guessing. For the controlled workshop target only,
> pass `--allow-local-demo-mcp`. That explicit flag approves one `mcp` request at a time; it does
> **not** use `APPROVE_ALL`, and the MCP configuration still exposes only Playwright
> `browser_navigate`. It cannot enforce the exact URL while the SDK payload is unavailable. Never
> enable it for a production, shared, or untrusted target.

Add this option parser beside `parseTarget`:

```java
private static final String LOCAL_DEMO_MCP_FLAG = "--allow-local-demo-mcp";

private static RunOptions parseRunOptions(String[] args) throws URISyntaxException {
    boolean allowLocalDemoMcp = false;
    String target = null;
    for (String arg : args) {
        if (LOCAL_DEMO_MCP_FLAG.equals(arg)) {
            if (allowLocalDemoMcp) {
                throw new IllegalArgumentException("Specify " + LOCAL_DEMO_MCP_FLAG + " at most once.");
            }
            allowLocalDemoMcp = true;
        } else if (target == null) {
            target = arg;
        } else {
            throw new IllegalArgumentException(usage());
        }
    }
    if (target == null) {
        throw new IllegalArgumentException(usage());
    }
    return new RunOptions(parseTarget(target), allowLocalDemoMcp);
}

private static String usage() {
    return "Usage: mvn compile exec:java -Dexec.args=\"["
            + LOCAL_DEMO_MCP_FLAG + "] <http-or-https-url>\"";
}

private record RunOptions(URI target, boolean allowLocalDemoMcp) {
}
```

Add the URL-matching helpers:

```java
private static boolean isExactNavigation(Map<String, Object> request, URI target) {
    if (request == null
            || !"playwright".equals(request.get("serverName"))
            || !(request.get("toolName") instanceof String toolName)
            || !("browser_navigate".equals(toolName)
                    || "playwright-browser_navigate".equals(toolName))
            || !(request.get("args") instanceof Map<?, ?> args)
            || !(args.get("url") instanceof String requested)) {
        return false;
    }
    try {
        return sameUrl(new URI(requested), target);
    } catch (URISyntaxException ignored) {
        return false;
    }
}

private static boolean sameUrl(URI requested, URI allowed) {
    return equalsIgnoreCase(requested.getScheme(), allowed.getScheme())
            && equalsIgnoreCase(requested.getHost(), allowed.getHost())
            && requested.getPort() == allowed.getPort()
            && java.util.Objects.equals(requested.getRawUserInfo(), allowed.getRawUserInfo())
            && java.util.Objects.equals(requested.getRawPath(), allowed.getRawPath())
            && java.util.Objects.equals(requested.getRawQuery(), allowed.getRawQuery())
            && java.util.Objects.equals(requested.getRawFragment(), allowed.getRawFragment());
}

private static boolean equalsIgnoreCase(String left, String right) {
    return left == null ? right == null : right != null && left.equalsIgnoreCase(right);
}
```

### 3. Add the snapshot-reader boundary

Register a no-argument snapshot reader that only returns current-run Playwright files:

```java
var readSnapshot = ToolDefinition.from(
        "read_latest_accessibility_snapshot",
        "Reads the newest Playwright accessibility snapshot created during this run.",
        new SnapshotReader(workingDirectory)::read).skipPermission(true);
```

Add the nested reader class:

```java
private static final class SnapshotReader {
    private final Path outputDirectory;
    private final Set<Path> existing;

    private SnapshotReader(Path workingDirectory) throws IOException {
        outputDirectory = workingDirectory.resolve(".playwright-mcp").normalize();
        existing = new HashSet<>();
        if (Files.isDirectory(outputDirectory, LinkOption.NOFOLLOW_LINKS)) {
            try (Stream<Path> paths = Files.list(outputDirectory)) {
                paths.filter(SnapshotReader::isSnapshotName).forEach(existing::add);
            }
        }
    }

    private String read() {
        try (Stream<Path> paths = Files.list(outputDirectory)) {
            Path newest = paths
                    .filter(path -> !existing.contains(path))
                    .filter(SnapshotReader::isSnapshotName)
                    .filter(path -> !Files.isSymbolicLink(path))
                    .filter(SnapshotReader::isSafeSnapshot)
                    .max(Comparator.comparing(this::modifiedTime))
                    .orElseThrow(() -> new IllegalStateException(
                            "No current-run Playwright snapshot is available. Call browser_navigate first."));
            return Files.readString(newest, StandardCharsets.UTF_8);
        } catch (IOException exception) {
            throw new IllegalStateException(
                    "No current-run Playwright snapshot is available. Call browser_navigate first.",
                    exception);
        }
    }

    private static boolean isSnapshotName(Path path) {
        String name = path.getFileName().toString();
        return name.startsWith("page-") && name.endsWith(".yml");
    }

    private static boolean isSafeSnapshot(Path path) {
        try {
            BasicFileAttributes attributes = Files.readAttributes(
                    path, BasicFileAttributes.class, LinkOption.NOFOLLOW_LINKS);
            return attributes.isRegularFile()
                    && !attributes.isSymbolicLink()
                    && attributes.size() > 0
                    && attributes.size() <= MAX_SNAPSHOT_BYTES;
        } catch (IOException exception) {
            return false;
        }
    }

    private java.nio.file.attribute.FileTime modifiedTime(Path path) {
        try {
            return Files.getLastModifiedTime(path, LinkOption.NOFOLLOW_LINKS);
        } catch (IOException exception) {
            return java.nio.file.attribute.FileTime.fromMillis(0);
        }
    }
}
```

### 4. Add Playwright MCP and scoped permissions

Build the full session configuration and send the browser evidence prompt:

```java
var lookup = ToolDefinition.from(
        "accessibility_rule_lookup",
        "Looks up read-only WCAG guidance maintained by this application.",
        Param.of(String.class, "query", "The accessibility issue or WCAG criterion to look up."),
        AccessibilityReport::lookupRule).skipPermission(true);
var readSnapshot = ToolDefinition.from(
        "read_latest_accessibility_snapshot",
        "Reads the newest Playwright accessibility snapshot created during this run.",
        new SnapshotReader(workingDirectory)::read).skipPermission(true);

var config = new SessionConfig()
        .setStreaming(true)
        .setTools(List.of(lookup, readSnapshot))
        .setAvailableTools(List.of(
                "accessibility_rule_lookup",
                "read_latest_accessibility_snapshot",
                "playwright-browser_navigate"))
        .setMcpServers(Map.of("playwright", new McpStdioServerConfig()
                .setCommand("npx")
                .setArgs(List.of("-y", "@playwright/mcp@0.0.78", "--browser=msedge", "--output-dir", ".playwright-mcp", "--output-mode", "file"))
                .setWorkingDirectory(workingDirectory.toString())
                .setTools(List.of("browser_navigate"))))
        .setOnPermissionRequest((request, ignored) -> {
            if ("mcp".equals(request.getKind())
                    && isExactNavigation(request.getExtensionData(), target)) {
                return java.util.concurrent.CompletableFuture.completedFuture(
                        PermissionRequestResult.approveOnce());
            }
            if (options.allowLocalDemoMcp() && "mcp".equals(request.getKind())) {
                return java.util.concurrent.CompletableFuture.completedFuture(
                        PermissionRequestResult.approveOnce());
            }
            return java.util.concurrent.CompletableFuture.completedFuture(
                    PermissionRequestResult.reject(
                            "This workshop allows Playwright to navigate only to the exact requested target. "
                                    + "MCP requests without target data remain denied unless the explicit "
                                    + LOCAL_DEMO_MCP_FLAG + " local-demo fallback is enabled."));
        });

try (var client = new CopilotClient()) {
    client.start().get();
    var session = client.createSession(config).get();
    var response = session.sendAndWait(new MessageOptions().setPrompt(
            """
            Open %s with browser_navigate.
            1. Use browser_navigate to open that exact URL.
            2. Call read_latest_accessibility_snapshot to inspect its accessibility tree.
            3. Return the observed page title only.

            The permission handler must approve only this exact Playwright navigation target."""
                    .formatted(target))).get();
    if (response == null) {
        throw new IllegalStateException("Copilot completed without an assistant message.");
    }
    System.out.println(response.getData().content());
}
```

Add the MCP and permission imports:

```java
import com.github.copilot.rpc.McpStdioServerConfig;
import com.github.copilot.rpc.PermissionRequestResult;
```

## Run it

```bash
mvn compile exec:java -Dexec.args="--allow-local-demo-mcp {{TARGET_APP_URL}}"
```

The first run may take longer while `npx` starts Playwright. This command intentionally opts into
the temporary local-demo fallback above; omit the flag to keep the strict fail-closed policy.

Look for a page title such as:

```text
Page title: Blazor Accessibility Target
```

<details>
<summary>Troubleshooting this run</summary>

| Symptom | Fix |
|---|---|
| `npx` cannot be started | Rerun the preflight MCP command and verify Node.js is on `PATH`. |
| Playwright cannot find a browser | Install Edge or Chrome, or configure an installed browser as described by Playwright MCP. |
| A permission is rejected | The default handler intentionally denies missing or non-exact request payloads. Use the exact target when the SDK provides it; for this controlled target only, add `--allow-local-demo-mcp` until [#2273](https://github.com/github/copilot-sdk/issues/2273) is fixed. |
| No current-run snapshot is available | Keep the prompt order: call `browser_navigate` before `read_latest_accessibility_snapshot`. |
| MCP or permission types unresolved | Add the `McpStdioServerConfig` and `PermissionRequestResult` imports. |

</details>

<details>
<summary>Complete Step 4 implementation</summary>

Compare your work with this complete Step 4 implementation.

Session wiring from `AccessibilityReport.java`:

```java
var config = new SessionConfig()
        .setStreaming(true)
        .setTools(List.of(lookup, readSnapshot))
        .setAvailableTools(List.of(
                "accessibility_rule_lookup",
                "read_latest_accessibility_snapshot",
                "playwright-browser_navigate"))
        .setMcpServers(Map.of("playwright", new McpStdioServerConfig()
                .setCommand("npx")
                .setArgs(List.of("-y", "@playwright/mcp@0.0.78", "--browser=msedge", "--output-dir", ".playwright-mcp", "--output-mode", "file"))
                .setWorkingDirectory(workingDirectory.toString())
                .setTools(List.of("browser_navigate"))))
        .setOnPermissionRequest((request, ignored) -> {
            if ("mcp".equals(request.getKind())
                    && isExactNavigation(request.getExtensionData(), target)) {
                return java.util.concurrent.CompletableFuture.completedFuture(
                        PermissionRequestResult.approveOnce());
            }
            if (options.allowLocalDemoMcp() && "mcp".equals(request.getKind())) {
                return java.util.concurrent.CompletableFuture.completedFuture(
                        PermissionRequestResult.approveOnce());
            }
            return java.util.concurrent.CompletableFuture.completedFuture(
                    PermissionRequestResult.reject(
                            "This workshop allows Playwright to navigate only to the exact requested target. "
                                    + "MCP requests without target data remain denied unless the explicit "
                                    + LOCAL_DEMO_MCP_FLAG + " local-demo fallback is enabled."));
        });
```

</details>
:::

> **You're ready to combine tools when:** the terminal shows named Playwright tool activity and
> prints the target page title.

## Check your understanding

Why is Playwright an MCP server here instead of another application-owned callback?

<details>
<summary>Check your answer</summary>

Playwright provides reusable browser automation in its own process, with its own dependencies. MCP
connects it without moving browser logic into the application's domain code, and permissions
protect the process boundary.

</details>

## Learn more

- [Model Context Protocol](https://modelcontextprotocol.io/): the open standard the Playwright
  server implements, and the vocabulary its tool names come from.
- [MCP debugging](https://github.com/github/copilot-sdk/blob/main/docs/troubleshooting/mcp-debugging.md):
  diagnosing a server that will not start or that exposes different tools than you expected.
- [Hook error handling](https://github.com/github/copilot-sdk/blob/main/docs/hooks/error-handling.md):
  deciding what a session does when a tool call or a handler fails.
- [Plugin directories](https://github.com/github/copilot-sdk/blob/main/docs/features/plugin-directories.md):
  bundling MCP servers, skills, and hooks so a session loads them as one unit.

Continue to [Step 5: Combine local and MCP tools](05-combine-tools.md).
