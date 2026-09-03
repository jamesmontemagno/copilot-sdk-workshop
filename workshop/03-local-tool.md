# Step 3: Add application-owned knowledge

> **Time:** 15 minutes

## What you'll add

You'll give Copilot a typed local tool that retrieves an exact criterion and remediation from the
application-owned Web Content Accessibility Guidelines (WCAG) catalog.

## Give Copilot a tool your app owns

**Tool calling** lets the model request a capability while it works on an answer. A **local tool**
runs inside your application process. The model decides when to request it, but your code still owns
the data, validation, execution, and result.

In this step, you expose application-owned WCAG guidance as `accessibility_rule_lookup`, register
that tool with the session, and explicitly make it available to the model.

## Bring your own source of truth

The model's general knowledge is not a substitute for data your application owns. This local tool
returns a small, exact result from deterministic code you can test instead of putting the full
catalog in every prompt.

`skip permission` is deliberate here because the tool only reads application-owned data. The
external MCP process in the next step will use a permission boundary instead.

:::language dotnet
## Wire up the C# lookup

### 1. Add the catalog lookup tool

At the top of `Helpers/AccessibilityRuleCatalog.cs`, insert:

```csharp
using System.ComponentModel;
using GitHub.Copilot;
using Microsoft.Extensions.AI;
```

Inside `AccessibilityRuleCatalog`, after the existing `Rules` array, insert:

```csharp
public static AIFunction CreateLookupTool() => CopilotTool.DefineTool(
    ([Description("The accessibility issue or WCAG criterion to look up.")] string query) =>
        Task.FromResult(Lookup(query)),
    toolOptions: new CopilotToolOptions { SkipPermission = true },
    factoryOptions: new AIFunctionFactoryOptions
    {
        Name = "accessibility_rule_lookup",
        Description = "Looks up read-only WCAG guidance maintained by this application."
    });

public static AccessibilityRule Lookup(string query)
{
    var normalizedQuery = query.Trim();
    return Rules.FirstOrDefault(rule =>
               normalizedQuery.Contains(rule.Criterion, StringComparison.OrdinalIgnoreCase) ||
               normalizedQuery.Contains(rule.Title, StringComparison.OrdinalIgnoreCase) ||
               rule.Keywords.Any(keyword =>
                   normalizedQuery.Contains(keyword, StringComparison.OrdinalIgnoreCase)))
           ?? new AccessibilityRule(
               "No exact match",
               "Criterion not found",
               "The issue is not represented in the workshop catalog.",
               "Verify the evidence and consult the complete WCAG reference.",
               []);
}
```

### 2. Show tool activity

In `Helpers/ResponseStreamer.cs`, insert these cases before `SessionIdleEvent`:

```csharp
case ToolExecutionStartEvent tool:
    Console.WriteLine($"\n[tool:start] {tool.Data.ToolName}");
    break;
case ToolExecutionCompleteEvent tool:
    Console.WriteLine($"[tool:done] success={tool.Data.Success}");
    break;
```

### 3. Register and request the tool

Replace the session configuration and send call in `Program.cs`:

```csharp
await using var session = await client.CreateSessionAsync(new SessionConfig
{
    Streaming = true,
    Tools = [AccessibilityRuleCatalog.CreateLookupTool()],
    AvailableTools = ["accessibility_rule_lookup"]
});

Console.WriteLine("\nCopilot:");
await ResponseStreamer.SendAndPrintAsync(
    session,
    "Use accessibility_rule_lookup to explain how to fix an input with no accessible name.");
```

## Run it

```bash
dotnet run
```

Look for the tool name and its mapping to 4.1.2:

```text
[tool:start] accessibility_rule_lookup
[tool:done] success=True

WCAG 4.1.2 Name, Role, Value ...
```

<details>
<summary>Troubleshooting this run</summary>

| Symptom | Fix |
|---|---|
| No tool event appears | Keep the explicit `Use accessibility_rule_lookup` instruction in this learning step. |
| The compiler cannot find `AIFunction` | Add `using Microsoft.Extensions.AI;` to the catalog file. |
| The result says no exact match | Confirm the prompt contains `accessible name`, a keyword in the starter data. |

