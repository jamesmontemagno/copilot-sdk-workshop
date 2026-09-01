# Own the lifecycle and test it

> **Time:** 30 minutes  
> **Goal:** Complete generation with bounded time, empty-output rejection, and cleanup on every path.

The application validates the prompt before startup, starts one client, creates one tool-free
session, waits at most two minutes, rejects blank output, validates content, then always disconnects
and stops. The SDK adapter translates SDK objects; the service owns application policy.

:::language dotnet
Replace `museum-workshop-app/MuseumExhibitService.cs`:

```csharp
using GitHub.Copilot;

namespace MuseumExhibitStudio;

public sealed record GeneratedExhibit(string Content, ExhibitValidation Validation);

public sealed class MuseumExhibitService(ICuratorClient client)
{
    public static readonly TimeSpan GenerationTimeout = TimeSpan.FromMinutes(2);

    public async Task<GeneratedExhibit> GenerateAsync(
        IEnumerable<string> approvedFacts,
        string? model = null,
        CancellationToken cancellationToken = default)
    {
        var prompt = CuratorPrompts.BuildExhibitPrompt(approvedFacts);

        await client.StartAsync(cancellationToken);
        try
        {
            await using var session = await client.CreateSessionAsync(
                CreateSessionConfiguration(model),
                cancellationToken);
            var content = await session.SendAndWaitAsync(
                prompt,
                GenerationTimeout,
                cancellationToken);

            if (string.IsNullOrWhiteSpace(content))
            {
                throw new InvalidOperationException("The curator returned no exhibit content.");
            }

            return new GeneratedExhibit(content, ExhibitValidator.Validate(content));
        }
        finally
        {
            await client.StopAsync();
        }
    }

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

Create `museum-workshop-app/tests/MuseumExhibitServiceTests.cs`:

```csharp
using GitHub.Copilot;
using MuseumExhibitStudio;

namespace MuseumExhibitStudio.Tests;

public sealed class MuseumExhibitServiceTests
{
    [Fact]
    public void CreateSessionConfigurationOwnsPromptAndHasNoTools()
    {
        var configuration = MuseumExhibitService.CreateSessionConfiguration("test-model");

        Assert.Equal("museum-exhibit-studio", configuration.ClientName);
        Assert.Equal("test-model", configuration.Model);
        Assert.Empty(configuration.AvailableTools!);
        Assert.Equal(SystemMessageMode.Replace, configuration.SystemMessage!.Mode);
        Assert.Equal(CuratorPrompts.SystemMessage, configuration.SystemMessage.Content);
    }

    [Fact]
    public async Task GenerateReturnsContentAndCleansUp()
    {
        var session = new FakeSession { Content = CreateValidExhibit() };
        await using var client = new FakeClient(session);
        var service = new MuseumExhibitService(client);

        var result = await service.GenerateAsync(CuratorPrompts.Apollo11Facts);

        Assert.True(result.Validation.Valid);
        Assert.True(result.Validation.Narrative.Valid);
        Assert.True(client.Started);
        Assert.True(client.Stopped);
        Assert.True(session.Disposed);
        Assert.NotNull(client.Configuration);
        Assert.All(CuratorPrompts.Apollo11Facts, fact => Assert.Contains(fact, session.Prompt));
    }

    [Fact]
    public async Task GenerateRejectsEmptyResponseAndCleansUp()
    {
        var session = new FakeSession { Content = " " };
        await using var client = new FakeClient(session);
        var service = new MuseumExhibitService(client);

        await Assert.ThrowsAsync<InvalidOperationException>(
            () => service.GenerateAsync(CuratorPrompts.Apollo11Facts));

        Assert.True(client.Stopped);
        Assert.True(session.Disposed);
    }

    [Fact]
    public async Task GenerateCleansUpAfterSessionFailure()
    {
        var session = new FakeSession { Failure = new TimeoutException("Timed out.") };
        await using var client = new FakeClient(session);
        var service = new MuseumExhibitService(client);

        await Assert.ThrowsAsync<TimeoutException>(
            () => service.GenerateAsync(CuratorPrompts.Apollo11Facts));

        Assert.True(client.Stopped);
        Assert.True(session.Disposed);
    }

    private static string CreateValidExhibit()
    {
        var narrative = string.Join(' ', Enumerable.Range(1, 110).Select(index => $"word{index}"));
        return $"""
            # A Journey
            ## Narrative
            {narrative}
            ## Visitor questions
            1. What do you notice?
            2. What would you ask?
            3. What will you remember?
            """;
    }

