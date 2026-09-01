# Create a tool-free session

> **Time:** 15 minutes  
> **Goal:** Add the SDK boundary and a session configuration with no tools.

The system message guides behavior; it does not remove capabilities. `availableTools: []` is the
application-owned capability boundary. Streaming is disabled because validation needs the complete
response. `replace` removes coding-agent defaults instead of combining them with the curator role.

:::language dotnet
Create `museum-workshop-app/CuratorRuntime.cs` with the exact SDK adapter:

```csharp
using GitHub.Copilot;

namespace MuseumExhibitStudio;

public interface ICuratorSession : IAsyncDisposable
{
    Task<string?> SendAndWaitAsync(
        string prompt,
        TimeSpan timeout,
        CancellationToken cancellationToken = default);
}

public interface ICuratorClient : IAsyncDisposable
{
    Task StartAsync(CancellationToken cancellationToken = default);
    Task<ICuratorSession> CreateSessionAsync(
        SessionConfig configuration,
        CancellationToken cancellationToken = default);
    Task StopAsync();
}

public sealed class CopilotCuratorClient : ICuratorClient
{
    private readonly CopilotClient client = new();

    public Task StartAsync(CancellationToken cancellationToken = default) =>
        client.StartAsync(cancellationToken);

    public async Task<ICuratorSession> CreateSessionAsync(
        SessionConfig configuration,
        CancellationToken cancellationToken = default) =>
        new CopilotCuratorSession(
            await client.CreateSessionAsync(configuration, cancellationToken));

    public Task StopAsync() => client.StopAsync();
    public ValueTask DisposeAsync() => client.DisposeAsync();

    private sealed class CopilotCuratorSession(CopilotSession session) : ICuratorSession
    {
        public async Task<string?> SendAndWaitAsync(
            string prompt,
            TimeSpan timeout,
            CancellationToken cancellationToken = default)
        {
            var response = await session.SendAndWaitAsync(prompt, timeout, cancellationToken);
            return response?.Data.Content;
        }

        public ValueTask DisposeAsync() => session.DisposeAsync();
    }
}
```

Create `museum-workshop-app/MuseumExhibitService.cs` as the compile-ready configuration shell:

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
:::

:::language nodejs
Create `museum-workshop-app/src/service.ts`:

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
    systemMessage: { mode: "replace", content: systemMessage },
  };
}

export function createCopilotCuratorClient(): CuratorClient {
  return new CopilotClient();
}
```
:::

:::language python
Create `museum-workshop-app/museum_exhibit_service.py`:

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

`Any` is the deliberately small test seam used by the completed sample: production supplies a
`CopilotClient`, while tests supply a fake with the same three async methods.
:::

:::language go
Create `museum-workshop-app/service.go` with the configuration, interfaces, and SDK adapter:

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
			Mode: "replace", Content: curatorSystemMessage,
		},
	}
}

type copilotCuratorClient struct {
	client *copilot.Client
}

func newCopilotCuratorClient() *copilotCuratorClient {
	return &copilotCuratorClient{client: copilot.NewClient(&copilot.ClientOptions{LogLevel: "error"})}
}

func (client *copilotCuratorClient) Start(ctx context.Context) error {
	return client.client.Start(ctx)
}

func (client *copilotCuratorClient) CreateSession(
	ctx context.Context, config *copilot.SessionConfig,
) (curatorSession, error) {
	session, err := client.client.CreateSession(ctx, config)
	if err != nil {
		return nil, err
	}
	return copilotCuratorSession{session: session}, nil
}

func (client *copilotCuratorClient) Stop() error { return client.client.Stop() }

type copilotCuratorSession struct {
	session *copilot.Session
}

func (session copilotCuratorSession) SendAndWait(
	ctx context.Context, prompt string,
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
:::

:::language rust
At the top of `museum-workshop-app/src/lib.rs`, add these imports:

```rust
use std::error::Error;
use std::time::Duration;

use async_trait::async_trait;
use github_copilot_sdk::types::{MessageOptions, SessionConfig, SystemMessageConfig};
use github_copilot_sdk::{Client, ClientOptions};
```

Then append this configuration and runtime boundary to the same file:

```rust
pub const GENERATION_TIMEOUT: Duration = Duration::from_secs(120);

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

pub type RuntimeError = Box<dyn Error + Send + Sync>;

#[async_trait]
pub trait CuratorSession: Send {
    async fn send_and_wait(
        &mut self,
        prompt: String,
        timeout: Duration,
    ) -> Result<Option<String>, RuntimeError>;
    async fn disconnect(&mut self) -> Result<(), RuntimeError>;
}

#[async_trait]
pub trait CuratorClient: Send {
    async fn start(&mut self) -> Result<(), RuntimeError>;
    async fn create_session(
        &mut self,
        configuration: SessionConfig,
    ) -> Result<Box<dyn CuratorSession>, RuntimeError>;
    async fn stop(&mut self) -> Result<(), RuntimeError>;
}