</details>

<details>
<summary>Complete Step 3 implementation</summary>

Compare your version with this complete Step 3 implementation.

`Program.cs`:

```csharp
using GitHub.Copilot;
using HelloCopilotSDK.Helpers;

Console.WriteLine("=== Application-owned WCAG guidance ===\n");

await using var client = new CopilotClient();
await client.StartAsync();

var ping = await client.PingAsync("workshop");
Console.WriteLine($"Connected to the Copilot runtime: {ping.Message}\n");

await using var session = await client.CreateSessionAsync(new SessionConfig
{
    Streaming = true,
    Tools = [AccessibilityRuleCatalog.CreateLookupTool()],
    AvailableTools = ["accessibility_rule_lookup"]
});

Console.WriteLine("Copilot:");
await ResponseStreamer.SendAndPrintAsync(
    session,
    "Use accessibility_rule_lookup to explain how to fix an input with no accessible name.");
```

The catalog tool and lookup live in `Helpers/AccessibilityRuleCatalog.cs`. Tool start and completion
printing live in `Helpers/ResponseStreamer.cs`.

</details>
:::

:::language nodejs
## Wire up the TypeScript lookup

### 1. Inspect the prebuilt typed tool

Open `src/workshop.ts`. The starter already imports the catalog and defines this local tool:

```typescript
export const accessibilityRuleLookup = defineTool("accessibility_rule_lookup", {
  description: "Looks up read-only WCAG guidance maintained by this application.",
  parameters: z.object({ query: z.string().describe("The accessibility issue or WCAG criterion to look up.") }),
  skipPermission: true,
  handler: async ({ query }) => {
    const normalized = query.trim().toLowerCase();
    return accessibilityRules.find((rule) => normalized.includes(rule.criterion.toLowerCase()) || normalized.includes(rule.title.toLowerCase()) || rule.keywords.some((keyword) => normalized.includes(keyword))) ?? noMatch;
  },
});
```

The Zod schema gives the model a typed `query` argument. The handler searches
`accessibilityRules`, which remains application-owned. `skipPermission: true` is intentional because
this tool only returns application-owned read-only data.

### 2. Confirm tool activity printing

In the same file, `streamResponse` already prints tool lifecycle events:

```typescript
else if (event.type === "tool.execution_start") console.log(`\n[tool:start] ${event.data.toolName}`);
else if (event.type === "tool.execution_complete") console.log(`[tool:done] success=${event.data.success}`);
```

Keep those branches so you can see when the model calls the local tool.

### 3. Register and request the tool

In `src/index.ts`, import the tool with the streaming helper:

```typescript
import { accessibilityRuleLookup, streamResponse } from "./workshop.js";
```

Replace the session creation and send call:

```typescript
const session = await client.createSession({
  streaming: true,
  tools: [accessibilityRuleLookup],
  availableTools: ["accessibility_rule_lookup"],
});
try {
  await streamResponse(
    session,
    "Use accessibility_rule_lookup to explain WCAG 4.1.2.",
  );
} finally {
  await session.disconnect();
}
```

`tools` registers the implementation. `availableTools` is the allowlist the model may call.

## Run it

```bash
npm start
```

Look for the tool name and guidance for WCAG 4.1.2:

```text
[tool:start] accessibility_rule_lookup
[tool:done] success=true

WCAG 4.1.2 Name, Role, Value ...
```

<details>
<summary>Troubleshooting this run</summary>

| Symptom | Fix |
|---|---|
| TypeScript cannot resolve `zod` | Run `npm install` in the starter directory. |
| No tool event appears | Keep the tool name in both `tools` and `availableTools`, and keep the explicit instruction in the prompt. |
| The lookup returns no match | Ask about `4.1.2` or `accessible name`, both represented in the catalog. |
| Tool events never print | Confirm `streamResponse` still handles `tool.execution_start` and `tool.execution_complete`. |

</details>

<details>
<summary>Complete Step 3 implementation</summary>

Compare your version with this complete Step 3 implementation.

`src/index.ts`:

```typescript
import { CopilotClient } from "@github/copilot-sdk";
import { accessibilityRuleLookup, streamResponse } from "./workshop.js";

const client = new CopilotClient();
await client.start();
try {
  const session = await client.createSession({
    streaming: true,
    tools: [accessibilityRuleLookup],
    availableTools: ["accessibility_rule_lookup"],
  });
  try {
    await streamResponse(session, "Use accessibility_rule_lookup to explain WCAG 4.1.2.");
  } finally {
    await session.disconnect();
  }
} finally {
  await client.stop();
}
```

The typed tool definition and tool-activity printing live in `src/workshop.ts`.

</details>
:::

:::language python
## Wire up the Python lookup

### 1. Inspect the prebuilt typed tool

Open `workshop.py`. The starter already defines the parameter model and local tool:

```python
class LookupParams(BaseModel):
    query: str = Field(description="The accessibility issue or WCAG criterion to look up.")


@define_tool(name="accessibility_rule_lookup", description="Looks up read-only WCAG guidance maintained by this application.", skip_permission=True)
def accessibility_rule_lookup(params: LookupParams) -> dict[str, object]:
    query = params.query.strip().lower()
    rule = next((item for item in ACCESSIBILITY_RULES if item.criterion.lower() in query or item.title.lower() in query or any(keyword in query for keyword in item.keywords)), None)
    if rule is None:
        return {"criterion": "No exact match", "title": "Criterion not found", "when_it_applies": "The issue is not represented in the workshop catalog.", "recommendation": "Verify the evidence and consult the complete WCAG reference."}
    return rule.__dict__
```

Pydantic describes the model-visible argument while the handler searches
`ACCESSIBILITY_RULES`, which remains application-owned. `skip_permission=True` is intentional
because this tool only returns application-owned read-only data.

### 2. Register and request the tool

In `main.py`, import the tool:

```python
from workshop import accessibility_rule_lookup
```

Replace the session creation and send call. Keep the Step 2 event handler inside the session block:

```python
async with await client.create_session(
    streaming=True,
    tools=[accessibility_rule_lookup],
    available_tools=["accessibility_rule_lookup"],
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
        "Use accessibility_rule_lookup to explain WCAG 4.1.2."
    )
    await done.wait()
    if error is not None:
        raise error
```

`tools` registers the implementation. `available_tools` is the allowlist the model may call.

## Run it

```bash
python main.py
```

The response should use the catalog's WCAG 4.1.2 title and recommendation:

```text
WCAG 4.1.2 Name, Role, Value ...
Associate a visible <label> with the input ...
```

<details>
<summary>Troubleshooting this run</summary>

| Symptom | Fix |
|---|---|
| Python cannot import `pydantic` | Activate the preflight virtual environment and reinstall `requirements.txt`. |
| The tool is not called | Keep it in both `tools` and `available_tools`, and keep the explicit instruction in the prompt. |
| The lookup returns no match | Ask about `4.1.2` or `accessible name`, both represented in the catalog. |
| Import error for `accessibility_rule_lookup` | Confirm `from workshop import accessibility_rule_lookup` is present in `main.py`. |

</details>

<details>
<summary>Complete Step 3 implementation</summary>

Compare your version with this complete Step 3 implementation.

`main.py`:

```python
import asyncio

from copilot import CopilotClient
from copilot.session_events import AssistantMessageData, AssistantMessageDeltaData, SessionErrorData, SessionIdleData

from workshop import accessibility_rule_lookup


async def main() -> None:
    async with CopilotClient() as client:
        async with await client.create_session(
            streaming=True,
            tools=[accessibility_rule_lookup],
            available_tools=["accessibility_rule_lookup"],
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
            await session.send("Use accessibility_rule_lookup to explain WCAG 4.1.2.")
            await done.wait()
            if error is not None:
                raise error


if __name__ == "__main__":
    asyncio.run(main())
```

The typed tool definition lives in `workshop.py`.

</details>
:::

:::language go
## Wire up the Go lookup

### 1. Add the typed lookup

Add `strings` to the imports in `main.go`, then add these declarations before `streamResponse`:

```go
type lookupParams struct {
	Query string `json:"query" jsonschema:"The accessibility issue or WCAG criterion to look up."`
}

func accessibilityRuleLookup(params lookupParams, _ copilot.ToolInvocation) (any, error) {
	query := strings.ToLower(params.Query)
	if strings.Contains(query, "4.1.2") || strings.Contains(query, "accessible name") {
		return map[string]string{
			"criterion":      "4.1.2",
			"title":          "Name, Role, Value",
			"recommendation": "Associate each input with a visible label.",
		}, nil
	}
	return map[string]string{
		"criterion":      "No exact match",
		"recommendation": "Verify the evidence and consult the WCAG reference.",
	}, nil
}
```

### 2. Define and register the tool

At the start of `main`, create the tool:

```go
lookup := copilot.DefineTool(
	"accessibility_rule_lookup",
	"Looks up read-only WCAG guidance maintained by this application.",
	accessibilityRuleLookup,
)
lookup.SkipPermission = true
```

Replace the session configuration and final send:

```go
session, err := client.CreateSession(context.Background(), &copilot.SessionConfig{
	Streaming:      copilot.Bool(true),
	Tools:          []copilot.Tool{lookup},
	AvailableTools: []string{"accessibility_rule_lookup"},
})
if err != nil {
	panic(err)
}
defer session.Disconnect()

if err := streamResponse(
	session,
	"Use accessibility_rule_lookup to explain WCAG 4.1.2.",
); err != nil {
	panic(err)
}
```

`Tools` registers the implementation. `AvailableTools` is the allowlist the model may call.
`SkipPermission = true` is intentional because this tool only returns application-owned read-only
data.

## Run it

```bash
go run .
```

The streamed response should use the lookup result for WCAG 4.1.2:

```text
WCAG 4.1.2 Name, Role, Value ...
Associate each input with a visible label.
```

<details>
<summary>Troubleshooting this run</summary>

| Symptom | Fix |
|---|---|
| `strings` is undefined | Add the standard-library `strings` import. |
| The model cannot see the tool | Keep the tool in `Tools` and its exact name in `AvailableTools`. |
| The lookup returns no match | Ask about `4.1.2` or `accessible name`. |
| Build fails on `DefineTool` | Confirm the handler signature is `(lookupParams, copilot.ToolInvocation) (any, error)`. |

</details>

<details>
<summary>Complete Step 3 implementation</summary>

Compare your version with this complete Step 3 implementation.

`main.go`:

```go
package main

import (
	"context"
	"fmt"
	"strings"

	copilot "github.com/github/copilot-sdk/go"
)

type lookupParams struct {
	Query string `json:"query" jsonschema:"The accessibility issue or WCAG criterion to look up."`
}

func accessibilityRuleLookup(params lookupParams, _ copilot.ToolInvocation) (any, error) {
	query := strings.ToLower(params.Query)
	if strings.Contains(query, "4.1.2") || strings.Contains(query, "accessible name") {
		return map[string]string{
			"criterion":      "4.1.2",
			"title":          "Name, Role, Value",
			"recommendation": "Associate each input with a visible label.",
		}, nil
	}
	return map[string]string{
		"criterion":      "No exact match",
		"recommendation": "Verify the evidence and consult the WCAG reference.",
	}, nil
}

func streamResponse(session *copilot.Session, prompt string) error {
	receivedDelta := false
	unsubscribe := session.On(func(event copilot.SessionEvent) {
		if delta, ok := event.Data.(*copilot.AssistantMessageDeltaData); ok {
			receivedDelta = true
			fmt.Print(delta.DeltaContent)
		}
	})
	defer unsubscribe()
	response, err := session.SendAndWait(context.Background(), copilot.MessageOptions{Prompt: prompt})
	if err == nil && !receivedDelta && response != nil {
		if message, ok := response.Data.(*copilot.AssistantMessageData); ok {
			fmt.Print(message.Content)
		}
	}
	fmt.Println()
	return err
}

func main() {
	lookup := copilot.DefineTool(
		"accessibility_rule_lookup",
		"Looks up read-only WCAG guidance maintained by this application.",
		accessibilityRuleLookup,
	)
	lookup.SkipPermission = true

	client := copilot.NewClient(&copilot.ClientOptions{LogLevel: "error"})
	if err := client.Start(context.Background()); err != nil {
		panic(err)
	}
	defer client.Stop()

	session, err := client.CreateSession(context.Background(), &copilot.SessionConfig{
		Streaming:      copilot.Bool(true),
		Tools:          []copilot.Tool{lookup},
		AvailableTools: []string{"accessibility_rule_lookup"},
	})
	if err != nil {
		panic(err)
	}
	defer session.Disconnect()

	if err := streamResponse(session, "Use accessibility_rule_lookup to explain WCAG 4.1.2."); err != nil {
		panic(err)
	}
}
```

