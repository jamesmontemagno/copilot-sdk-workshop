# Own the lifecycle

> **Time:** 15 minutes
> **Goal:** Move generation into a service that enforces a response timeout, rejects blank output,
> and always stops the client, then watch each of those boundaries in the running CLI.

Previous: [Validate the exhibit deterministically](museum-04-deterministic-validation.md)

Until now the entrypoint has driven the client directly. That is fine for a demonstration and wrong
for production: a stalled model hangs the process forever, an empty response reaches the validator
as an empty exhibit, and an early failure can leave a Copilot process running.

This lesson introduces the generation service the finished application ships with. It owns three
guarantees:

| Boundary | Behavior |
|---|---|
| Response timeout | 120 seconds, applied by the application rather than hoped for |
| Blank output | An empty or whitespace-only response is an error, never a validated exhibit |
| Cleanup | The session disconnects and the client stops on success **and** on failure |

The service also becomes the single place that builds the prompt, calls the session, and validates
the result, so the entrypoint shrinks to input, output, and error reporting. The CLI stops echoing
the prompt from lesson 3 and prints the enforced boundaries instead.

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

`StopAsync` sits in a `finally` block, so it runs after a timeout, after a blank-output rejection,
and after an exception thrown while creating the session.

Replace `museum-workshop-app/Program.cs`:

```csharp
using MuseumExhibitStudio;

Console.WriteLine("=== Museum Exhibit Studio ===");
Console.WriteLine("Approved Apollo 11 facts:");
for (var index = 0; index < CuratorPrompts.Apollo11Facts.Count; index++)
{
    Console.WriteLine($"{index + 1}. {CuratorPrompts.Apollo11Facts[index]}");
}

Console.WriteLine(
    $"\nLifecycle boundaries: {MuseumExhibitService.GenerationTimeout.TotalSeconds:0} second " +
    "response timeout, blank output rejected, client stopped on every path.");

await using var client = new CopilotCuratorClient();
var studio = new MuseumExhibitService(client);

try
{
    var result = await studio.GenerateAsync(
        CuratorPrompts.Apollo11Facts,
        Environment.GetEnvironmentVariable("COPILOT_MODEL"));
    Console.WriteLine($"\n{result.Content}\n");
    PrintValidation(result.Validation);
    Console.WriteLine("\nCurator client stopped; no Copilot process remains.");
    return 0;
}
catch (TimeoutException)
{
    Console.Error.WriteLine("The curator did not respond within two minutes. Try again.");
    return 1;
}
catch (Exception exception)
{
    Console.Error.WriteLine($"Could not generate the exhibit: {exception.Message}");
    return 1;
}

static void PrintValidation(ExhibitValidation validation)
{
    Console.WriteLine(validation.Valid
        ? "Structural checks passed."
        : "Structural checks found issues:");

    Console.WriteLine($"- One level-one title: {validation.Title.Present}");
    Console.WriteLine($"- Narrative section: {validation.Narrative.Present}");
    Console.WriteLine(
        $"- Narrative length: {validation.Narrative.WordCount} words " +
        $"(within 100-140: {validation.Narrative.WithinLimit})");
    Console.WriteLine($"- Visitor questions section: {validation.VisitorQuestions.Present}");
    Console.WriteLine(
        $"- Numbered questions: {validation.VisitorQuestions.QuestionCount} " +
        $"(exactly three: {validation.VisitorQuestions.ExactlyThree})");
    Console.WriteLine($"- Every item is a question: {validation.VisitorQuestions.AllItemsAreQuestions}");

    foreach (var error in validation.Errors)
    {
        Console.WriteLine($"  - {error}");
    }

    Console.WriteLine(
        "\nStructural checks do not prove factual grounding. " +
        "Unsupported claims require human review or a separate evaluator.");
}
```
:::

:::language nodejs
Replace `museum-workshop-app/src/service.ts`:

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

The nested `finally` matters: if `disconnect()` throws, `stop()` still runs.

Replace `museum-workshop-app/src/index.ts`:

```typescript
import { apollo11Facts } from "./prompts.js";
import {
  createCopilotCuratorClient,
  generationTimeoutMs,
  MuseumExhibitService,
} from "./service.js";
import type { ExhibitValidation } from "./validator.js";

console.log("=== Museum Exhibit Studio ===");
console.log("Approved Apollo 11 facts:");
apollo11Facts.forEach((fact, index) => console.log(`${index + 1}. ${fact}`));

console.log(
  `\nLifecycle boundaries: ${generationTimeoutMs / 1000} second response timeout, ` +
    "blank output rejected, client stopped on every path.",
);

try {
  const studio = new MuseumExhibitService(createCopilotCuratorClient());
  const result = await studio.generate(apollo11Facts, process.env.COPILOT_MODEL);
  console.log(`\n${result.content}\n`);
  printValidation(result.validation);
  console.log("\nCurator client stopped; no Copilot process remains.");
} catch (error) {
  const message = error instanceof Error ? error.message : String(error);
  console.error(message.toLocaleLowerCase().includes("timeout")
    ? "The curator did not respond within two minutes. Try again."
    : `Could not generate the exhibit: ${message}`);
  process.exitCode = 1;
}

function printValidation(validation: ExhibitValidation): void {
  console.log(validation.valid ? "Structural checks passed." : "Structural checks found issues:");
  console.log(`- One level-one title: ${validation.title.present}`);
  console.log(`- Narrative section: ${validation.narrative.present}`);
  console.log(`- Narrative length: ${validation.narrative.wordCount} words (within 100-140: ${validation.narrative.withinLimit})`);
  console.log(`- Visitor questions section: ${validation.visitorQuestions.present}`);
  console.log(`- Numbered questions: ${validation.visitorQuestions.questionCount} (exactly three: ${validation.visitorQuestions.exactlyThree})`);
  console.log(`- Every item is a question: ${validation.visitorQuestions.allItemsAreQuestions}`);
  validation.errors.forEach((error) => console.log(`  - ${error}`));
  console.log("\nStructural checks do not prove factual grounding. Unsupported claims require human review or a separate evaluator.");
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

The nested `finally` matters: if `disconnect()` raises, `stop()` still runs.

Replace `museum-workshop-app/main.py`:

```python
from __future__ import annotations

import asyncio
import os
import sys

from copilot import CopilotClient

from curator_prompts import APOLLO_11_FACTS
from exhibit_validator import ExhibitValidation
from museum_exhibit_service import GENERATION_TIMEOUT_SECONDS, MuseumExhibitService

GROUNDING_DISCLAIMER = (
    "Structural checks do not prove factual grounding. "
    "Unsupported claims require human review or a separate evaluator."
)


def print_validation(validation: ExhibitValidation) -> None:
    print(
        "Structural checks passed."
        if validation.valid
        else "Structural checks found issues:"
    )
    print(f"- One level-one title: {validation.title.present}")
    print(f"- Narrative section: {validation.narrative.present}")
    print(
        f"- Narrative length: {validation.narrative.word_count} words "
        f"(within 100-140: {validation.narrative.within_limit})"
    )
    print(f"- Visitor questions section: {validation.visitor_questions.present}")
    print(
        f"- Numbered questions: {validation.visitor_questions.question_count} "
        f"(exactly three: {validation.visitor_questions.exactly_three})"
    )
    print(
        "- Every item is a question: "
        f"{validation.visitor_questions.all_items_are_questions}"
    )
    for error in validation.errors:
        print(f"  - {error}")
    print(f"\n{GROUNDING_DISCLAIMER}")