    private sealed class FakeClient(FakeSession session) : ICuratorClient
    {
        public bool Started { get; private set; }
        public bool Stopped { get; private set; }
        public SessionConfig? Configuration { get; private set; }

        public Task StartAsync(CancellationToken cancellationToken = default)
        {
            Started = true;
            return Task.CompletedTask;
        }

        public Task<ICuratorSession> CreateSessionAsync(
            SessionConfig configuration,
            CancellationToken cancellationToken = default)
        {
            Configuration = configuration;
            return Task.FromResult<ICuratorSession>(session);
        }

        public Task StopAsync()
        {
            Stopped = true;
            return Task.CompletedTask;
        }

        public ValueTask DisposeAsync() => ValueTask.CompletedTask;
    }

    private sealed class FakeSession : ICuratorSession
    {
        public string? Content { get; init; }
        public Exception? Failure { get; init; }
        public string Prompt { get; private set; } = string.Empty;
        public bool Disposed { get; private set; }

        public Task<string?> SendAndWaitAsync(
            string prompt,
            TimeSpan timeout,
            CancellationToken cancellationToken = default)
        {
            Prompt = prompt;
            return Failure is null
                ? Task.FromResult(Content)
                : Task.FromException<string?>(Failure);
        }

        public ValueTask DisposeAsync()
        {
            Disposed = true;
            return ValueTask.CompletedTask;
        }
    }
}
```
:::

:::language nodejs
Replace `museum-workshop-app/src/service.ts` with the completed service and SDK factory:

```typescript
import { CopilotClient, type SessionConfig } from "@github/copilot-sdk";
import { buildExhibitPrompt, systemMessage } from "./prompts.js";
import { validateExhibit, type ExhibitValidation } from "./validator.js";

export const generationTimeoutMs = 120_000;

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

export interface GeneratedExhibit {
  content: string;
  validation: ExhibitValidation;
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

export class MuseumExhibitService {
  constructor(private readonly client: CuratorClient) {}

  async generate(approvedFacts: Iterable<string>, model?: string): Promise<GeneratedExhibit> {
    const prompt = buildExhibitPrompt(approvedFacts);
    let session: CuratorSession | undefined;

    try {
      await this.client.start();
      session = await this.client.createSession(createSessionConfiguration(model));
      const response = await session.sendAndWait(prompt, generationTimeoutMs);
      const content = response?.data.content;
      if (!content?.trim()) throw new Error("The curator returned no exhibit content.");
      return { content, validation: validateExhibit(content) };
    } finally {
      try {
        await session?.disconnect();
      } finally {
        await this.client.stop();
      }
    }
  }
}

export function createCopilotCuratorClient(): CuratorClient {
  return new CopilotClient();
}
```

Create `museum-workshop-app/tests/service.test.ts`:

```typescript
import assert from "node:assert/strict";
import test from "node:test";
import type { SessionConfig } from "@github/copilot-sdk";
import { apollo11Facts, systemMessage } from "../src/prompts.js";
import {
  createSessionConfiguration,
  generationTimeoutMs,
  MuseumExhibitService,
  type CuratorClient,
  type CuratorSession,
} from "../src/service.js";

test("session config owns complete prompt and exposes no tools", () => {
  const config = createSessionConfiguration(" test-model ");
  assert.equal(config.clientName, "museum-exhibit-studio");
  assert.equal(config.model, "test-model");
  assert.deepEqual(config.availableTools, []);
  assert.equal(config.streaming, false);
  assert.deepEqual(config.systemMessage, { mode: "replace", content: systemMessage });
});

test("generation returns validated content with separate user prompt and cleans up", async () => {
  const harness = createHarness(validExhibit());
  const result = await new MuseumExhibitService(harness.client).generate(apollo11Facts);
  assert.equal(result.validation.valid, true);
  assert.equal(result.validation.narrative.valid, true);
  assert.equal(harness.started, true);
  assert.equal(harness.stopped, true);
  assert.equal(harness.disconnected, true);
  assert.equal(harness.timeout, generationTimeoutMs);
  apollo11Facts.forEach((fact) => assert.match(harness.prompt, new RegExp(escapeRegex(fact))));
  assert.equal(harness.prompt.includes(systemMessage), false);
});

test("generation rejects empty output and cleans up", async () => {
  const harness = createHarness(" ");
  await assert.rejects(
    new MuseumExhibitService(harness.client).generate(apollo11Facts),
    /no exhibit content/,
  );
  assert.equal(harness.disconnected, true);
  assert.equal(harness.stopped, true);
});

test("generation failure disconnects the session and stops the client", async () => {
  const harness = createHarness(undefined, new Error("Timed out."));
  await assert.rejects(new MuseumExhibitService(harness.client).generate(apollo11Facts), /Timed out/);
  assert.equal(harness.disconnected, true);
  assert.equal(harness.stopped, true);
});

test("client is stopped when session creation fails", async () => {
  let stopped = false;
  const client: CuratorClient = {
    start: async () => {},
    createSession: async () => { throw new Error("create failed"); },
    stop: async () => { stopped = true; },
  };
  await assert.rejects(new MuseumExhibitService(client).generate(apollo11Facts), /create failed/);
  assert.equal(stopped, true);
});

function createHarness(content?: string, failure?: Error) {
  const state = {
    started: false,
    stopped: false,
    disconnected: false,
    prompt: "",
    timeout: 0,
  };
  const session: CuratorSession = {
    sendAndWait: async (prompt, timeout) => {
      state.prompt = prompt;
      state.timeout = timeout ?? 0;
      if (failure) throw failure;
      return content === undefined ? undefined : { data: { content } };
    },
    disconnect: async () => { state.disconnected = true; },
  };
  const client: CuratorClient = {
    start: async () => { state.started = true; },
    createSession: async (_config: SessionConfig) => session,
    stop: async () => { state.stopped = true; },
  };
  return Object.assign(state, { client });
}

function validExhibit(): string {
  const narrative = Array.from({ length: 110 }, (_, index) => `word${index + 1}`).join(" ");
  return `# A Journey\n## Narrative\n${narrative}\n## Visitor questions\n1. What do you notice?\n2. What would you ask?\n3. What will you remember?`;
}

function escapeRegex(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}
```
:::

:::language python
Replace `museum-workshop-app/museum_exhibit_service.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from curator_prompts import SYSTEM_MESSAGE, build_exhibit_prompt
from exhibit_validator import ExhibitValidation, validate_exhibit

GENERATION_TIMEOUT_SECONDS = 120.0


@dataclass(frozen=True)
class GeneratedExhibit:
    content: str
    validation: ExhibitValidation


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

