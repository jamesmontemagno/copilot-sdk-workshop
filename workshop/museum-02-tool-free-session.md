# Create a tool-free session

> **Time:** 10 minutes
> **Goal:** Start a real Copilot session that carries the curator policy and has an empty tool
> allowlist, then watch the curator answer with no capability to look anything up.

Previous: [Define the curator contract](museum-01-curator-role.md)

The system message from lesson 1 guides behavior. It does not remove capability. Three session
settings do the structural work:

| Setting | Value | Why |
|---|---|---|
| Tool allowlist | empty | The session cannot invoke any tool, whatever the prompt says |
| System message mode | `replace` | Removes the coding-agent defaults instead of merging with them |
| Streaming | off | Later lessons validate a complete response, not partial deltas |

This lesson wires the session configuration into the SDK adapter that shipped with the starter and
sends one probe prompt:

```text
Using only facts supplied by the user, write one sentence of exhibit copy about Apollo 11.
If no facts have been supplied, say so instead of inventing any.
```

No facts are supplied yet, so a correctly configured curator has nothing to draw on and says so.
That single reply demonstrates both boundaries at once: the policy holds, and the session has no
tool with which to go find the facts itself.

Authentication is required from this lesson onward. Set `COPILOT_MODEL` to choose a model, or leave
it unset and let the Copilot runtime pick its default.

:::language dotnet
Create `museum-workshop-app/MuseumExhibitService.cs`:

```csharp
using GitHub.Copilot;

namespace MuseumExhibitStudio;

public sealed class MuseumExhibitService
{
    public static SessionConfig CreateSessionConfiguration(string? model = null) => new()
    {
        ClientName = "museum-exhibit-studio",
        Model = string.IsNullOrWhiteSpace(model) ? null : model,
        AvailableTools = [],
        Streaming = false,
        SystemMessage = new SystemMessageConfig
        {
            Mode = SystemMessageMode.Replace,
            Content = CuratorPrompts.SystemMessage
        }
    };
}
```

Replace `museum-workshop-app/Program.cs`. `CopilotCuratorClient` is the adapter already in
`museum-workshop-app/CuratorRuntime.cs`:

```csharp
using MuseumExhibitStudio;

const string ProbePrompt =
    "Using only facts supplied by the user, write one sentence of exhibit copy about " +
    "Apollo 11. If no facts have been supplied, say so instead of inventing any.";

Console.WriteLine("=== Museum Exhibit Studio ===");
Console.WriteLine("Curator policy (durable system message):");
Console.WriteLine(CuratorPrompts.SystemMessage);

Console.WriteLine();
Console.WriteLine("Approved Apollo 11 facts (task data):");
for (var index = 0; index < CuratorPrompts.Apollo11Facts.Count; index++)
{
    Console.WriteLine($"{index + 1}. {CuratorPrompts.Apollo11Facts[index]}");
}

Console.WriteLine();
Console.WriteLine(
    $"Application limits: at most {CuratorPrompts.MaximumFactCount} facts, " +
    $"{CuratorPrompts.MaximumFactLength} characters each.");
Console.WriteLine("Session tools allowed: none (empty allowlist).");

await using var client = new CopilotCuratorClient();
await client.StartAsync();
try
{
    await using var session = await client.CreateSessionAsync(
        MuseumExhibitService.CreateSessionConfiguration(
            Environment.GetEnvironmentVariable("COPILOT_MODEL")));
    var reply = await session.SendAndWaitAsync(ProbePrompt, TimeSpan.FromMinutes(2));
    Console.WriteLine($"\nCurator reply:\n{reply}");
}
finally
{
    await client.StopAsync();
}
```
:::

:::language nodejs
The starter's SDK adapter now moves next to the session configuration it serves. Create
`museum-workshop-app/src/service.ts` with the contents of `museum-workshop-app/src/runtime.ts` plus
the new configuration:

```typescript
import { CopilotClient, type SessionConfig } from "@github/copilot-sdk";
import { systemMessage } from "./prompts.js";

export interface CuratorSession {
  sendAndWait(prompt: string, timeout?: number): Promise<
    { data: { content: string } } | undefined
  >;
  disconnect(): Promise<void>;
}

export interface CuratorClient {
  start(): Promise<void>;
  createSession(configuration: SessionConfig): Promise<CuratorSession>;
  stop(): Promise<unknown>;
}

export function createSessionConfiguration(model?: string): SessionConfig {
  return {
    clientName: "museum-exhibit-studio",
    model: model?.trim() || undefined,
    availableTools: [],
    streaming: false,
    systemMessage: {
      mode: "replace",
      content: systemMessage,
    },
  };
}

export function createCopilotCuratorClient(): CuratorClient {
  return new CopilotClient();
}
```

