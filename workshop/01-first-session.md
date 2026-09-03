# Step 1: Create your first Copilot session

> **Time:** 10 minutes

## What you'll build

You'll connect the console application to the Copilot runtime, create a conversation, send a
prompt, and print the response.

:::language dotnet
## Meet the GitHub Copilot SDK and runtime

The **GitHub Copilot SDK** is the .NET API your application uses to run Copilot as an agent. The
[**Copilot runtime**](https://github.com/github/copilot-sdk/blob/main/docs/features/agent-loop.md)
receives prompts, calls models, and manages tools. `CopilotClient` connects your C# code to that
runtime.

A `CopilotSession` represents one continuing conversation. It holds the messages and tool results
that make up the conversation's context. Keep one client alive for the application, then create a
session for each independent conversation.

## Why clients and sessions stay separate

Keeping those responsibilities separate lets the runtime connection outlive any one conversation.
It also gives you a small working example before streaming and tools enter the picture.

At this point, the console app is simply `CopilotClient -> CopilotSession -> model response`.
:::

:::language nodejs
## Meet the GitHub Copilot SDK and runtime

The **GitHub Copilot SDK** is the Node.js API your application uses to run Copilot as an agent. The
[**Copilot runtime**](https://github.com/github/copilot-sdk/blob/main/docs/features/agent-loop.md)
receives prompts, calls models, and manages tools. `CopilotClient` connects your TypeScript code to
that runtime.

A session from `createSession` represents one continuing conversation. It holds the messages and
tool results that make up the conversation's context. Keep one client alive for the application,
then create a session for each independent conversation.

## Why clients and sessions stay separate

Keeping those responsibilities separate lets the runtime connection outlive any one conversation.
It also gives you a small working example before streaming and tools enter the picture.

At this point, the console app is simply `CopilotClient -> session -> model response`.
:::

:::language python
## Meet the GitHub Copilot SDK and runtime

The **GitHub Copilot SDK** is the Python API your application uses to run Copilot as an agent. The
[**Copilot runtime**](https://github.com/github/copilot-sdk/blob/main/docs/features/agent-loop.md)
receives prompts, calls models, and manages tools. `CopilotClient` connects your Python code to
that runtime.

A session from `create_session` represents one continuing conversation. It holds the messages and
tool results that make up the conversation's context. Keep one client alive for the application,
then create a session for each independent conversation.

## Why clients and sessions stay separate

Keeping those responsibilities separate lets the runtime connection outlive any one conversation.
It also gives you a small working example before streaming and tools enter the picture.

At this point, the console app is simply `CopilotClient -> session -> model response`.
:::

:::language go
## Meet the GitHub Copilot SDK and runtime

The **GitHub Copilot SDK** is the Go API your application uses to run Copilot as an agent. The
[**Copilot runtime**](https://github.com/github/copilot-sdk/blob/main/docs/features/agent-loop.md)
receives prompts, calls models, and manages tools. `copilot.NewClient` connects your Go code to
that runtime.

A session from `CreateSession` represents one continuing conversation. It holds the messages and
tool results that make up the conversation's context. Keep one client alive for the application,
then create a session for each independent conversation.

## Why clients and sessions stay separate

Keeping those responsibilities separate lets the runtime connection outlive any one conversation.
It also gives you a small working example before streaming and tools enter the picture.

At this point, the console app is simply `Client -> Session -> model response`.
:::

:::language rust
## Meet the GitHub Copilot SDK and runtime

The **GitHub Copilot SDK** is the Rust API your application uses to run Copilot as an agent. The
[**Copilot runtime**](https://github.com/github/copilot-sdk/blob/main/docs/features/agent-loop.md)
receives prompts, calls models, and manages tools. `Client` connects your Rust code to that
runtime.

A session from `create_session` represents one continuing conversation. It holds the messages and
tool results that make up the conversation's context. Keep one client alive for the application,
then create a session for each independent conversation.

## Why clients and sessions stay separate

Keeping those responsibilities separate lets the runtime connection outlive any one conversation.
It also gives you a small working example before streaming and tools enter the picture.

At this point, the console app is simply `Client -> session -> model response`.
:::

:::language java
## Meet the GitHub Copilot SDK and runtime

The **GitHub Copilot SDK** is the Java API your application uses to run Copilot as an agent. The
[**Copilot runtime**](https://github.com/github/copilot-sdk/blob/main/docs/features/agent-loop.md)
receives prompts, calls models, and manages tools. `CopilotClient` connects your Java code to that
runtime.

A session from `createSession` represents one continuing conversation. It holds the messages and
tool results that make up the conversation's context. Keep one client alive for the application,
then create a session for each independent conversation.

## Why clients and sessions stay separate

Keeping those responsibilities separate lets the runtime connection outlive any one conversation.
It also gives you a small working example before streaming and tools enter the picture.

At this point, the console app is simply `CopilotClient -> session -> model response`.
:::

## Fire up your first Copilot session

:::language dotnet
Open `Program.cs` and **replace the entire file**:

```csharp
using GitHub.Copilot;
using GitHub.Copilot.Rpc;

Console.WriteLine("=== First Copilot session ===\n");

await using var client = new CopilotClient();
await client.StartAsync();

var ping = await client.PingAsync("workshop");
Console.WriteLine($"Connected to the Copilot runtime: {ping.Message}");

await using var session = await client.CreateSessionAsync(new SessionConfig
{
    OnPermissionRequest = PermissionHandler.ApproveAll,
});
var response = await session.SendAndWaitAsync(
    "In one sentence, explain why an accessible name matters for a form input.");

if (response is null)
{
    throw new InvalidOperationException("Copilot completed without an assistant message.");
}

Console.WriteLine($"\nCopilot: {response.Data.Content}");
```

The ping verifies the runtime connection. The completed-response send waits until the session
becomes idle, so it works well when you only need the finished answer.
:::

:::language nodejs
Open `src/index.ts` and **replace the entire file**:

```typescript
import { approveAll, CopilotClient } from "@github/copilot-sdk";

const client = new CopilotClient();
await client.start();
try {
  const session = await client.createSession({ onPermissionRequest: approveAll });
  try {
    const response = await session.sendAndWait({ prompt: "Reply with one sentence confirming this Copilot session is ready." });
    console.log(response?.data && "content" in response.data ? response.data.content : response);
  } finally {
    await session.disconnect();
  }
} finally {
  await client.stop();
}
```

`sendAndWait` waits until the session becomes idle, so it works well when you only need the finished
answer. Always stop the session and client in `finally` blocks so the runtime shuts down cleanly.
:::

:::language python
Open `main.py` and **replace the entire file**:

```python
import asyncio

from copilot import CopilotClient, PermissionHandler
from copilot.session_events import AssistantMessageData, SessionErrorData, SessionIdleData


async def main() -> None:
    async with CopilotClient() as client:
        async with await client.create_session(
            on_permission_request=PermissionHandler.approve_all
        ) as session:
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
            await session.send("In one sentence, explain why an accessible name matters for a form input.")
            await done.wait()
            if error is not None:
                raise error


if __name__ == "__main__":
    asyncio.run(main())
```

Python listens for session events instead of calling a single completed-response helper. Print the
assistant message, treat session errors as failures, and wait for the idle event before exiting.
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
	client := copilot.NewClient(&copilot.ClientOptions{LogLevel: "error"})
	if err := client.Start(context.Background()); err != nil {
		panic(err)
	}
	defer client.Stop()

	session, err := client.CreateSession(context.Background(), &copilot.SessionConfig{
		OnPermissionRequest: copilot.PermissionHandler.ApproveAll,
	})
	if err != nil {
		panic(err)
	}
	defer session.Disconnect()

	response, err := session.SendAndWait(context.Background(), copilot.MessageOptions{
		Prompt: "In one sentence, explain why an accessible name matters for a form input.",
	})
	if err != nil {
		panic(err)
	}
	if response != nil {
		if message, ok := response.Data.(*copilot.AssistantMessageData); ok {
			fmt.Println(message.Content)
		}
	}
}
```

`SendAndWait` waits until the session becomes idle, so it works well when you only need the finished
answer. `defer` disconnects the session and stops the client on the way out.
:::

:::language rust
Open `src/main.rs` and **replace the entire file**:

```rust
use github_copilot_sdk::permission;
use github_copilot_sdk::types::{MessageOptions, SessionConfig};
use github_copilot_sdk::{Client, ClientOptions};

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let client = Client::start(ClientOptions::default()).await?;
    let session = client
        .create_session(SessionConfig::default().with_permission_handler(permission::approve_all()))
        .await?;
    let response = session
        .send_and_wait(MessageOptions::new(
            "In one sentence, explain why an accessible name matters for a form input.",
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

`send_and_wait` waits until the session becomes idle, so it works well when you only need the
finished answer. Disconnect the session and stop the client before returning.
:::

:::language java
Open `src/main/java/workshop/AccessibilityReport.java` and **replace the entire file**:

```java
package workshop;

import com.github.copilot.CopilotClient;
import com.github.copilot.rpc.PermissionHandler;
import com.github.copilot.rpc.MessageOptions;
import com.github.copilot.rpc.SessionConfig;

public final class AccessibilityReport {
    private AccessibilityReport() {
    }

    public static void main(String[] args) throws Exception {
        try (var client = new CopilotClient()) {
            client.start().get();
            var session = client
                    .createSession(new SessionConfig().setOnPermissionRequest(PermissionHandler.APPROVE_ALL)).get();
            var response = session.sendAndWait(new MessageOptions()
                    .setPrompt("In one sentence, explain why an accessible name matters for a form input."))
                    .get();
            if (response == null) {
                throw new IllegalStateException("Copilot completed without an assistant message.");
            }
            System.out.println(response.getData().content());
        }
    }
}
```

`sendAndWait` waits until the session becomes idle, so it works well when you only need the finished
answer. The try-with-resources block closes the client when `main` exits.
:::

This session sets a permission handler and nothing else, so it runs with the SDK's default persona.
The knob you did not turn is the
[system message](https://github.com/github/copilot-sdk/blob/main/docs/getting-started.md#customize-the-system-message),
which has three modes. `append` is the default: your content is added after the SDK-managed prompt,
and the default CLI persona is preserved along with the environment context, tool instructions, and
security guardrails the SDK injects. `replace` swaps the entire prompt for your content.
`customize` overrides individual sections — tone, guidelines, code change rules, and others — while
preserving the rest. This workshop stays on the default, so every answer you see comes from the
standard persona. Reach for the other two modes when an application needs a voice or a scope of its
own.

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
python main.py
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

:::language dotnet
Your exact response will vary, but the output should have this shape:

```text
=== First Copilot session ===

Connected to the Copilot runtime: ...

Copilot: An accessible name lets assistive technology identify the input's purpose.
```
:::

:::language nodejs
Your exact response will vary, but the output should have this shape:

```text
This Copilot session is ready and waiting for your next prompt.
```
:::

:::language python
Your exact response will vary, but the output should have this shape:

```text
An accessible name lets assistive technology identify the input's purpose.
```
:::

:::language go
Your exact response will vary, but the output should have this shape:

```text
An accessible name lets assistive technology identify the input's purpose.
```
:::

:::language rust
Your exact response will vary, but the output should have this shape:

```text
An accessible name lets assistive technology identify the input's purpose.
```
:::

:::language java
Your exact response will vary, but the output should have this shape:

```text
An accessible name lets assistive technology identify the input's purpose.
```
:::

<details>
<summary>Troubleshooting this run</summary>

| Symptom | Fix |
|---|---|
| Authentication or authorization error | Run `copilot login` again, then rerun the project. |
| Runtime executable not found | Set `COPILOT_CLI_BINARY_PATH` using the preflight instructions. |
| The request times out | Check network access to GitHub Copilot and retry; this example does not hide the failure. |

</details>

> **You're ready for streaming when:** the terminal prints one complete Copilot response.

## Check your understanding

Which object should usually live for the application lifetime, and which object owns one
conversation's context?

:::language dotnet
<details>
<summary>Check your answer</summary>

Keep `CopilotClient` for the lifetime of the runtime connection. A `CopilotSession` owns the
messages and tool context for one conversation.

</details>
:::

:::language nodejs
<details>
<summary>Check your answer</summary>

Keep `CopilotClient` for the lifetime of the runtime connection. A session from `createSession` owns
the messages and tool context for one conversation.

</details>
:::

:::language python
<details>
<summary>Check your answer</summary>

Keep `CopilotClient` for the lifetime of the runtime connection. A session from `create_session`
owns the messages and tool context for one conversation.

</details>
:::

:::language go
<details>
<summary>Check your answer</summary>

Keep the client from `copilot.NewClient` for the lifetime of the runtime connection. A session from
`CreateSession` owns the messages and tool context for one conversation.

</details>
:::

:::language rust
<details>
<summary>Check your answer</summary>

Keep `Client` for the lifetime of the runtime connection. A session from `create_session` owns the
messages and tool context for one conversation.

</details>
:::

:::language java
<details>
<summary>Check your answer</summary>

Keep `CopilotClient` for the lifetime of the runtime connection. A session from `createSession` owns
the messages and tool context for one conversation.

</details>
:::

:::language dotnet
<details>
<summary>Complete Step 1 implementation</summary>

Compare your work with this complete Step 1 implementation.

```csharp
using GitHub.Copilot;

Console.WriteLine("=== First Copilot session ===\n");

await using var client = new CopilotClient();
await client.StartAsync();

var ping = await client.PingAsync("workshop");
Console.WriteLine($"Connected to the Copilot runtime: {ping.Message}");

await using var session = await client.CreateSessionAsync(new SessionConfig());
var response = await session.SendAndWaitAsync(
    "In one sentence, explain why an accessible name matters for a form input.");

if (response is null)
{
    throw new InvalidOperationException("Copilot completed without an assistant message.");
}

Console.WriteLine($"\nCopilot: {response.Data.Content}");
```
</details>
:::

:::language nodejs
<details>
<summary>Complete Step 1 implementation</summary>

Compare your work with this complete Step 1 implementation.

```typescript
import { CopilotClient } from "@github/copilot-sdk";

const client = new CopilotClient();
await client.start();
try {
  const session = await client.createSession({});
  try {
    const response = await session.sendAndWait({ prompt: "Reply with one sentence confirming this Copilot session is ready." });
    console.log(response?.data && "content" in response.data ? response.data.content : response);
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
<details>
<summary>Complete Step 1 implementation</summary>

Compare your work with this complete Step 1 implementation.

```python
import asyncio

from copilot import CopilotClient
from copilot.session_events import AssistantMessageData, SessionErrorData, SessionIdleData


async def main() -> None:
    async with CopilotClient() as client:
        async with await client.create_session() as session:
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
            await session.send("In one sentence, explain why an accessible name matters for a form input.")
            await done.wait()
            if error is not None:
                raise error


if __name__ == "__main__":
    asyncio.run(main())
```
</details>
:::

:::language go
<details>
<summary>Complete Step 1 implementation</summary>

Compare your work with this complete Step 1 implementation.

```go
package main

import (
	"context"
	"fmt"

	copilot "github.com/github/copilot-sdk/go"
)

func main() {
	client := copilot.NewClient(&copilot.ClientOptions{LogLevel: "error"})
	if err := client.Start(context.Background()); err != nil {
		panic(err)
	}
	defer client.Stop()

	session, err := client.CreateSession(context.Background(), &copilot.SessionConfig{})
	if err != nil {
		panic(err)
	}
	defer session.Disconnect()

	response, err := session.SendAndWait(context.Background(), copilot.MessageOptions{
		Prompt: "In one sentence, explain why an accessible name matters for a form input.",
	})
	if err != nil {
		panic(err)
	}
	if response != nil {
		if message, ok := response.Data.(*copilot.AssistantMessageData); ok {
			fmt.Println(message.Content)
		}
	}
}
```
</details>
:::

:::language rust
<details>
<summary>Complete Step 1 implementation</summary>

Compare your work with this complete Step 1 implementation.

```rust
use github_copilot_sdk::types::{MessageOptions, SessionConfig};
use github_copilot_sdk::{Client, ClientOptions};

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let client = Client::start(ClientOptions::default()).await?;
    let session = client.create_session(SessionConfig::default()).await?;
    let response = session
        .send_and_wait(MessageOptions::new(
            "In one sentence, explain why an accessible name matters for a form input.",
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
</details>
:::

:::language java
<details>
<summary>Complete Step 1 implementation</summary>

Compare your work with this complete Step 1 implementation.

```java
package workshop;

import com.github.copilot.CopilotClient;
import com.github.copilot.rpc.MessageOptions;
import com.github.copilot.rpc.SessionConfig;

public final class AccessibilityReport {
    private AccessibilityReport() {
    }

    public static void main(String[] args) throws Exception {
        try (var client = new CopilotClient()) {
            client.start().get();
            var session = client.createSession(new SessionConfig()).get();
            var response = session.sendAndWait(new MessageOptions()
                    .setPrompt("In one sentence, explain why an accessible name matters for a form input."))
                    .get();
            if (response == null) {
                throw new IllegalStateException("Copilot completed without an assistant message.");
            }
            System.out.println(response.getData().content());
        }
    }
}
```
</details>
:::

## Learn more

- [Build your first Copilot-powered app](https://docs.github.com/en/copilot/how-tos/copilot-sdk/getting-started):
  GitHub's tutorial for the same first client, session, and prompt.
- [Session resume and persistence](https://github.com/github/copilot-sdk/blob/main/docs/features/session-persistence.md):
  how a session's conversation state is kept, and how to resume it after a restart.
- [Context clearing](https://github.com/github/copilot-sdk/blob/main/docs/features/context-management.md):
  replacing the conversation inside a session without creating a new one.
- [Authentication](https://github.com/github/copilot-sdk/blob/main/docs/auth/README.md):
  the credentials a client can use once you move past `copilot login`.

Continue to [Step 2: Stream a response](02-streaming.md).