    async def generate(
        self, approved_facts: list[str] | tuple[str, ...], model: str | None = None
    ) -> GeneratedExhibit:
        prompt = build_exhibit_prompt(approved_facts)
        session = None
        try:
            await self._client.start()
            session = await self._client.create_session(
                **create_session_configuration(model)
            )
            response = await session.send_and_wait(
                prompt, timeout=GENERATION_TIMEOUT_SECONDS
            )
            content = getattr(getattr(response, "data", None), "content", None)
            if not content or not content.strip():
                raise RuntimeError("The curator returned no exhibit content.")
            return GeneratedExhibit(content, validate_exhibit(content))
        finally:
            try:
                if session is not None:
                    await session.disconnect()
            finally:
                await self._client.stop()
```

Create `museum-workshop-app/tests/test_museum_exhibit_service.py`:

```python
from types import SimpleNamespace
import unittest

from curator_prompts import APOLLO_11_FACTS, SYSTEM_MESSAGE
from museum_exhibit_service import (
    GENERATION_TIMEOUT_SECONDS,
    MuseumExhibitService,
    create_session_configuration,
)


def valid_exhibit() -> str:
    narrative = " ".join(f"word{index}" for index in range(1, 111))
    return (
        f"# A Journey\n## Narrative\n{narrative}\n## Visitor questions\n"
        "1. What do you notice?\n"
        "2. What would you ask?\n"
        "3. What will you remember?"
    )


class FakeSession:
    def __init__(self, content: str | None = None, failure: Exception | None = None):
        self.content = content
        self.failure = failure
        self.prompt = ""
        self.timeout = 0.0
        self.disconnected = False

    async def send_and_wait(self, prompt: str, *, timeout: float):
        self.prompt = prompt
        self.timeout = timeout
        if self.failure:
            raise self.failure
        return SimpleNamespace(data=SimpleNamespace(content=self.content))

    async def disconnect(self) -> None:
        self.disconnected = True


class FakeClient:
    def __init__(
        self,
        session: FakeSession,
        create_failure: Exception | None = None,
        start_failure: Exception | None = None,
    ) -> None:
        self.session = session
        self.create_failure = create_failure
        self.start_failure = start_failure
        self.started = False
        self.stopped = False
        self.configuration = {}

    async def start(self) -> None:
        self.started = True
        if self.start_failure:
            raise self.start_failure

    async def create_session(self, **configuration):
        self.configuration = configuration
        if self.create_failure:
            raise self.create_failure
        return self.session