async def main() -> int:
    print("=== Museum Exhibit Studio ===")
    print("Approved Apollo 11 facts:")
    for index, fact in enumerate(APOLLO_11_FACTS, start=1):
        print(f"{index}. {fact}")

    print(
        f"\nLifecycle boundaries: {GENERATION_TIMEOUT_SECONDS:.0f} second response "
        "timeout, blank output rejected, client stopped on every path."
    )

    try:
        studio = MuseumExhibitService(CopilotClient())
        result = await studio.generate(list(APOLLO_11_FACTS), os.getenv("COPILOT_MODEL"))
        print(f"\n{result.content}\n")
        print_validation(result.validation)
        print("\nCurator client stopped; no Copilot process remains.")
        return 0
    except TimeoutError:
        print("The curator did not respond within two minutes. Try again.", file=sys.stderr)
        return 1
    except Exception as error:
        print(f"Could not generate the exhibit: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
```
:::

:::language go
Add the generation lifecycle to `museum-workshop-app/service.go`. Replace its import block with:

```go
import (
	"context"
	"errors"
	"fmt"
	"strings"
	"time"

	copilot "github.com/github/copilot-sdk/go"
)
```

Then append the timeout constant, the result type, the service type, and the `Generate` method to
the same file:

```go
const generationTimeout = 120 * time.Second

type generatedExhibit struct {
	Content    string
	Validation ExhibitValidation
}

type museumExhibitService struct {
	client curatorClient
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
```

The deferred `Stop` is registered before `Start` is checked, so the client is stopped even when
session creation fails. `errors.Join` keeps a cleanup failure visible instead of discarding it.

Replace `museum-workshop-app/main.go`:

```go
package main

import (
	"context"
	"errors"
	"fmt"
	"os"
)

func main() {
	fmt.Println("=== Museum Exhibit Studio ===")
	fmt.Println("Approved Apollo 11 facts:")
	for index, fact := range apollo11Facts {
		fmt.Printf("%d. %s\n", index+1, fact)
	}

	fmt.Printf("\nLifecycle boundaries: %.0f second response timeout, blank output rejected, "+
		"client stopped on every path.\n", generationTimeout.Seconds())

	result, err := (museumExhibitService{client: newCopilotCuratorClient()}).Generate(
		context.Background(),
		apollo11Facts,
		os.Getenv("COPILOT_MODEL"),
	)
	if err != nil {
		if errors.Is(err, context.DeadlineExceeded) {
			fmt.Fprintln(os.Stderr, "The curator did not respond within two minutes. Try again.")
		} else {
			fmt.Fprintln(os.Stderr, "Could not generate the exhibit:", err)
		}
		os.Exit(1)
	}

	fmt.Printf("\n%s\n\n", result.Content)
	printValidation(result.Validation)
	fmt.Println("\nCurator client stopped; no Copilot process remains.")
}

func printValidation(validation ExhibitValidation) {
	if validation.Valid() {
		fmt.Println("Structural checks passed.")
	} else {
		fmt.Println("Structural checks found issues:")
	}
	fmt.Printf("- One level-one title: %t\n", validation.Title.Present())
	fmt.Printf("- Narrative section: %t\n", validation.Narrative.Present)
	fmt.Printf("- Narrative length: %d words (within 100-140: %t)\n", validation.Narrative.WordCount, validation.Narrative.WithinLimit())
	fmt.Printf("- Visitor questions section: %t\n", validation.VisitorQuestions.Present)
	fmt.Printf("- Numbered questions: %d (exactly three: %t)\n", validation.VisitorQuestions.QuestionCount, validation.VisitorQuestions.ExactlyThree())
	fmt.Printf("- Every item is a question: %t\n", validation.VisitorQuestions.AllItemsAreQuestions)
	for _, message := range validation.Errors {
		fmt.Println("  -", message)
	}
	fmt.Println("\nStructural checks do not prove factual grounding. Unsupported claims require human review or a separate evaluator.")
}
```
:::

:::language rust
Add the lifecycle to `museum-workshop-app/src/lib.rs`, below `validate_exhibit`:

```rust
pub const GENERATION_TIMEOUT: Duration = Duration::from_secs(120);

#[derive(Debug)]
struct StudioError(&'static str);

impl fmt::Display for StudioError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str(self.0)
    }
}

impl Error for StudioError {}

pub fn is_timeout_error(error: &(dyn Error + 'static)) -> bool {
    let mut current = Some(error);
    while let Some(candidate) = current {
        if candidate
            .downcast_ref::<std::io::Error>()
            .is_some_and(|error| error.kind() == std::io::ErrorKind::TimedOut)
        {
            return true;
        }
        let message = candidate.to_string().to_lowercase();
        if message.contains("timed out") || message.contains("timeout") {
            return true;
        }
        current = candidate.source();
    }
    false
}

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
            .create_session(create_session_configuration(model))
            .await?;
        let response = session.send_and_wait(prompt, GENERATION_TIMEOUT).await;
        let disconnect = session.disconnect().await;
        drop(session);

        match response {
            Err(error) => Err(error),
            Ok(content) => {
                disconnect?;
                let content = content
                    .filter(|content| !content.trim().is_empty())
                    .ok_or_else(|| {
                        Box::new(StudioError("The curator returned no exhibit content."))
                            as RuntimeError
                    })?;
                let validation = validate_exhibit(&content);
                Ok(GeneratedExhibit {
                    content,
                    validation,
                })
            }
        }
    }
    .await;

    let stop = client.stop().await;
    match result {
        Err(error) => Err(error),
        Ok(exhibit) => {
            stop?;
            Ok(exhibit)
        }
    }
}
```

`client.stop()` is awaited after the inner block regardless of how that block ended, so a timeout,
an empty response, or a failed session creation all still stop the client.

Replace `museum-workshop-app/src/main.rs`:

```rust
use museum_exhibit_studio::{
    APOLLO_11_FACTS, CopilotCuratorClient, ExhibitValidation, GENERATION_TIMEOUT, RuntimeError,
    generate_exhibit, is_timeout_error,
};