Delete the now-duplicated adapter so one module owns the SDK boundary:

```bash
rm museum-workshop-app/src/runtime.ts
```

Replace `museum-workshop-app/src/index.ts`:

```typescript
import { apollo11Facts, maximumFactCount, maximumFactLength, systemMessage } from "./prompts.js";
import {
  createCopilotCuratorClient,
  createSessionConfiguration,
  type CuratorSession,
} from "./service.js";

const probePrompt =
  "Using only facts supplied by the user, write one sentence of exhibit copy about " +
  "Apollo 11. If no facts have been supplied, say so instead of inventing any.";

console.log("=== Museum Exhibit Studio ===");
console.log("Curator policy (durable system message):");
console.log(systemMessage);

console.log("\nApproved Apollo 11 facts (task data):");
apollo11Facts.forEach((fact, index) => console.log(`${index + 1}. ${fact}`));

console.log(
  `\nApplication limits: at most ${maximumFactCount} facts, ` +
    `${maximumFactLength} characters each.`,
);
console.log("Session tools allowed: none (empty allowlist).");

const client = createCopilotCuratorClient();
let session: CuratorSession | undefined;
await client.start();
try {
  session = await client.createSession(
    createSessionConfiguration(process.env.COPILOT_MODEL),
  );
  const response = await session.sendAndWait(probePrompt, 120_000);
  console.log(`\nCurator reply:\n${response?.data.content ?? ""}`);
} finally {
  await session?.disconnect();
  await client.stop();
}
```
:::

:::language python
The starter's SDK protocols now move next to the session configuration they serve. Create
`museum-workshop-app/museum_exhibit_service.py`:

```python
from __future__ import annotations

from typing import Any

from curator_prompts import SYSTEM_MESSAGE


def create_session_configuration(model: str | None = None) -> dict[str, Any]:
    return {
        "client_name": "museum-exhibit-studio",
        "model": model.strip() if model and model.strip() else None,
        "available_tools": [],
        "streaming": False,
        "system_message": {"mode": "replace", "content": SYSTEM_MESSAGE},
    }


class MuseumExhibitService:
    def __init__(self, client: Any) -> None:
        self._client = client
```

Delete the now-duplicated adapter so one module owns the SDK boundary:

```bash
rm museum-workshop-app/curator_runtime.py
```

Replace `museum-workshop-app/main.py`:

```python
from __future__ import annotations

import asyncio
import os

from copilot import CopilotClient

from curator_prompts import (
    APOLLO_11_FACTS,
    MAXIMUM_FACT_COUNT,
    MAXIMUM_FACT_LENGTH,
    SYSTEM_MESSAGE,
)
from museum_exhibit_service import create_session_configuration

PROBE_PROMPT = (
    "Using only facts supplied by the user, write one sentence of exhibit copy about "
    "Apollo 11. If no facts have been supplied, say so instead of inventing any."
)


async def main() -> None:
    print("=== Museum Exhibit Studio ===")
    print("Curator policy (durable system message):")
    print(SYSTEM_MESSAGE)

    print("\nApproved Apollo 11 facts (task data):")
    for index, fact in enumerate(APOLLO_11_FACTS, start=1):
        print(f"{index}. {fact}")

    print(
        f"\nApplication limits: at most {MAXIMUM_FACT_COUNT} facts, "
        f"{MAXIMUM_FACT_LENGTH} characters each."
    )
    print("Session tools allowed: none (empty allowlist).")

    client = CopilotClient()
    session = None
    await client.start()
    try:
        session = await client.create_session(
            **create_session_configuration(os.getenv("COPILOT_MODEL"))
        )
        response = await session.send_and_wait(PROBE_PROMPT, timeout=120.0)
        print(f"\nCurator reply:\n{response.data.content}")
    finally:
        if session is not None:
            await session.disconnect()
        await client.stop()


if __name__ == "__main__":
    asyncio.run(main())
```
:::

:::language go
The starter's SDK adapter now moves next to the session configuration it serves. Create
`museum-workshop-app/service.go`:

```go
package main

import (
	"context"
	"strings"

	copilot "github.com/github/copilot-sdk/go"
)

type curatorSession interface {
	SendAndWait(context.Context, string) (string, error)
	Disconnect() error
}

type curatorClient interface {
	Start(context.Context) error
	CreateSession(context.Context, *copilot.SessionConfig) (curatorSession, error)
	Stop() error
}

func createSessionConfiguration(model string) *copilot.SessionConfig {
	return &copilot.SessionConfig{
		ClientName:     "museum-exhibit-studio",
		Model:          strings.TrimSpace(model),
		AvailableTools: []string{},
		Streaming:      copilot.Bool(false),
		SystemMessage: &copilot.SystemMessageConfig{
			Mode:    "replace",
			Content: curatorSystemMessage,
		},
	}
}

type copilotCuratorClient struct {
	client *copilot.Client
}

func newCopilotCuratorClient() *copilotCuratorClient {
	return &copilotCuratorClient{
		client: copilot.NewClient(&copilot.ClientOptions{LogLevel: "error"}),
	}
}

func (client *copilotCuratorClient) Start(ctx context.Context) error {
	return client.client.Start(ctx)
}

func (client *copilotCuratorClient) CreateSession(
	ctx context.Context,
	config *copilot.SessionConfig,
) (curatorSession, error) {
	session, err := client.client.CreateSession(ctx, config)
	if err != nil {
		return nil, err
	}
	return copilotCuratorSession{session: session}, nil
}

func (client *copilotCuratorClient) Stop() error {
	return client.client.Stop()
}

type copilotCuratorSession struct {
	session *copilot.Session
}

func (session copilotCuratorSession) SendAndWait(
	ctx context.Context,
	prompt string,
) (string, error) {
	response, err := session.session.SendAndWait(ctx, copilot.MessageOptions{Prompt: prompt})
	if err != nil || response == nil {
		return "", err
	}
	message, ok := response.Data.(*copilot.AssistantMessageData)
	if !ok {
		return "", nil
	}
	return message.Content, nil
}

func (session copilotCuratorSession) Disconnect() error {
	return session.session.Disconnect()
}
```

Delete the duplicated adapter. Two files declaring the same package-level types will not compile:

```bash
rm museum-workshop-app/curator_runtime.go
```

Replace `museum-workshop-app/main.go`:

```go
package main

import (
	"context"
	"errors"
	"fmt"
	"os"
	"time"
)

const probePrompt = "Using only facts supplied by the user, write one sentence of exhibit copy " +
	"about Apollo 11. If no facts have been supplied, say so instead of inventing any."

func main() {
	fmt.Println("=== Museum Exhibit Studio ===")
	fmt.Println("Curator policy (durable system message):")
	fmt.Println(curatorSystemMessage)

	fmt.Println("\nApproved Apollo 11 facts (task data):")
	for index, fact := range apollo11Facts {
		fmt.Printf("%d. %s\n", index+1, fact)
	}

	fmt.Printf("\nApplication limits: at most %d facts, %d characters each.\n",
		maximumFactCount, maximumFactLength)
	fmt.Println("Session tools allowed: none (empty allowlist).")

	if err := probeCurator(); err != nil {
		fmt.Fprintln(os.Stderr, "Could not reach the curator:", err)
		os.Exit(1)
	}
}

func probeCurator() (err error) {
	ctx := context.Background()
	client := newCopilotCuratorClient()
	if err = client.Start(ctx); err != nil {
		return err
	}
	defer func() { err = errors.Join(err, client.Stop()) }()

	session, err := client.CreateSession(ctx, createSessionConfiguration(os.Getenv("COPILOT_MODEL")))
	if err != nil {
		return err
	}
	defer func() { err = errors.Join(err, session.Disconnect()) }()

	replyContext, cancel := context.WithTimeout(ctx, 2*time.Minute)
	defer cancel()
	reply, err := session.SendAndWait(replyContext, probePrompt)
	if err != nil {
		return err
	}
	fmt.Printf("\nCurator reply:\n%s\n", reply)
	return nil
}
```
:::

:::language rust
The probe runs on an async runtime, so add Tokio to the `[dependencies]` section of
`museum-workshop-app/Cargo.toml`. The completed reference pins exact versions; these requirements
match the versions already recorded in your copied `Cargo.lock`:

```toml
[dependencies]
async-trait = "=0.1.91"
github-copilot-sdk = { version = "=1.0.11", features = ["derive"] }
tokio = { version = "1", features = ["macros", "rt-multi-thread"] }
```

In `museum-workshop-app/src/lib.rs`, extend the existing SDK type import with `SystemMessageConfig`:

```rust
use github_copilot_sdk::types::{MessageOptions, SessionConfig, SystemMessageConfig};
```

Then add the session configuration to `museum-workshop-app/src/lib.rs`, directly below the
`SYSTEM_MESSAGE` constant:

```rust
pub fn create_session_configuration(model: Option<&str>) -> SessionConfig {
    let mut config = SessionConfig::default();
    config.client_name = Some("museum-exhibit-studio".to_owned());
    config.model = model
        .map(str::trim)
        .filter(|model| !model.is_empty())
        .map(str::to_owned);
    config.available_tools = Some(Vec::new());
    config.streaming = Some(false);
    config.system_message = Some(
        SystemMessageConfig::new()
            .with_mode("replace")
            .with_content(SYSTEM_MESSAGE),
    );
    config
}
```

Replace `museum-workshop-app/src/main.rs`. `CopilotCuratorClient` is the adapter already in
`museum-workshop-app/src/lib.rs`:

```rust
use std::time::Duration;

use museum_exhibit_studio::{
    APOLLO_11_FACTS, CopilotCuratorClient, CuratorClient, CuratorSession, MAXIMUM_FACT_COUNT,
    MAXIMUM_FACT_LENGTH, RuntimeError, SYSTEM_MESSAGE, create_session_configuration,
};

const PROBE_PROMPT: &str = "Using only facts supplied by the user, write one sentence of exhibit \
copy about Apollo 11. If no facts have been supplied, say so instead of inventing any.";

fn print_contract() {
    println!("=== Museum Exhibit Studio ===");
    println!("Curator policy (durable system message):");
    println!("{SYSTEM_MESSAGE}");

    println!("\nApproved Apollo 11 facts (task data):");
    for (index, fact) in APOLLO_11_FACTS.iter().enumerate() {
        println!("{}. {fact}", index + 1);
    }

    println!(
        "\nApplication limits: at most {MAXIMUM_FACT_COUNT} facts, \
         {MAXIMUM_FACT_LENGTH} characters each."
    );
    println!("Session tools allowed: none (empty allowlist).");
}

async fn probe_curator() -> Result<(), RuntimeError> {
    let mut client = CopilotCuratorClient::new();
    client.start().await?;
    let mut session = client
        .create_session(create_session_configuration(
            std::env::var("COPILOT_MODEL").ok().as_deref(),
        ))
        .await?;
    let reply = session
        .send_and_wait(PROBE_PROMPT.to_owned(), Duration::from_secs(120))
        .await;
    session.disconnect().await?;
    client.stop().await?;
    println!("\nCurator reply:\n{}", reply?.unwrap_or_default());
    Ok(())
}

#[tokio::main]
async fn main() {
    print_contract();
    if let Err(error) = probe_curator().await {
        eprintln!("Could not reach the curator: {error}");
        std::process::exit(1);
    }
}
```
:::

:::language java
Create `museum-workshop-app/src/main/java/workshop/MuseumExhibitService.java`. The reject-all
permission handler is a second lock on the same door: even if a tool reached this session, every
request is denied:

```java
package workshop;

import com.github.copilot.SystemMessageMode;
import com.github.copilot.rpc.PermissionRequestResult;
import com.github.copilot.rpc.SessionConfig;
import com.github.copilot.rpc.SystemMessageConfig;

import java.util.List;
import java.util.concurrent.CompletableFuture;

public final class MuseumExhibitService {
    private MuseumExhibitService() {
    }

    public static SessionConfig createSessionConfiguration(String model) {
        SessionConfig configuration = new SessionConfig()
                .setClientName("museum-exhibit-studio")
                .setAvailableTools(List.of())
                .setStreaming(false)
                .setOnPermissionRequest((request, invocation) ->
                        CompletableFuture.completedFuture(
                                PermissionRequestResult.reject(
                                        "This session does not permit tools.")))
                .setSystemMessage(new SystemMessageConfig()
                        .setMode(SystemMessageMode.REPLACE)
                        .setContent(CuratorPrompts.SYSTEM_MESSAGE));
        if (model != null && !model.isBlank()) {
            configuration.setModel(model);
        }
        return configuration;
    }
}
```