</details>
:::

:::language rust
## Wire up the Rust lookup

### 1. Add the typed handler

Add these imports near the top of `src/main.rs`:

```rust
use std::sync::Arc;

use async_trait::async_trait;
use github_copilot_sdk::tool::{JsonSchema, ToolHandler, schema_for};
use github_copilot_sdk::types::{SessionConfig, Tool, ToolInvocation};
use github_copilot_sdk::{Client, ClientOptions, Error, ToolResult};
use serde::Deserialize;
```

Replace the narrower Step 2 SDK imports, then add the typed handler before `stream_response`:

```rust
#[derive(Deserialize, JsonSchema)]
struct LookupParams {
    /// The accessibility issue or WCAG criterion to look up.
    query: String,
}

struct AccessibilityRuleLookup;

#[async_trait]
impl ToolHandler for AccessibilityRuleLookup {
    async fn call(&self, invocation: ToolInvocation) -> Result<ToolResult, Error> {
        let params: LookupParams = serde_json::from_value(invocation.arguments)?;
        let result = if params.query.to_lowercase().contains("4.1.2") {
            r#"{"criterion":"4.1.2","title":"Name, Role, Value","recommendation":"Associate each input with a visible label."}"#
        } else {
            r#"{"criterion":"No exact match","recommendation":"Verify the evidence and consult the WCAG reference."}"#
        };
        Ok(ToolResult::Text(result.to_owned()))
    }
}
```

### 2. Define and register the tool

At the start of `main`, create the tool and add it to the session configuration:

```rust
let lookup = Tool::new("accessibility_rule_lookup")
    .with_description("Looks up read-only WCAG guidance maintained by this application.")
    .with_parameters(schema_for::<LookupParams>())
    .with_skip_permission(true)
    .with_handler(Arc::new(AccessibilityRuleLookup));

let client = Client::start(ClientOptions::default()).await?;
let mut config = SessionConfig::default();
config.streaming = Some(true);
config.tools = Some(vec![lookup]);
config.available_tools = Some(vec!["accessibility_rule_lookup".to_owned()]);
let session = client.create_session(config).await?;

stream_response!(
    session,
    "Use accessibility_rule_lookup to explain WCAG 4.1.2.".to_owned()
);
```

Keep the Step 2 disconnect and client shutdown after the macro call.
`config.tools` registers the implementation. `config.available_tools` is the allowlist the model may
call. `with_skip_permission(true)` is intentional because this tool only returns application-owned
read-only data.

## Run it

```bash
cargo run
```

The streamed response should use the lookup result for WCAG 4.1.2:

```text
WCAG 4.1.2 Name, Role, Value ...
Associate each input with a visible label.
```

<details>
<summary>Troubleshooting this run</summary>

| Symptom | Fix |
|---|---|
| A trait or derive is unresolved | Keep the `async_trait`, `serde`, schema, and tool imports shown above. |
| The model cannot see the tool | Set both `config.tools` and `config.available_tools`. |
| The lookup returns no match | Ask explicitly about `4.1.2`. |
| Handler type errors | Confirm `ToolHandler::call` returns `Result<ToolResult, Error>`. |

</details>

<details>
<summary>Complete Step 3 implementation</summary>

Compare your version with this complete Step 3 implementation.

`src/main.rs`:

```rust
use std::io::{self, Write};
use std::sync::Arc;

use async_trait::async_trait;
use github_copilot_sdk::tool::{JsonSchema, ToolHandler, schema_for};
use github_copilot_sdk::types::{SessionConfig, Tool, ToolInvocation};
use github_copilot_sdk::{Client, ClientOptions, Error, ToolResult};
use serde::Deserialize;

#[derive(Deserialize, JsonSchema)]
struct LookupParams {
    /// The accessibility issue or WCAG criterion to look up.
    query: String,
}

struct AccessibilityRuleLookup;

#[async_trait]
impl ToolHandler for AccessibilityRuleLookup {
    async fn call(&self, invocation: ToolInvocation) -> Result<ToolResult, Error> {
        let params: LookupParams = serde_json::from_value(invocation.arguments)?;
        let result = if params.query.to_lowercase().contains("4.1.2") {
            r#"{"criterion":"4.1.2","title":"Name, Role, Value","recommendation":"Associate each input with a visible label."}"#
        } else {
            r#"{"criterion":"No exact match","recommendation":"Verify the evidence and consult the WCAG reference."}"#
        };
        Ok(ToolResult::Text(result.to_owned()))
    }
}

macro_rules! stream_response {
    ($session:expr, $prompt:expr) => {{
        let mut events = $session.subscribe();
        let send = $session.send($prompt);
        tokio::pin!(send);
        let mut sent = false;
        let mut idle = false;
        let mut received_delta = false;

        while !sent || !idle {
            tokio::select! {
                result = &mut send, if !sent => {
                    result?;
                    sent = true;
                }
                event = events.recv() => {
                    let event = event?;
                    match event.event_type.as_str() {
                        "assistant.message_delta" => {
                            if let Some(delta) = event.data.get("deltaContent").and_then(|value| value.as_str()) {
                                received_delta = true;
                                print!("{delta}");
                                io::stdout().flush()?;
                            }
                        }
                        "assistant.message" if !received_delta => {
                            if let Some(content) = event.data.get("content").and_then(|value| value.as_str()) {
                                print!("{content}");
                                io::stdout().flush()?;
                            }
                        }
                        "session.error" => {
                            let message = event.data.get("message").and_then(|value| value.as_str())
                                .unwrap_or("Copilot session failed");
                            return Err(std::io::Error::new(std::io::ErrorKind::Other, message.to_owned()).into());
                        }
                        "session.idle" => idle = true,
                        _ => {}
                    }
                }
            }
        }
        println!();
    }};
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let lookup = Tool::new("accessibility_rule_lookup")
        .with_description("Looks up read-only WCAG guidance maintained by this application.")
        .with_parameters(schema_for::<LookupParams>())
        .with_skip_permission(true)
        .with_handler(Arc::new(AccessibilityRuleLookup));

    let client = Client::start(ClientOptions::default()).await?;
    let mut config = SessionConfig::default();
    config.streaming = Some(true);
    config.tools = Some(vec![lookup]);
    config.available_tools = Some(vec!["accessibility_rule_lookup".to_owned()]);
    let session = client.create_session(config).await?;

    stream_response!(
        session,
        "Use accessibility_rule_lookup to explain WCAG 4.1.2.".to_owned()
    );
    session.disconnect().await?;
    client.stop().await?;
    Ok(())
}
```

</details>
:::

:::language java
## Wire up the Java lookup

### 1. Add the typed lookup

Add these imports to `src/main/java/workshop/AccessibilityReport.java`:

```java
import com.github.copilot.rpc.ToolDefinition;
import com.github.copilot.tool.Param;

import java.util.List;
```

Add this method before the class's closing brace:

```java
private static String lookupRule(String query) {
    if (query.toLowerCase(java.util.Locale.ROOT).contains("4.1.2")) {
        return """
                {"criterion":"4.1.2","title":"Name, Role, Value","recommendation":"Associate each input with a visible label."}""";
    }
    return """
            {"criterion":"No exact match","recommendation":"Verify the evidence and consult the WCAG reference."}""";
}
```

### 2. Define and register the tool

At the start of `main`, define the tool and session configuration:

