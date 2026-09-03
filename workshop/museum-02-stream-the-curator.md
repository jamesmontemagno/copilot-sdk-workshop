# Step 2: Stream the curator

> **Time:** 10 minutes

## What you'll build

The same prompt, but the answer appears word by word instead of arriving after a silent pause.

You will not write an event loop. The starter already ships a streaming printer in the pre-built
curator helpers: it subscribes to session events, writes each delta to standard output, reports tool
activity, fails on session errors, enforces a timeout, unsubscribes on every path, and returns the
full text it accumulated. Your job is to turn streaming on and call it.

## Why streaming matters for a curator

Exhibit copy is prose a human has to read and judge. Watching it arrive tells you immediately
whether the tone is right, whether the model is padding, and whether it is drifting off the subject
— long before the run finishes. Streaming also gives you a place to notice tool calls, which
matters from Step 4 onward, when the curator has to call the application's fact tool before it can
write anything.

The helper returns the whole response as a string, so from here on you always have the finished
text to inspect after the stream ends.

## Swap the blocking call for the streamer

:::language dotnet
Replace the entire contents of `Program.cs`:

```csharp
using GitHub.Copilot;
using MuseumExhibitStudio.Helpers;

Console.WriteLine("=== Museum Exhibit Studio ===");
Console.WriteLine();

await using var client = new CopilotClient();
await client.StartAsync();

await using var session = await client.CreateSessionAsync(new SessionConfig
{
    ClientName = "museum-exhibit-studio",
    Streaming = true
});

await CuratorStreamer.StreamExhibitAsync(
    session,
    "Write two sentences of museum wall text about the Apollo 11 Moon landing.");

await client.StopAsync();
```

Two changes: `Streaming = true` on the session config, and `CuratorStreamer.StreamExhibitAsync`
in place of `SendAndWaitAsync`. The helper lives in `Helpers/CuratorStreamer.cs` and you never
edit it.
:::

:::language nodejs
Replace the entire contents of `src/index.ts`:

```typescript
import { CopilotClient } from "@github/copilot-sdk";
import { streamExhibit } from "./curator.js";

async function main(): Promise<void> {
  console.log("=== Museum Exhibit Studio ===");
  console.log();

  const client = new CopilotClient();
  await client.start();
  const session = await client.createSession({
    clientName: "museum-exhibit-studio",
    streaming: true,
  });

  await streamExhibit(
    session,
    "Write two sentences of museum wall text about the Apollo 11 Moon landing.",
  );

  await session.disconnect();
  await client.stop();
}

void main();
```

Two changes: `streaming: true` on the session config, and `streamExhibit` in place of
`sendAndWait`. The helper lives in `src/curator.ts` and you never edit it.
:::

:::language python
Replace the entire contents of `main.py`:

```python
import asyncio

from copilot import CopilotClient

from curator import stream_exhibit


async def main() -> None:
    print("=== Museum Exhibit Studio ===")
    print()

    async with CopilotClient() as client:
        async with await client.create_session(
            client_name="museum-exhibit-studio",
            streaming=True,
        ) as session:
            await stream_exhibit(
                session,
                "Write two sentences of museum wall text about the Apollo 11 Moon landing.",
            )


if __name__ == "__main__":
    asyncio.run(main())
```

The whole event listener from Step 1 collapses into one call. `stream_exhibit` lives in
`curator.py`, already does the matching on `AssistantMessageDeltaData`, `SessionErrorData`, and
`SessionIdleData`, and you never edit it.
:::

:::language go
Replace the entire contents of `main.go`:

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
		Streaming:  copilot.Bool(true),
	})
	if err != nil {
		panic(err)
	}
	defer func() { _ = session.Disconnect() }()

	if _, err := StreamExhibit(
		session,
		"Write two sentences of museum wall text about the Apollo 11 Moon landing.",
		GenerationTimeout,
	); err != nil {
		panic(err)
	}
}
```

Two changes: `Streaming: copilot.Bool(true)` on the session config, and `StreamExhibit` in place of
`SendAndWait`. `StreamExhibit` and `GenerationTimeout` come from `curator.go` in the same package,
and you never edit that file.
:::

:::language rust
Replace the entire contents of `src/main.rs`:

```rust
use github_copilot_sdk::types::SessionConfig;
use github_copilot_sdk::{Client, ClientOptions};
use museum_exhibit_studio::{GENERATION_TIMEOUT, stream_exhibit};

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    println!("=== Museum Exhibit Studio ===");
    println!();

    let client = Client::start(ClientOptions::default()).await?;
    let mut config = SessionConfig::default();
    config.client_name = Some("museum-exhibit-studio".to_owned());
    config.streaming = Some(true);
    let session = client.create_session(config).await?;

    stream_exhibit(
        &session,
        "Write two sentences of museum wall text about the Apollo 11 Moon landing.",
        GENERATION_TIMEOUT,
    )
    .await?;

    session.disconnect().await?;
    client.stop().await?;
    Ok(())
}
```

Two changes: `config.streaming = Some(true)`, and `stream_exhibit` in place of `send_and_wait`.
Both `stream_exhibit` and `GENERATION_TIMEOUT` come from the `museum_exhibit_studio` crate in
`src/lib.rs`, and you never edit it.
:::

:::language java
Replace the entire contents of `src/main/java/workshop/MuseumExhibitStudio.java`:

```java
package workshop;

import com.github.copilot.CopilotClient;
import com.github.copilot.rpc.SessionConfig;

public final class MuseumExhibitStudio {
    private MuseumExhibitStudio() {
    }

    public static void main(String[] args) throws Exception {
        System.out.println("=== Museum Exhibit Studio ===");
        System.out.println();

        try (var client = new CopilotClient()) {
            client.start().get();
            var session = client.createSession(new SessionConfig()
                    .setClientName("museum-exhibit-studio")
                    .setStreaming(true)).get();
            try {
                CuratorStreamer.streamExhibit(session,
                        "Write two sentences of museum wall text about the Apollo 11 Moon landing.");
            } finally {
                session.close();
                client.stop().get();
            }
        }
    }
}
```

Two changes: `setStreaming(true)` on the session config, and `CuratorStreamer.streamExhibit` in
place of `sendAndWait`. The helper lives in `CuratorStreamer.java` beside your file, and you never
edit it.
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

The same kind of answer appears, but this time you watch it being written:

```text
=== Museum Exhibit Studio ===

In July 1969, three astronauts left Earth aboard Apollo 11... 
```

The text grows in place instead of appearing all at once, and the program exits shortly after the
last word. If you see nothing until the very end, the session is not streaming — check that you set
the streaming flag on the session config.

## Check your understanding

- Streaming is switched on in two places conceptually: the session config and the code that reads
  events. Which one did you write, and which one did the helper already own?
- The helper returns the full response text even though it also printed it. Why will that return
  value matter in Step 6?
- If the model never becomes idle, what stops your program from waiting forever?

Continue to [Give the curator a voice](museum-03-curator-voice.md).