Replace `museum-workshop-app/src/main/java/workshop/MuseumExhibitStudio.java`.
`CopilotCuratorClient` is the adapter already in
`museum-workshop-app/src/main/java/workshop/CuratorRuntime.java`:

```java
package workshop;

public final class MuseumExhibitStudio {
    private static final String PROBE_PROMPT =
            "Using only facts supplied by the user, write one sentence of exhibit copy about "
                    + "Apollo 11. If no facts have been supplied, say so instead of inventing any.";

    private MuseumExhibitStudio() {
    }

    public static void main(String[] args) throws Exception {
        System.out.println("=== Museum Exhibit Studio ===");
        System.out.println("Curator policy (durable system message):");
        System.out.println(CuratorPrompts.SYSTEM_MESSAGE);

        System.out.println("Approved Apollo 11 facts (task data):");
        for (int index = 0; index < CuratorPrompts.APOLLO_11_FACTS.size(); index++) {
            System.out.printf("%d. %s%n", index + 1, CuratorPrompts.APOLLO_11_FACTS.get(index));
        }

        System.out.printf(
                "%nApplication limits: at most %d facts, %d characters each.%n",
                CuratorPrompts.MAXIMUM_FACT_COUNT,
                CuratorPrompts.MAXIMUM_FACT_LENGTH);
        System.out.println("Session tools allowed: none (empty allowlist).");

        try (CuratorClient client = new CopilotCuratorClient()) {
            client.start();
            CuratorSession session = null;
            try {
                session = client.createSession(
                        MuseumExhibitService.createSessionConfiguration(
                                System.getenv("COPILOT_MODEL")));
                String reply = session.sendAndWait(PROBE_PROMPT, 120_000L);
                System.out.printf("%nCurator reply:%n%s%n", reply);
            } finally {
                if (session != null) {
                    session.disconnect();
                }
                client.stop();
            }
        }
    }
}
```
:::

## Run it

Build, then run. The run starts a real Copilot process and needs an authenticated GitHub Copilot
CLI.

:::language dotnet
```bash
dotnet build museum-workshop-app
dotnet run --project museum-workshop-app
```
:::
:::language nodejs
```bash
npm --prefix museum-workshop-app run build
npm --prefix museum-workshop-app start
```
:::
:::language python
```bash
museum-workshop-app/.venv/bin/python -m py_compile museum-workshop-app/*.py
museum-workshop-app/.venv/bin/python museum-workshop-app/main.py
```
:::
:::language go
```bash
go -C museum-workshop-app build -mod=readonly ./...
go -C museum-workshop-app run .
```
:::
:::language rust
```bash
cargo check --manifest-path museum-workshop-app/Cargo.toml
cargo run --manifest-path museum-workshop-app/Cargo.toml
```
:::
:::language java
```bash
mvn -f museum-workshop-app/pom.xml compile
mvn -f museum-workshop-app/pom.xml compile exec:java
```
:::

After the lesson 1 output, the run adds the allowlist line and a curator reply. Wording varies
between models and runs; the shape does not:

```text
Application limits: at most 20 facts, 500 characters each.
Session tools allowed: none (empty allowlist).

Curator reply:
No approved facts have been supplied yet, so there is nothing I can write about Apollo 11
without inventing details.
```

That answer is the point of the lesson. The curator did not summarize what it remembers about
Apollo 11, and it had no tool available to go and find anything. If the reply instead recites moon
landing trivia, the system message is not reaching the session: confirm the mode is `replace` and
that the configuration function is the one the session was created with.

Troubleshooting this run:

- An authentication error means the GitHub Copilot CLI is not signed in. Sign in, then rerun.
- A missing SDK symbol means the copied manifest no longer pins 1.0.11. Rerun the preflight restore
  command for your language.
- A hang means the model is still working. The run has a two-minute ceiling; lesson 5 moves that
  ceiling into the application where it can be enforced and reported.

## Check your understanding

1. Why is an empty tool allowlist a stronger control than the sentence in the system message that
   tells the curator not to use tools?
2. What would remain in the session if the system message used append mode instead of `replace`?
3. Streaming is off. Which later lesson depends on that, and why?

Continue to [Ground the exhibit in approved facts](museum-03-approved-facts.md).
