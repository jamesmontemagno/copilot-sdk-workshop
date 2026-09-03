# Step 1: Your first curator session

> **Time:** 10 minutes

## What you'll build

Real museum copy, in your terminal, in about ten minutes. You connect to the Copilot runtime, open
one conversation, send a single prompt, and print what comes back.

No system message. No facts catalog. No tools. No interfaces. Nothing to implement against — you
call the SDK directly, and the pre-built curator helpers stay untouched until Step 2 needs them.

## Meet the client and the session

The **Copilot runtime** receives prompts, calls models, and manages tools. The **client** connects
your application to that runtime. A **session** is one continuing conversation: it holds the
messages and tool results that make up context.

Keep one client alive for a piece of work, then create a session for each independent conversation.
Right now the application is simply `client -> session -> printed response`.

## Write the session

:::language dotnet
Open `Program.cs` and **replace the entire file**:

```csharp
using GitHub.Copilot;

Console.WriteLine("=== Museum Exhibit Studio ===");
Console.WriteLine();

await using var client = new CopilotClient();
await client.StartAsync();

await using var session = await client.CreateSessionAsync(new SessionConfig
{
    ClientName = "museum-exhibit-studio"
});

var response = await session.SendAndWaitAsync(
    "Write two sentences of museum wall text about the Apollo 11 Moon landing.");

if (response is null)
{
    throw new InvalidOperationException("The curator returned no content.");
}

Console.WriteLine(response.Data.Content);

await client.StopAsync();
```

`SendAndWaitAsync` blocks until the session goes idle, so you get the finished answer in one call.
`await using` disposes the session and the client on the way out.

The pre-built helpers you start calling in Step 2 live in `Helpers/CuratorFacts.cs`,
`Helpers/CuratorStreamer.cs`, `Helpers/CuratorValidation.cs`, `Helpers/CuratorSafety.cs`, and
`Helpers/CuratorTerminal.cs`. You never edit those files — you read them.
:::

:::language nodejs
Open `src/index.ts` and **replace the entire file**:

```typescript
import { CopilotClient } from "@github/copilot-sdk";

async function main(): Promise<void> {
  console.log("=== Museum Exhibit Studio ===");
  console.log();

  const client = new CopilotClient();
  await client.start();
  const session = await client.createSession({ clientName: "museum-exhibit-studio" });

  const response = await session.sendAndWait({
    prompt: "Write two sentences of museum wall text about the Apollo 11 Moon landing.",
  });
  console.log(response?.data && "content" in response.data ? response.data.content : response);

  await session.disconnect();
  await client.stop();
}

void main();
```

`sendAndWait` blocks until the session goes idle, so you get the finished answer in one call.

`src/curator.ts` beside this file is the pre-built helper module you start calling in Step 2. You
never edit it — you read it.
:::

:::language python
Open `main.py` and **replace the entire file**:

```python
import asyncio

from copilot import CopilotClient
from copilot.session_events import AssistantMessageData, SessionErrorData, SessionIdleData


async def main() -> None:
    print("=== Museum Exhibit Studio ===")
    print()

    async with CopilotClient() as client:
        async with await client.create_session(client_name="museum-exhibit-studio") as session:
            done = asyncio.Event()
            error: RuntimeError | None = None

            def on_event(event) -> None:
                nonlocal error
                match event.data:
                    case AssistantMessageData(content=content):
                        print(content)
                    case SessionErrorData(message=message):
                        error = RuntimeError(message)
                        done.set()
                    case SessionIdleData():
                        done.set()

            session.on(on_event)
            await session.send(
                "Write two sentences of museum wall text about the Apollo 11 Moon landing."
            )
            await done.wait()
            if error is not None:
                raise error


if __name__ == "__main__":
    asyncio.run(main())
```

Python listens for session events rather than calling one blocking helper. Print the assistant
message, treat a session error as a failure, and wait for idle before exiting. Step 2 replaces this
whole listener with one helper call.

`curator.py` beside this file is the pre-built helper module that owns that replacement. You never
edit it — you read it.
:::

:::language go
Open `main.go` and **replace the entire file**:

```go
package main

import (
	"context"
	"fmt"

	copilot "github.com/github/copilot-sdk/go"
)

func main() {
	fmt.Println("=== Museum Exhibit Studio ===")
	fmt.Println()

	ctx := context.Background()
	client := copilot.NewClient(&copilot.ClientOptions{LogLevel: "error"})
	if err := client.Start(ctx); err != nil {
		panic(err)
	}
	defer func() { _ = client.Stop() }()

	session, err := client.CreateSession(ctx, &copilot.SessionConfig{
		ClientName: "museum-exhibit-studio",
	})
	if err != nil {
		panic(err)
	}
	defer func() { _ = session.Disconnect() }()

	response, err := session.SendAndWait(ctx, copilot.MessageOptions{
		Prompt: "Write two sentences of museum wall text about the Apollo 11 Moon landing.",
	})
	if err != nil {
		panic(err)
	}
	if response == nil {
		panic("The curator returned no content.")
	}
	if message, ok := response.Data.(*copilot.AssistantMessageData); ok {
		fmt.Println(message.Content)
	}
}
```

`curator.go` is already in this same `main` package, so its helpers are in scope the moment you
need them. `SendAndWait` blocks until the session goes idle.
:::

:::language rust
Open `src/main.rs` and **replace the entire file**:

```rust
use github_copilot_sdk::types::{MessageOptions, SessionConfig};
use github_copilot_sdk::{Client, ClientOptions};

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    println!("=== Museum Exhibit Studio ===");
    println!();

    let client = Client::start(ClientOptions::default()).await?;
    let mut config = SessionConfig::default();
    config.client_name = Some("museum-exhibit-studio".to_owned());
    let session = client.create_session(config).await?;

    let response = session
        .send_and_wait(MessageOptions::new(
            "Write two sentences of museum wall text about the Apollo 11 Moon landing.",
        ))
        .await?;

    if let Some(message) = response {
        if let Some(content) = message.data.get("content").and_then(|value| value.as_str()) {
            println!("{content}");
        }
    }

    session.disconnect().await?;
    client.stop().await?;
    Ok(())
}
```

`src/lib.rs` is the `museum_exhibit_studio` library crate that ships the pre-built helpers. You do
not need it yet, and you never edit it.
:::

:::language java
Open `src/main/java/workshop/MuseumExhibitStudio.java` and **replace the entire file**:

```java
package workshop;

import com.github.copilot.CopilotClient;
import com.github.copilot.rpc.MessageOptions;
import com.github.copilot.rpc.SessionConfig;

public final class MuseumExhibitStudio {
    private MuseumExhibitStudio() {
    }

    public static void main(String[] args) throws Exception {
        System.out.println("=== Museum Exhibit Studio ===");
        System.out.println();

        try (var client = new CopilotClient()) {
            client.start().get();
            var session = client.createSession(
                    new SessionConfig().setClientName("museum-exhibit-studio")).get();
            try {
                var response = session.sendAndWait(new MessageOptions().setPrompt(
                        "Write two sentences of museum wall text about the Apollo 11 Moon landing.")).get();
                if (response == null) {
                    throw new IllegalStateException("The curator returned no content.");
                }
                System.out.println(response.getData().content());
            } finally {
                session.close();
                client.stop().get();
            }
        }
    }
}
```

`sendAndWait` blocks until the session goes idle. The try-with-resources block closes the client
when `main` exits.

The pre-built helpers you start calling in Step 2 sit beside your file in
`src/main/java/workshop/`: `CuratorFacts.java`, `CuratorStreamer.java`, `CuratorValidation.java`,
`CuratorSafety.java`, and `CuratorTerminal.java`. You never edit those files — you read them.
:::

## Run it

:::language dotnet
```bash
dotnet run
```
:::
:::language nodejs
```bash
npm start
```
:::
:::language python
```bash
.venv/bin/python main.py
```
:::
:::language go
```bash
go run .
```
:::
:::language rust
```bash
cargo run
```
:::
:::language java
```bash
mvn compile exec:java
```
:::

Your exact wording will vary, but the output has this shape:

```text
=== Museum Exhibit Studio ===

The Apollo 11 mission carried three astronauts toward the Moon in July 1969. Days later,
two of them stepped onto its surface while the world listened.
```

Two sentences of museum-ish prose arrive after a short pause. Nothing streams yet, no tone is
enforced yet, and nothing stops the model from reaching past the subject you asked about. Those are
the next three steps.

## Check your understanding

- What does the session hold that the client does not?
- The response arrived all at once after a pause. Which part of the current code causes that?
- Nothing in this step restricts what the model may claim about Apollo 11. What is the only thing
  keeping the answer roughly on topic right now?

Continue to [Stream the curator](museum-02-stream-the-curator.md).