fn print_validation(validation: &ExhibitValidation) {
    println!(
        "{}",
        if validation.is_valid() {
            "Structural checks passed."
        } else {
            "Structural checks found issues:"
        }
    );
    println!("- One level-one title: {}", validation.title.is_present());
    println!("- Narrative section: {}", validation.narrative.present);
    println!(
        "- Narrative length: {} words (within 100-140: {})",
        validation.narrative.word_count,
        validation.narrative.is_within_limit()
    );
    println!(
        "- Visitor questions section: {}",
        validation.visitor_questions.present
    );
    println!(
        "- Numbered questions: {} (exactly three: {})",
        validation.visitor_questions.question_count,
        validation.visitor_questions.has_exactly_three()
    );
    println!(
        "- Every item is a question: {}",
        validation.visitor_questions.all_items_are_questions
    );
    for error in &validation.errors {
        println!("  - {error}");
    }
    println!(
        "\nStructural checks do not prove factual grounding. Unsupported claims require human review or a separate evaluator."
    );
}

async fn run() -> Result<(), RuntimeError> {
    println!("=== Museum Exhibit Studio ===");
    println!("Approved Apollo 11 facts:");
    for (index, fact) in APOLLO_11_FACTS.iter().enumerate() {
        println!("{}. {fact}", index + 1);
    }

    println!(
        "\nLifecycle boundaries: {} second response timeout, blank output rejected, \
         client stopped on every path.",
        GENERATION_TIMEOUT.as_secs()
    );

    let facts: Vec<String> = APOLLO_11_FACTS.map(str::to_owned).to_vec();
    let mut client = CopilotCuratorClient::new();
    let result = generate_exhibit(
        &mut client,
        &facts,
        std::env::var("COPILOT_MODEL").ok().as_deref(),
    )
    .await?;

    println!("\n{}\n", result.content);
    print_validation(&result.validation);
    println!("\nCurator client stopped; no Copilot process remains.");
    Ok(())
}

