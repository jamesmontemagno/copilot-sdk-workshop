# Step 7: Run and explain the application

> **Time:** 10 minutes

## What you'll be ready to explain

You'll run the complete application and explain its state, tool boundaries, permission boundary,
and report limitations.

## See the whole agent system

:::language dotnet
The finished application is an agent host. Its session coordinates a model, an application-owned
function, and a browser running in another process:

```text
Console application
  |
  +-- CopilotClient -------- runtime connection
       |
       `-- CopilotSession --- one conversation and its context
            |
            +-- accessibility_rule_lookup
            |     same process, application-owned data
            |
            `-- Playwright MCP
                  separate process, scoped permission handler
                       |
                       `-- Browser target
```
:::

:::language nodejs
The finished application is an agent host. Its session coordinates a model, an application-owned
function, and a browser running in another process:

```text
Node.js application
  |
  +-- CopilotClient -------- runtime connection
       |
       `-- CopilotSession --- one conversation and its context
            |
            +-- accessibility_rule_lookup
            |     same process, application-owned data
            |
            `-- Playwright MCP
                  separate process, scoped permission handler
                       |
                       `-- Browser target
```

The completed report is also in
[`finished/nodejs/accessibility-report`](https://github.com/jamesmontemagno/copilot-sdk-workshop/tree/main/finished/nodejs/accessibility-report).
:::

:::language python
The finished application is an agent host. Its session coordinates a model, an application-owned
function, and a browser running in another process:

```text
Python application
  |
  +-- CopilotClient -------- runtime connection
       |
       `-- session ---------- one conversation and its context
            |
            +-- accessibility_rule_lookup
            |     same process, application-owned data
            |
            `-- Playwright MCP
                  separate process, scoped permission handler
                       |
                       `-- Browser target
```

The completed report is also in
[`finished/python/accessibility-report`](https://github.com/jamesmontemagno/copilot-sdk-workshop/tree/main/finished/python/accessibility-report).
:::

:::language go
The finished application is an agent host. Its session coordinates a model, an application-owned
function, and a browser running in another process:

```text
Go application
  |
  +-- Client ---------------- runtime connection
       |
       `-- Session ---------- one conversation and its context
            |
            +-- accessibility_rule_lookup
            |     same process, application-owned data
            |
            `-- Playwright MCP
                  separate process, scoped permission handler
                       |
                       `-- Browser target
```
:::

:::language rust
The finished application is an agent host. Its session coordinates a model, an application-owned
function, and a browser running in another process:

```text
Rust application
  |
  +-- Client ---------------- runtime connection
       |
       `-- Session ---------- one conversation and its context
            |
            +-- accessibility_rule_lookup
            |     same process, application-owned data
            |
            `-- Playwright MCP
                  separate process, scoped permission handler
                       |
                       `-- Browser target
```
:::

:::language java
The finished application is an agent host. Its session coordinates a model, an application-owned
function, and a browser running in another process:

```text
Java application
  |
  +-- CopilotClient -------- runtime connection
       |
       `-- session ---------- one conversation and its context
            |
            +-- accessibility_rule_lookup
            |     same process, application-owned data
            |
            `-- Playwright MCP
                  separate process, scoped permission handler
                       |
                       `-- Browser target
```
:::

## Take the design beyond this workshop

Understanding these boundaries lets you reuse the design in another application instead of only
reproducing the workshop code. A database lookup, deployment service, or issue tracker may use
different tools, but the same ownership and trust questions apply.

:::language dotnet
The complete flow is
`URL -> Playwright inspection -> C# WCAG lookup -> structured accessibility report`.
:::

:::language nodejs
The complete flow is
`URL -> Playwright inspection -> TypeScript WCAG lookup -> structured accessibility report`.
:::

:::language python
The complete flow is
`URL -> Playwright inspection -> Python WCAG lookup -> structured accessibility report`.
:::

:::language go
The complete flow is
`URL -> Playwright inspection -> Go WCAG lookup -> structured accessibility report`.
:::

:::language rust
The complete flow is
`URL -> Playwright inspection -> Rust WCAG lookup -> structured accessibility report`.
:::

:::language java
The complete flow is
`URL -> Playwright inspection -> Java WCAG lookup -> structured accessibility report`.
:::

## Take a victory lap

There is no code to change. Keep the Step 6 implementation in place so this run tests the
application you built.

## Run it

:::language dotnet
```bash
dotnet run --project workshop-app
```
:::
:::language nodejs
```bash
npm --prefix workshop-app start -- "{{TARGET_APP_URL}}"
```
:::
:::language python
```bash
python workshop-app/main.py "{{TARGET_APP_URL}}"
```
:::
:::language go
```bash
go -C workshop-app run . "{{TARGET_APP_URL}}"
```
:::
:::language rust
```bash
cargo run --manifest-path workshop-app/Cargo.toml -- "{{TARGET_APP_URL}}"
```
:::
:::language java
```bash
mvn -f workshop-app/pom.xml compile exec:java -Dexec.args="--allow-local-demo-mcp {{TARGET_APP_URL}}"
```

> **Java local-demo warning:** This explicit flag is a temporary workaround for
> [github/copilot-sdk#2273](https://github.com/github/copilot-sdk/issues/2273). Without it,
> the callback fails closed unless it can verify the exact URL from the permission payload. With it,
> the session approves only the `mcp` permission kind, one request at a time, under the configured
> Playwright `browser_navigate` allowlist; it cannot enforce the exact target. Use it only for the
> controlled local workshop target, never for production, shared, or untrusted URLs.
:::
Use the workshop target:

```text
{{TARGET_APP_URL}}
```

Watch for all five stages:

1. The client connects and creates one session.
2. Playwright navigates to the exact target and creates an accessibility snapshot.
3. The narrow local reader returns that current-run snapshot.
4. The local catalog is called for browser-supported findings.
5. The response follows the report contract and states its limits.

:::language dotnet
Your transcript will vary, but it should have this shape:

```text
=== Accessibility Report Generator ===

Enter URL to analyze: {{TARGET_APP_URL}}

Connected to the Copilot runtime: ...
Analyzing: {{TARGET_APP_URL}}

[tool:start] browser_navigate / playwright-browser_navigate
[tool:done] success=True
[tool:start] read_latest_accessibility_snapshot
[tool:done] success=True
[tool:start] accessibility_rule_lookup
[tool:done] success=True
...

# Accessibility review
## Finding 1: ...
- Evidence: ...
- WCAG criterion: ...
- Recommended remediation: ...
## Review limits
...
```
:::

:::language nodejs
Your transcript will vary, but it should have this shape:

```text
[tool:start] browser_navigate
[tool:done] success=true
[tool:start] read_latest_accessibility_snapshot
[tool:done] success=true
[tool:start] accessibility_rule_lookup
[tool:done] success=true
...

# Accessibility review
## Finding 1: ...
- Evidence: ...
- WCAG criterion: ...
- Recommended remediation: ...
## Review limits
...
```

`streamResponse` prints tool start/done lines and streams the assistant text to stdout.
:::

:::language python
Your transcript will vary, but it should have this shape:

```text
[tool:start] browser_navigate
[tool:done] success=True
[tool:start] read_latest_accessibility_snapshot
[tool:done] success=True
[tool:start] accessibility_rule_lookup
[tool:done] success=True
...

# Accessibility review
## Finding 1: ...
- Evidence: ...
- WCAG criterion: ...
- Recommended remediation: ...
## Review limits
...
```

`main.py` launches `report.main`, which waits on `session.idle` after streaming deltas.
:::

:::language go
Your transcript will vary, but it should have this shape:

```text
# Accessibility review
## Finding 1: ...
- Evidence: ...
- WCAG criterion: ...
- Recommended remediation: ...
## Review limits
...
```

Explain that `Client` owns the Copilot CLI lifecycle, the `Session` owns one conversation, and the
permission handler gates external navigation. The expected report is evidence-bound.
:::

:::language rust
Your transcript will vary, but it should have this shape:

```text
# Accessibility review
## Finding 1: ...
- Evidence: ...
- WCAG criterion: ...
- Recommended remediation: ...
## Review limits
...
```

Explain that `Client` manages the runtime, `Session` dispatches events, typed tools are app-owned,
and the permission handler trusts only exact navigation.
:::

:::language java
Your transcript will vary, but it should have this shape:

```text
# Accessibility review
## Finding 1: ...
- Evidence: ...
- WCAG criterion: ...
- Recommended remediation: ...
## Review limits
...
```

Explain that Maven compiles the Java 17 application, `CopilotClient` manages the runtime, and tools
remain scoped. By default the permission callback accepts only the canonical URL; with the explicit
local-demo flag it is limited to the configured `mcp` kind but cannot verify that URL.
:::

The controlled target intentionally includes browser-observable issues: a missing text alternative,
no `main` landmark, an illogical heading sequence, and a textbox without an accessible name.
Compare the report with the
[published target HTML](https://github.com/jamesmontemagno/copilot-sdk-workshop/blob/main/docs/target-app/index.html);
do not accept a finding that is absent from both the snapshot and source.

<details>
<summary>Troubleshooting the complete run</summary>

| Symptom | Fix |
|---|---|
| A known issue is omitted | Agent output can vary. Rerun once, but require evidence rather than forcing a predetermined answer. |
| A reported issue is not in the page | Reject it as ungrounded; the prompt requires specific browser evidence. |
| A tool is denied | Check that `browser_navigate` uses the exact entered target. |
| The reader finds no snapshot | Keep the prompt order: navigate before calling `read_latest_accessibility_snapshot`. |
| The runtime cannot start | Re-authenticate with `copilot login`, confirm the CLI is on `PATH`, and retry the run command for your language. |

</details>

> **You have completed the core workshop when:** the report is grounded, the tool names are visible,
> and you can answer the architecture questions below without reading the code.

## Check your understanding

1. What state belongs to the session?
2. Why is the WCAG catalog local?
3. Why is Playwright external?
4. Where are permissions enforced?
5. What changes when another MCP server is added?

<details>
<summary>Compare your explanation</summary>

1. The session owns one conversation's messages, model response, and tool results.
2. The application owns the catalog data and deterministic lookup, so the function stays local.
3. Playwright is a reusable browser capability with its own Node.js process and dependencies.
4. The MCP tool allowlist exposes only navigation, and the permission handler approves only
   the exact target. The trusted local reader accepts no path and reads only a new generated
   snapshot; the catalog is also read-only. Those application-owned tools skip permission.
5. Add the server configuration, expose only needed tools, define its trust policy, and keep
   observing its calls through the same session event stream.

</details>

## Keep exploring

Try [Optional: Select a model](08-model-selection.md) if your application needs explicit control
over model choice, then continue to [Optional: Generate an interactive HTML report](09-interactive-html-report.md).
You can also go straight to the HTML report extension. Otherwise, the core workshop is complete.

:::language dotnet
Complete references:

- [Finished accessibility reporter](https://github.com/jamesmontemagno/copilot-sdk-workshop/tree/main/finished/dotnet/accessibility-report)
- [GitHub Copilot SDK for .NET](https://github.com/github/copilot-sdk/tree/main/dotnet)
- [Playwright MCP](https://github.com/microsoft/playwright-mcp)
:::

:::language nodejs
Complete references:

- [Finished accessibility reporter](https://github.com/jamesmontemagno/copilot-sdk-workshop/tree/main/finished/nodejs/accessibility-report)
- [GitHub Copilot SDK for Node.js](https://github.com/github/copilot-sdk/tree/main/nodejs)
- [Playwright MCP](https://github.com/microsoft/playwright-mcp)
:::

:::language python
Complete references:

- [Finished accessibility reporter](https://github.com/jamesmontemagno/copilot-sdk-workshop/tree/main/finished/python/accessibility-report)
- [GitHub Copilot SDK for Python](https://github.com/github/copilot-sdk/tree/main/python)
- [Playwright MCP](https://github.com/microsoft/playwright-mcp)
:::

:::language go
Complete references:

- [Finished accessibility reporter](https://github.com/jamesmontemagno/copilot-sdk-workshop/tree/main/finished/go/accessibility-report)
- [GitHub Copilot SDK for Go](https://github.com/github/copilot-sdk/tree/main/go)
- [Playwright MCP](https://github.com/microsoft/playwright-mcp)

If the CLI is missing, install it rather than granting broader permissions.
:::

:::language rust
Complete references:

- [Finished accessibility reporter](https://github.com/jamesmontemagno/copilot-sdk-workshop/tree/main/finished/rust/accessibility-report)
- [GitHub Copilot SDK for Rust](https://github.com/github/copilot-sdk/tree/main/rust)
- [Playwright MCP](https://github.com/microsoft/playwright-mcp)

If it cannot start, install and authenticate the Copilot CLI.
:::

:::language java
Complete references:

- [Finished accessibility reporter](https://github.com/jamesmontemagno/copilot-sdk-workshop/tree/main/finished/java/accessibility-report)
- [GitHub Copilot SDK for Java](https://github.com/github/copilot-sdk/tree/main/java)
- [Playwright MCP](https://github.com/microsoft/playwright-mcp)

If the runtime is unavailable, install the Copilot CLI; do not replace Maven with JBang or Gradle.
:::