pub struct CopilotCuratorClient {
    client: Option<Client>,
}

impl CopilotCuratorClient {
    pub fn new() -> Self { Self { client: None } }
}

impl Default for CopilotCuratorClient {
    fn default() -> Self { Self::new() }
}

struct CopilotCuratorSession(github_copilot_sdk::session::Session);

#[async_trait]
impl CuratorSession for CopilotCuratorSession {
    async fn send_and_wait(
        &mut self,
        prompt: String,
        timeout: Duration,
    ) -> Result<Option<String>, RuntimeError> {
        let event = self.0
            .send_and_wait(MessageOptions::new(prompt).with_wait_timeout(timeout))
            .await?;
        Ok(event.and_then(|event| event.data.get("content")
            .and_then(|content| content.as_str()).map(str::to_owned)))
    }

    async fn disconnect(&mut self) -> Result<(), RuntimeError> {
        self.0.disconnect().await?;
        Ok(())
    }
}

#[async_trait]
impl CuratorClient for CopilotCuratorClient {
    async fn start(&mut self) -> Result<(), RuntimeError> {
        self.client = Some(Client::start(ClientOptions::default()).await?);
        Ok(())
    }

    async fn create_session(
        &mut self,
        configuration: SessionConfig,
    ) -> Result<Box<dyn CuratorSession>, RuntimeError> {
        let client = self.client.as_ref()
            .ok_or_else(|| std::io::Error::other("The curator client is not started."))?;
        Ok(Box::new(CopilotCuratorSession(
            client.create_session(configuration).await?,
        )))
    }

    async fn stop(&mut self) -> Result<(), RuntimeError> {
        if let Some(client) = self.client.take() {
            client.stop().await?;
        }
        Ok(())
    }
}
```
:::

:::language java
Create `museum-workshop-app/src/main/java/workshop/CuratorRuntime.java`:

```java
package workshop;

import com.github.copilot.CopilotClient;
import com.github.copilot.CopilotSession;
import com.github.copilot.rpc.MessageOptions;
import com.github.copilot.rpc.SessionConfig;

interface CuratorSession {
    String sendAndWait(String prompt, long timeoutMillis) throws Exception;
    void disconnect();
}

interface CuratorClient extends AutoCloseable {
    void start() throws Exception;
    CuratorSession createSession(SessionConfig configuration) throws Exception;
    void stop() throws Exception;
    @Override void close();
}

final class CopilotCuratorClient implements CuratorClient {
    private final CopilotClient client = new CopilotClient();

    public void start() throws Exception { client.start().get(); }

    public CuratorSession createSession(SessionConfig configuration) throws Exception {
        return new CopilotCuratorSession(client.createSession(configuration).get());
    }

    public void stop() throws Exception { client.stop().get(); }
    public void close() { client.close(); }

    private record CopilotCuratorSession(CopilotSession session) implements CuratorSession {
        public String sendAndWait(String prompt, long timeoutMillis) throws Exception {
            var response = session.sendAndWait(
                    new MessageOptions().setPrompt(prompt), timeoutMillis).get();
            return response == null || response.getData() == null
                    ? null : response.getData().content();
        }

        public void disconnect() { session.close(); }
    }
}
```

Create `museum-workshop-app/src/main/java/workshop/MuseumExhibitService.java`:

```java
package workshop;

import com.github.copilot.SystemMessageMode;
import com.github.copilot.rpc.PermissionRequestResult;
import com.github.copilot.rpc.SessionConfig;
import com.github.copilot.rpc.SystemMessageConfig;
import java.util.List;
import java.util.concurrent.CompletableFuture;

public final class MuseumExhibitService {
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
:::

## Run it

These commands compile configuration and adapter types but do not authenticate or start Copilot.

:::language dotnet
```bash
dotnet build museum-workshop-app
```
:::
:::language nodejs
```bash
npm --prefix museum-workshop-app run build
```
:::
:::language python
```bash
museum-workshop-app/.venv/bin/python -m py_compile museum-workshop-app/curator_prompts.py museum-workshop-app/museum_exhibit_service.py
```
:::
:::language go
```bash
go -C museum-workshop-app test ./...
```
:::
:::language rust
```bash
cargo check --manifest-path museum-workshop-app/Cargo.toml --locked
```
:::
:::language java
```bash
mvn -f museum-workshop-app/pom.xml test
```
:::

Pass condition: compilation succeeds without starting a model session. If an SDK symbol is missing,
confirm that the copied manifest still pins 1.0.11 and rerun the preflight restore command.

## Check your understanding

1. Why is an empty SDK allowlist stronger than a prompt instruction?
2. Why is the system-message mode `replace`?
3. What do the client/session interfaces let tests replace?