    async def stop(self) -> None:
        self.stopped = True


class MuseumExhibitServiceTests(unittest.IsolatedAsyncioTestCase):
    def test_configuration_owns_system_prompt_and_has_no_tools(self) -> None:
        configuration = create_session_configuration(" test-model ")
        self.assertEqual("museum-exhibit-studio", configuration["client_name"])
        self.assertEqual("test-model", configuration["model"])
        self.assertEqual([], configuration["available_tools"])
        self.assertFalse(configuration["streaming"])
        self.assertEqual(
            {"mode": "replace", "content": SYSTEM_MESSAGE},
            configuration["system_message"],
        )

    async def test_success_returns_content_and_cleans_up(self) -> None:
        session = FakeSession(valid_exhibit())
        client = FakeClient(session)
        result = await MuseumExhibitService(client).generate(list(APOLLO_11_FACTS))
        self.assertTrue(result.validation.valid)
        self.assertTrue(result.validation.narrative.valid)
        self.assertTrue(client.started)
        self.assertTrue(client.stopped)
        self.assertTrue(session.disconnected)
        self.assertEqual(GENERATION_TIMEOUT_SECONDS, session.timeout)
        for fact in APOLLO_11_FACTS:
            self.assertIn(fact, session.prompt)

    async def test_invalid_prompt_never_starts_client(self) -> None:
        session = FakeSession()
        client = FakeClient(session)
        with self.assertRaises(ValueError):
            await MuseumExhibitService(client).generate([])
        self.assertFalse(client.started)

    async def test_empty_output_is_an_error_and_cleans_up(self) -> None:
        session = FakeSession(" ")
        client = FakeClient(session)
        with self.assertRaisesRegex(RuntimeError, "no exhibit content"):
            await MuseumExhibitService(client).generate(list(APOLLO_11_FACTS))
        self.assertTrue(session.disconnected)
        self.assertTrue(client.stopped)

    async def test_send_failure_disconnects_session_and_stops_client(self) -> None:
        session = FakeSession(failure=TimeoutError("Timed out."))
        client = FakeClient(session)
        with self.assertRaises(TimeoutError):
            await MuseumExhibitService(client).generate(list(APOLLO_11_FACTS))
        self.assertTrue(session.disconnected)
        self.assertTrue(client.stopped)

    async def test_create_failure_still_stops_client(self) -> None:
        session = FakeSession()
        client = FakeClient(session, create_failure=RuntimeError("create failed"))
        with self.assertRaisesRegex(RuntimeError, "create failed"):
            await MuseumExhibitService(client).generate(list(APOLLO_11_FACTS))
        self.assertFalse(session.disconnected)
        self.assertTrue(client.stopped)