```java
var lookup = ToolDefinition.from(
        "accessibility_rule_lookup",
        "Looks up read-only WCAG guidance maintained by this application.",
        Param.of(String.class, "query",
                "The accessibility issue or WCAG criterion to look up."),
        AccessibilityReport::lookupRule).skipPermission(true);
var config = new SessionConfig()
        .setStreaming(true)
        .setTools(List.of(lookup))
        .setAvailableTools(List.of("accessibility_rule_lookup"))
        .setOnPermissionRequest(PermissionHandler.APPROVE_ALL);
```

Replace session creation and the prompt inside the client block:

```java
var session = client.createSession(config).get();
var response = session.sendAndWait(new MessageOptions()
        .setPrompt("Use accessibility_rule_lookup to explain WCAG 4.1.2."))
        .get();
if (response == null) {
    throw new IllegalStateException("Copilot completed without an assistant message.");
}
System.out.println(response.getData().content());
```

`setTools` registers the implementation. `setAvailableTools` is the allowlist the model may call.
`skipPermission(true)` is intentional because this tool only returns application-owned read-only
data. Keep the Step 1 permission handler until Step 4 replaces it with the scoped Playwright
handler. The Java implementation uses a streaming-enabled session with `sendAndWait`, so it prints the
completed response when the turn finishes.

## Run it

```bash
mvn compile exec:java
```

The response should use the lookup result for WCAG 4.1.2:

```text
WCAG 4.1.2 Name, Role, Value ...
Associate each input with a visible label.
```

<details>
<summary>Troubleshooting this run</summary>

| Symptom | Fix |
|---|---|
| `ToolDefinition` or `Param` is unresolved | Add the two Copilot tool imports shown above. |
| The model cannot see the tool | Keep `setTools` and `setAvailableTools` on the same session configuration. |
| The lookup returns no match | Ask explicitly about `4.1.2`. |
| Method reference fails | Confirm `lookupRule` is `private static` and accepts a single `String`. |

</details>

<details>
<summary>Complete Step 3 implementation</summary>

Compare your version with this complete Step 3 implementation.

`AccessibilityReport.java`:

```java
package workshop;

import com.github.copilot.CopilotClient;
import com.github.copilot.rpc.MessageOptions;
import com.github.copilot.rpc.PermissionHandler;
import com.github.copilot.rpc.SessionConfig;
import com.github.copilot.rpc.ToolDefinition;
import com.github.copilot.tool.Param;

import java.util.List;

public final class AccessibilityReport {
    private AccessibilityReport() {
    }

    public static void main(String[] args) throws Exception {
        var lookup = ToolDefinition.from(
                "accessibility_rule_lookup",
                "Looks up read-only WCAG guidance maintained by this application.",
                Param.of(String.class, "query", "The accessibility issue or WCAG criterion to look up."),
                AccessibilityReport::lookupRule).skipPermission(true);
        var config = new SessionConfig()
                .setStreaming(true)
                .setTools(List.of(lookup))
                .setAvailableTools(List.of("accessibility_rule_lookup"))
                .setOnPermissionRequest(PermissionHandler.APPROVE_ALL);

        try (var client = new CopilotClient()) {
            client.start().get();
            var session = client.createSession(config).get();
            var response = session.sendAndWait(new MessageOptions()
                    .setPrompt("Use accessibility_rule_lookup to explain WCAG 4.1.2."))
                    .get();
            if (response == null) {
                throw new IllegalStateException("Copilot completed without an assistant message.");
            }
            System.out.println(response.getData().content());
        }
    }

    private static String lookupRule(String query) {
        if (query.toLowerCase(java.util.Locale.ROOT).contains("4.1.2")) {
            return """
                    {"criterion":"4.1.2","title":"Name, Role, Value","recommendation":"Associate each input with a visible label."}""";
        }
        return """
                {"criterion":"No exact match","recommendation":"Verify the evidence and consult the WCAG reference."}""";
    }
}
```

</details>
:::

> **You're ready for Playwright when:** the answer uses criterion 4.1.2 from the application catalog.

## Check your understanding

Should calculating an order total from application-owned line items be a local tool or an MCP
server?

<details>
<summary>Check your answer</summary>

Usually a local tool. The application owns the line items and the deterministic calculation, so an
in-process function is easier to test and does not cross a process boundary.

</details>

Continue to [Step 4: Connect an external tool safely](04-mcp-safety.md).