#[tokio::main]
async fn main() {
    if let Err(error) = run().await {
        if is_timeout_error(error.as_ref()) {
            eprintln!("The curator did not respond within two minutes. Try again.");
        } else {
            eprintln!("Could not generate the exhibit: {error}");
        }
        std::process::exit(1);
    }
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

The nested `finally` matters: if `disconnect()` throws, `stop()` still runs.

Replace `museum-workshop-app/src/main/java/workshop/MuseumExhibitStudio.java`:

```java
package workshop;

import java.util.concurrent.TimeoutException;

public final class MuseumExhibitStudio {
    private MuseumExhibitStudio() {
    }

    public static void main(String[] args) {
        System.out.println("=== Museum Exhibit Studio ===");
        System.out.println("Approved Apollo 11 facts:");
        for (int index = 0; index < CuratorPrompts.APOLLO_11_FACTS.size(); index++) {
            System.out.printf("%d. %s%n", index + 1, CuratorPrompts.APOLLO_11_FACTS.get(index));
        }

        System.out.printf(
                "%nLifecycle boundaries: %d second response timeout, blank output rejected, "
                        + "client stopped on every path.%n",
                MuseumExhibitService.GENERATION_TIMEOUT.toSeconds());

        try (var client = new CopilotCuratorClient()) {
            var studio = new MuseumExhibitService(client);
            var result = studio.generate(
                    CuratorPrompts.APOLLO_11_FACTS, System.getenv("COPILOT_MODEL"));
            System.out.printf("%n%s%n%n", result.content());
            printValidation(result.validation());
            System.out.println("\nCurator client stopped; no Copilot process remains.");
        } catch (Exception exception) {
            if (hasCause(exception, TimeoutException.class)) {
                System.err.println("The curator did not respond within two minutes. Try again.");
            } else {
                System.err.println("Could not generate the exhibit: " + rootMessage(exception));
            }
            System.exit(1);
        }
    }

    private static void printValidation(ExhibitValidation validation) {
        System.out.println(validation.valid()
                ? "Structural checks passed."
                : "Structural checks found issues:");
        System.out.println("- One level-one title: " + validation.title().present());
        System.out.println("- Narrative section: " + validation.narrative().present());
        System.out.printf(
                "- Narrative length: %d words (within 100-140: %s)%n",
                validation.narrative().wordCount(),
                validation.narrative().withinLimit());
        System.out.println(
                "- Visitor questions section: " + validation.visitorQuestions().present());
        System.out.printf(
                "- Numbered questions: %d (exactly three: %s)%n",
                validation.visitorQuestions().questionCount(),
                validation.visitorQuestions().exactlyThree());
        System.out.println(
                "- Every item is a question: "
                        + validation.visitorQuestions().allItemsAreQuestions());
        validation.errors().forEach(error -> System.out.println("  - " + error));
        System.out.println("""

                Structural checks do not prove factual grounding. Unsupported claims require \
                human review or a separate evaluator.""");
    }

    private static boolean hasCause(Throwable error, Class<? extends Throwable> type) {
        Throwable current = error;
        while (current != null) {
            if (type.isInstance(current)) {
                return true;
            }
            current = current.getCause();
        }
        return false;
    }

    private static String rootMessage(Throwable error) {
        Throwable current = error;
        while (current.getCause() != null) {
            current = current.getCause();
        }
        return current.getMessage() == null
                ? current.getClass().getSimpleName()
                : current.getMessage();
    }
}
```
:::

## Run it

Build, then run. The run contacts a model and needs an authenticated GitHub Copilot CLI.

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

A successful run now states its boundaries first and confirms cleanup last:

```text
=== Museum Exhibit Studio ===
Approved Apollo 11 facts:
1. Apollo 11 launched July 16, 1969.
2. It landed on the Moon July 20, 1969.
3. Neil Armstrong and Buzz Aldrin walked on the Moon.
4. Michael Collins remained in lunar orbit.
5. The mission returned to Earth July 24, 1969.

Lifecycle boundaries: 120 second response timeout, blank output rejected, client stopped on every path.

# Footprints Beyond Earth
## Narrative
...
## Visitor questions
1. ...
2. ...
3. ...

Structural checks passed.
- One level-one title: true
- Narrative section: true
- Narrative length: 121 words (within 100-140: true)
- Visitor questions section: true
- Numbered questions: 3 (exactly three: true)
- Every item is a question: true

Structural checks do not prove factual grounding. Unsupported claims require human review
or a separate evaluator.

Curator client stopped; no Copilot process remains.
```

Now watch the timeout boundary do its job. Change the generation timeout constant in the service to
one second, rebuild, and rerun. The model cannot finish that fast, so the run ends on the error
path:

```text
The curator did not respond within two minutes. Try again.
```

The message names two minutes because it describes the shipped boundary; the process exits with
status 1 rather than hanging, which is the behavior under evaluation. Restore the 120-second value
and rebuild before continuing.

The blank-output boundary uses the same error path. When a response arrives with no usable content,
the service refuses to validate it and the CLI prints:

```text
Could not generate the exhibit: The curator returned no exhibit content.
```

In every one of those runs, cleanup still happened: the disconnect and stop calls live in `finally`
or deferred blocks that no error path can skip.

## Check your understanding

1. Cleanup runs in a `finally` or deferred block rather than after the last success line. Which
   failure would leak a Copilot process if it ran after that line instead?
2. Why does a blank response raise an error instead of being handed to the validator, which would
   have reported missing sections anyway?
3. The entrypoint no longer builds the prompt. What did the service gain by owning that call?

Continue to [Run and review the exhibit](museum-06-run-review.md).