    async def test_start_failure_still_stops_client(self) -> None:
        session = FakeSession()
        client = FakeClient(session, start_failure=RuntimeError("start failed"))
        with self.assertRaisesRegex(RuntimeError, "start failed"):
            await MuseumExhibitService(client).generate(list(APOLLO_11_FACTS))
        self.assertFalse(session.disconnected)
        self.assertTrue(client.stopped)


if __name__ == "__main__":
    unittest.main()
```
:::

:::language go
Replace `museum-workshop-app/service.go` with the completed sample implementation:

```go
package main

import (
	"context"
	"errors"
	"fmt"
	"strings"
	"time"

	copilot "github.com/github/copilot-sdk/go"
)

const generationTimeout = 120 * time.Second

type curatorSession interface {
	SendAndWait(context.Context, string) (string, error)
	Disconnect() error
}

type curatorClient interface {
	Start(context.Context) error
	CreateSession(context.Context, *copilot.SessionConfig) (curatorSession, error)
	Stop() error
}

type generatedExhibit struct {
	Content    string
	Validation ExhibitValidation
}

type museumExhibitService struct {
	client curatorClient
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

func (service museumExhibitService) Generate(ctx context.Context, approvedFacts []string, model string) (result generatedExhibit, err error) {
	prompt, err := buildExhibitPrompt(approvedFacts)
	if err != nil {
		return result, err
	}

	defer func() { err = errors.Join(err, service.client.Stop()) }()
	if err = service.client.Start(ctx); err != nil {
		return result, err
	}

	session, err := service.client.CreateSession(ctx, createSessionConfiguration(model))
	if err != nil {
		return result, err
	}
	defer func() { err = errors.Join(err, session.Disconnect()) }()

	generationContext, cancel := context.WithTimeout(ctx, generationTimeout)
	defer cancel()
	content, err := session.SendAndWait(generationContext, prompt)
	if err != nil {
		return result, err
	}
	if strings.TrimSpace(content) == "" {
		return result, fmt.Errorf("the curator returned no exhibit content")
	}
	return generatedExhibit{Content: content, Validation: validateExhibit(content)}, nil
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

func (client *copilotCuratorClient) CreateSession(ctx context.Context, config *copilot.SessionConfig) (curatorSession, error) {
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

func (session copilotCuratorSession) SendAndWait(ctx context.Context, prompt string) (string, error) {
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

Create `museum-workshop-app/service_test.go`:

```go
package main

import (
	"context"
	"errors"
	"strings"
	"testing"
	"time"

	copilot "github.com/github/copilot-sdk/go"
)

func TestCreateSessionConfiguration(t *testing.T) {
	config := createSessionConfiguration(" test-model ")
	if config.ClientName != "museum-exhibit-studio" {
		t.Errorf("ClientName = %q", config.ClientName)
	}
	if config.Model != "test-model" {
		t.Errorf("Model = %q", config.Model)
	}
	if config.AvailableTools == nil || len(config.AvailableTools) != 0 {
		t.Errorf("AvailableTools = %#v, want an explicit empty list", config.AvailableTools)
	}
	if config.Streaming == nil || *config.Streaming {
		t.Errorf("Streaming = %v, want false", config.Streaming)
	}
	if config.SystemMessage == nil || config.SystemMessage.Mode != "replace" ||
		config.SystemMessage.Content != curatorSystemMessage {
		t.Errorf("SystemMessage = %#v", config.SystemMessage)
	}
}

func TestGenerateLifecycle(t *testing.T) {
	sendFailure := errors.New("generation failed")
	createFailure := errors.New("create failed")
	startFailure := errors.New("start failed")
	tests := []struct {
		name        string
		content     string
		startErr    error
		createErr   error
		sendErr     error
		wantErr     string
		wantSession bool
		wantValid   bool
	}{
		{name: "success", content: makeExhibit(110, 3, true), wantSession: true, wantValid: true},
		{name: "empty output", content: " \n", wantErr: "no exhibit content", wantSession: true},
		{name: "send failure", sendErr: sendFailure, wantErr: sendFailure.Error(), wantSession: true},
		{name: "create failure", createErr: createFailure, wantErr: createFailure.Error()},
		{name: "start failure", startErr: startFailure, wantErr: startFailure.Error()},
	}

	for _, test := range tests {
		t.Run(test.name, func(t *testing.T) {
			session := &fakeSession{content: test.content, sendErr: test.sendErr}
			client := &fakeClient{
				session: session, startErr: test.startErr, createErr: test.createErr,
			}
			result, err := (museumExhibitService{client: client}).Generate(
				context.Background(), apollo11Facts, "test-model",
			)

			if test.wantErr == "" && err != nil {
				t.Fatalf("Generate() unexpected error: %v", err)
			}
			if test.wantErr != "" && (err == nil || !strings.Contains(err.Error(), test.wantErr)) {
				t.Fatalf("Generate() error = %v, want containing %q", err, test.wantErr)
			}
			if !client.stopCalled {
				t.Error("client Stop was not called")
			}
			if session.disconnectCalled != test.wantSession {
				t.Errorf("session Disconnect called = %t, want %t", session.disconnectCalled, test.wantSession)
			}
			if test.wantSession {
				if client.config == nil {
					t.Fatal("session configuration was not captured")
				}
				for _, fact := range apollo11Facts {
					if !strings.Contains(session.prompt, fact) {
						t.Errorf("prompt does not contain %q", fact)
					}
				}
				if session.deadlineRemaining <= 0 || session.deadlineRemaining > generationTimeout {
					t.Errorf("send deadline remaining = %v, want within %v", session.deadlineRemaining, generationTimeout)
				}
			}
			if test.wantErr == "" && result.Validation.Valid() != test.wantValid {
				t.Errorf("validation.Valid = %t, want %t", result.Validation.Valid(), test.wantValid)
			}
			if test.wantErr == "" && !result.Validation.Narrative.Valid() {
				t.Error("validation.Narrative.Valid = false")
			}
		})
	}
}

func TestGenerateReturnsCleanupFailures(t *testing.T) {
	session := &fakeSession{content: makeExhibit(110, 3, true), disconnectErr: errors.New("disconnect failed")}
	client := &fakeClient{session: session, stopErr: errors.New("stop failed")}
	_, err := (museumExhibitService{client: client}).Generate(context.Background(), apollo11Facts, "")
	if err == nil || !strings.Contains(err.Error(), "disconnect failed") || !strings.Contains(err.Error(), "stop failed") {
		t.Fatalf("Generate() error = %v, want both cleanup failures", err)
	}
}

type fakeClient struct {
	session     *fakeSession
	startErr    error
	createErr   error
	stopErr     error
	startCalled bool
	stopCalled  bool
	config      *copilot.SessionConfig
}

func (client *fakeClient) Start(context.Context) error {
	client.startCalled = true
	return client.startErr
}

func (client *fakeClient) CreateSession(_ context.Context, config *copilot.SessionConfig) (curatorSession, error) {
	client.config = config
	if client.createErr != nil {
		return nil, client.createErr
	}
	return client.session, nil
}

func (client *fakeClient) Stop() error {
	client.stopCalled = true
	return client.stopErr
}

type fakeSession struct {
	content           string
	sendErr           error
	disconnectErr     error
	prompt            string
	deadlineRemaining time.Duration
	disconnectCalled  bool
}

func (session *fakeSession) SendAndWait(ctx context.Context, prompt string) (string, error) {
	session.prompt = prompt
	if deadline, ok := ctx.Deadline(); ok {
		session.deadlineRemaining = time.Until(deadline)
	}
	return session.content, session.sendErr
}

func (session *fakeSession) Disconnect() error {
	session.disconnectCalled = true
	return session.disconnectErr
}
```
:::

:::language rust
Append this result, error, and lifecycle function to `museum-workshop-app/src/lib.rs`; the runtime
adapter from lesson 2 remains unchanged:

```rust
#[derive(Debug)]
struct StudioError(&'static str);
impl fmt::Display for StudioError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str(self.0)
    }
}
impl Error for StudioError {}

#[derive(Debug, Clone)]
pub struct GeneratedExhibit {
    pub content: String,
    pub validation: ExhibitValidation,
}

pub async fn generate_exhibit(
    client: &mut dyn CuratorClient,
    approved_facts: &[String],
    model: Option<&str>,
) -> Result<GeneratedExhibit, RuntimeError> {
    let prompt = build_exhibit_prompt(approved_facts)?;
    client.start().await?;
    let result = async {
        let mut session = client
            .create_session(create_session_configuration(model)).await?;
        let response = session.send_and_wait(prompt, GENERATION_TIMEOUT).await;
        let disconnect = session.disconnect().await;
        drop(session);
        match response {
            Err(error) => Err(error),
            Ok(content) => {
                disconnect?;
                let content = content.filter(|content| !content.trim().is_empty())
                    .ok_or_else(|| Box::new(StudioError(
                        "The curator returned no exhibit content.")) as RuntimeError)?;
                let validation = validate_exhibit(&content);
                Ok(GeneratedExhibit { content, validation })
            }
        }
    }.await;
    let stop = client.stop().await;
    match result {
        Err(error) => Err(error),
        Ok(exhibit) => { stop?; Ok(exhibit) }
    }
}
```

Create `museum-workshop-app/tests/service.rs`:

```rust
use async_trait::async_trait;
use museum_exhibit_studio::*;
use std::sync::{Arc, atomic::{AtomicBool, Ordering}};
use std::time::Duration;

struct Session { response: Result<Option<String>, RuntimeError>,
    disconnected: Arc<AtomicBool>, timeout: Arc<std::sync::Mutex<Duration>> }
#[async_trait]
impl CuratorSession for Session {
    async fn send_and_wait(&mut self, _: String, timeout: Duration)
        -> Result<Option<String>, RuntimeError> {
        *self.timeout.lock().unwrap() = timeout;
        std::mem::replace(&mut self.response, Ok(None))
    }
    async fn disconnect(&mut self) -> Result<(), RuntimeError> {
        self.disconnected.store(true, Ordering::SeqCst); Ok(())
    }
}
struct TestClient { session: Option<Session>, started: Arc<AtomicBool>,
    stopped: Arc<AtomicBool> }
#[async_trait]
impl CuratorClient for TestClient {
    async fn start(&mut self) -> Result<(), RuntimeError> {
        self.started.store(true, Ordering::SeqCst); Ok(())
    }
    async fn create_session(&mut self, _: github_copilot_sdk::types::SessionConfig)
        -> Result<Box<dyn CuratorSession>, RuntimeError> {
        Ok(Box::new(self.session.take().unwrap()))
    }
    async fn stop(&mut self) -> Result<(), RuntimeError> {
        self.stopped.store(true, Ordering::SeqCst); Ok(())
    }
}
fn client(content: Option<String>) -> (TestClient, Arc<AtomicBool>, Arc<AtomicBool>,
    Arc<AtomicBool>, Arc<std::sync::Mutex<Duration>>) {
    let started = Arc::new(AtomicBool::new(false));
    let stopped = Arc::new(AtomicBool::new(false));
    let disconnected = Arc::new(AtomicBool::new(false));
    let timeout = Arc::new(std::sync::Mutex::new(Duration::ZERO));
    (TestClient { session: Some(Session { response: Ok(content),
        disconnected: disconnected.clone(), timeout: timeout.clone() }),
        started: started.clone(), stopped: stopped.clone() },
        started, stopped, disconnected, timeout)
}
fn valid() -> String {
    let words = (1..=110).map(|i| format!("word{i}")).collect::<Vec<_>>().join(" ");
    format!("# A\n## Narrative\n{words}\n## Visitor questions\n1. One?\n2. Two?\n3. Three?")
}

#[tokio::test]
async fn success_and_empty_clean_up_with_timeout() {
    for output in [Some(valid()), Some(" ".to_owned())] {
        let (mut c, _, stopped, disconnected, timeout) = client(output);
        let facts = APOLLO_11_FACTS.map(str::to_owned);
        let result = generate_exhibit(&mut c, &facts, None).await;
        assert!(stopped.load(Ordering::SeqCst));
        assert!(disconnected.load(Ordering::SeqCst));
        assert_eq!(*timeout.lock().unwrap(), GENERATION_TIMEOUT);
        if let Ok(exhibit) = result {
            assert!(exhibit.validation.narrative.is_valid());
        }
    }
}

#[tokio::test]
async fn invalid_prompt_never_starts() {
    let (mut c, started, _, _, _) = client(Some(valid()));
    assert!(generate_exhibit(&mut c, &[], None).await.is_err());
    assert!(!started.load(Ordering::SeqCst));
}
```
:::

:::language java
Replace `museum-workshop-app/src/main/java/workshop/MuseumExhibitService.java`:

```java
package workshop;

import com.github.copilot.SystemMessageMode;
import com.github.copilot.rpc.PermissionRequestResult;
import com.github.copilot.rpc.SessionConfig;
import com.github.copilot.rpc.SystemMessageConfig;
import java.time.Duration;
import java.util.List;
import java.util.concurrent.CompletableFuture;

public final class MuseumExhibitService {
    public static final Duration GENERATION_TIMEOUT = Duration.ofSeconds(120);

    private final CuratorClient client;

    public MuseumExhibitService(CuratorClient client) {
        this.client = client;
    }

    public GeneratedExhibit generate(Iterable<String> approvedFacts, String model) throws Exception {
        String prompt = CuratorPrompts.buildExhibitPrompt(approvedFacts);
        CuratorSession session = null;
        try {
            client.start();
            session = client.createSession(createSessionConfiguration(model));
            String content = session.sendAndWait(prompt, GENERATION_TIMEOUT.toMillis());
            if (content == null || content.isBlank()) {
                throw new IllegalStateException("The curator returned no exhibit content.");
            }
            return new GeneratedExhibit(content, ExhibitValidator.validate(content));
        } finally {
            try {
                if (session != null) {
                    session.disconnect();
                }
            } finally {
                client.stop();
            }
        }
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

    public record GeneratedExhibit(String content, ExhibitValidation validation) {
    }
}
```

Create `museum-workshop-app/src/test/java/workshop/MuseumExhibitServiceTest.java`:

```java
package workshop;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.github.copilot.SystemMessageMode;
import com.github.copilot.rpc.SessionConfig;
import java.util.List;
import java.util.concurrent.TimeoutException;
import java.util.stream.IntStream;
import org.junit.jupiter.api.Test;

class MuseumExhibitServiceTest {
    @Test
    void configurationOwnsPromptAndHasNoTools() {
        SessionConfig configuration = MuseumExhibitService.createSessionConfiguration("test-model");

        assertEquals("museum-exhibit-studio", configuration.getClientName());
        assertEquals("test-model", configuration.getModel());
        assertTrue(configuration.getAvailableTools().isEmpty());
        assertFalse(configuration.isStreaming());
        assertEquals(SystemMessageMode.REPLACE, configuration.getSystemMessage().getMode());
        assertEquals(CuratorPrompts.SYSTEM_MESSAGE, configuration.getSystemMessage().getContent());
        assertEquals(120, MuseumExhibitService.GENERATION_TIMEOUT.toSeconds());
    }

    @Test
    void generateReturnsContentAndCleansUp() throws Exception {
        FakeSession session = new FakeSession(validExhibit(), null);
        FakeClient client = new FakeClient(session);

        var result = new MuseumExhibitService(client)
                .generate(CuratorPrompts.APOLLO_11_FACTS, null);

        assertTrue(result.validation().valid());
        assertTrue(result.validation().narrative().valid());
        assertTrue(client.started);
        assertTrue(client.stopped);
        assertTrue(session.disconnected);
        assertEquals(120_000, session.timeoutMillis);
        assertNotNull(client.configuration);
        CuratorPrompts.APOLLO_11_FACTS.forEach(
                fact -> assertTrue(session.prompt.contains(fact)));
    }

    @Test
    void invalidPromptNeverStartsClient() {
        FakeClient client = new FakeClient(new FakeSession(null, null));

        assertThrows(IllegalArgumentException.class,
                () -> new MuseumExhibitService(client).generate(List.of(), null));

        assertFalse(client.started);
    }

    @Test
    void generateRejectsEmptyResponseAndCleansUp() {
        FakeSession session = new FakeSession(" ", null);
        FakeClient client = new FakeClient(session);

        assertThrows(IllegalStateException.class,
                () -> new MuseumExhibitService(client)
                        .generate(CuratorPrompts.APOLLO_11_FACTS, null));

        assertTrue(client.stopped);
        assertTrue(session.disconnected);
    }

    @Test
    void generateCleansUpAfterSessionFailure() {
        FakeSession session = new FakeSession(null, new TimeoutException("Timed out."));
        FakeClient client = new FakeClient(session);

        assertThrows(TimeoutException.class,
                () -> new MuseumExhibitService(client)
                        .generate(CuratorPrompts.APOLLO_11_FACTS, null));

        assertTrue(client.stopped);
        assertTrue(session.disconnected);
    }

    @Test
    void clientStopsWhenStartupFails() {
        FakeClient client = new FakeClient(new FakeSession(null, null));
        client.startFailure = new IllegalStateException("Cannot start.");

        assertThrows(IllegalStateException.class,
                () -> new MuseumExhibitService(client)
                        .generate(CuratorPrompts.APOLLO_11_FACTS, null));

        assertTrue(client.stopped);
    }

    private static String validExhibit() {
        String narrative = IntStream.rangeClosed(1, 110)
                .mapToObj(index -> "word" + index)
                .reduce((left, right) -> left + " " + right)
                .orElseThrow();
        return """
                # A Journey
                ## Narrative
                %s
                ## Visitor questions
                1. What do you notice?
                2. What would you ask?
                3. What will you remember?
                """.formatted(narrative);
    }

    private static final class FakeClient implements CuratorClient {
        private final FakeSession session;
        private boolean started;
        private boolean stopped;
        private SessionConfig configuration;
        private Exception startFailure;

        private FakeClient(FakeSession session) {
            this.session = session;
        }

        @Override
        public void start() throws Exception {
            started = true;
            if (startFailure != null) {
                throw startFailure;
            }
        }

        @Override
        public CuratorSession createSession(SessionConfig configuration) {
            this.configuration = configuration;
            return session;
        }

        @Override
        public void stop() {
            stopped = true;
        }

        @Override
        public void close() {
        }
    }

    private static final class FakeSession implements CuratorSession {
        private final String content;
        private final Exception failure;
        private String prompt;
        private long timeoutMillis;
        private boolean disconnected;

        private FakeSession(String content, Exception failure) {
            this.content = content;
            this.failure = failure;
        }

        @Override
        public String sendAndWait(String prompt, long timeoutMillis) throws Exception {
            this.prompt = prompt;
            this.timeoutMillis = timeoutMillis;
            if (failure != null) {
                throw failure;
            }
            return content;
        }

        @Override
        public void disconnect() {
            disconnected = true;
        }
    }
}
```
:::

## Run it

No test creates a real SDK client; every lifecycle assertion uses a fake.

:::language dotnet
```bash
dotnet test museum-workshop-app/tests/museum-exhibit-studio.Tests.csproj
```
:::
:::language nodejs
```bash
npm --prefix museum-workshop-app test
```
:::
:::language python
```bash
PYTHONPATH=museum-workshop-app museum-workshop-app/.venv/bin/python -m unittest discover -s museum-workshop-app/tests
```
:::
:::language go
```bash
go -C museum-workshop-app test ./...
```
:::
:::language rust
```bash
cargo test --manifest-path museum-workshop-app/Cargo.toml --locked
```
:::
:::language java
```bash
mvn -f museum-workshop-app/pom.xml test
```
:::

Pass condition: tests prove pre-start prompt validation, the 120-second bound, blank rejection, and
cleanup after success and failure. If a test opens an authentication prompt, it constructed the
production adapter instead of the fake.

## Check your understanding

1. Why is prompt validation the first service operation?
2. Which resources are released after a timeout?
3. Why do lifecycle tests use interfaces rather than a live model?
