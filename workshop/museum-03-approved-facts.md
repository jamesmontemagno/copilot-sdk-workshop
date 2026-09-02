# Ground the exhibit in approved facts

> **Time:** 15 minutes
> **Goal:** Build the bounded user prompt from approved facts, print it before it is sent, and
> generate the first real exhibit draft.

Previous: [Create a tool-free session](museum-02-tool-free-session.md)

The curator now has a policy and no tools. It still has no material. This lesson adds the prompt
builder that turns approved facts into the single user message the session receives.

The builder is application code, not guidance, so it enforces what the model cannot be trusted to
respect:

| Rule | Enforced by |
|---|---|
| At least one approved fact | Rejects an empty list before the session is created |
| At most 20 facts | Rejects an oversized list before the session is created |
| At most 500 characters per fact | Rejects an oversized fact before the session is created |
| Blank facts are dropped | Trimmed and filtered while building the list |
| Fixed output structure | Written into the prompt as an exact template |

The prompt also repeats the grounding rule in task terms, and the CLI prints the finished prompt
before sending it, so nothing reaches the model that you have not seen in your terminal.

:::language dotnet
Add this method inside `CuratorPrompts` in `museum-workshop-app/CuratorPrompts.cs`, after the
`Apollo11Facts` property:

```csharp
    public static string BuildExhibitPrompt(IEnumerable<string> approvedFacts)
    {
        ArgumentNullException.ThrowIfNull(approvedFacts);

        var facts = approvedFacts
            .Select(fact => fact?.Trim())
            .Where(fact => !string.IsNullOrWhiteSpace(fact))
            .Cast<string>()
            .ToArray();

        if (facts.Length == 0)
        {
            throw new ArgumentException("Provide at least one approved fact.", nameof(approvedFacts));
        }

        if (facts.Length > MaximumFactCount)
        {
            throw new ArgumentException(
                $"Provide no more than {MaximumFactCount} approved facts.",
                nameof(approvedFacts));
        }

        if (facts.Any(fact => fact.Length > MaximumFactLength))
        {
            throw new ArgumentException(
                $"Each approved fact must be {MaximumFactLength} characters or fewer.",
                nameof(approvedFacts));
        }

        var factList = string.Join(Environment.NewLine, facts.Select(fact => $"- {fact}"));

        return $"""
            Create visitor-facing exhibit text about Apollo 11 using only these supplied facts:

            {factList}

            Return exactly this structure:

            # <an engaging exhibit title>
            ## Narrative
            <100-140 words, excluding the title and questions>
            ## Visitor questions
            1. <question>
            2. <question>
            3. <question>

            Write exactly three distinct visitor reflection questions. Do not add a preface,
            conclusion, software discussion, or facts not supplied above. Do not inspect the
            filesystem or use tools.
            """;
    }
```

Replace `museum-workshop-app/Program.cs`:

```csharp
using MuseumExhibitStudio;

Console.WriteLine("=== Museum Exhibit Studio ===");
Console.WriteLine("Curator policy: replace-mode system message, no tools allowed.");
Console.WriteLine("Approved Apollo 11 facts:");
for (var index = 0; index < CuratorPrompts.Apollo11Facts.Count; index++)
{
    Console.WriteLine($"{index + 1}. {CuratorPrompts.Apollo11Facts[index]}");
}

var prompt = CuratorPrompts.BuildExhibitPrompt(CuratorPrompts.Apollo11Facts);
Console.WriteLine(
    $"\nBounded prompt (at most {CuratorPrompts.MaximumFactCount} facts, " +
    $"{CuratorPrompts.MaximumFactLength} characters each):");
Console.WriteLine("--------");
Console.WriteLine(prompt);
Console.WriteLine("--------");

await using var client = new CopilotCuratorClient();
await client.StartAsync();
try
{
    await using var session = await client.CreateSessionAsync(
        MuseumExhibitService.CreateSessionConfiguration(
            Environment.GetEnvironmentVariable("COPILOT_MODEL")));
    var content = await session.SendAndWaitAsync(prompt, TimeSpan.FromMinutes(2));
    Console.WriteLine($"\nExhibit draft:\n{content}");
}
finally
{
    await client.StopAsync();
}
```
:::

:::language nodejs
Append this function to `museum-workshop-app/src/prompts.ts`:

```typescript
export function buildExhibitPrompt(approvedFacts: Iterable<string>): string {
  const facts = [...approvedFacts].map((fact) => fact.trim()).filter(Boolean);
  if (facts.length === 0) throw new Error("Provide at least one approved fact.");
  if (facts.length > maximumFactCount) {
    throw new Error(`Provide no more than ${maximumFactCount} approved facts.`);
  }
  if (facts.some((fact) => fact.length > maximumFactLength)) {
    throw new Error(`Each approved fact must be ${maximumFactLength} characters or fewer.`);
  }

  return `Create visitor-facing exhibit text about Apollo 11 using only these supplied facts:

${facts.map((fact) => `- ${fact}`).join("\n")}

Return exactly this structure:

# <an engaging exhibit title>
## Narrative
<100-140 words, excluding the title and questions>
## Visitor questions
1. <question>
2. <question>
3. <question>

Write exactly three distinct visitor reflection questions. Do not add a preface,
conclusion, software discussion, or facts not supplied above. Do not inspect the
filesystem or use tools.`;
}
```

Replace `museum-workshop-app/src/index.ts`:

```typescript
import {
  apollo11Facts,
  buildExhibitPrompt,
  maximumFactCount,
  maximumFactLength,
} from "./prompts.js";
import {
  createCopilotCuratorClient,
  createSessionConfiguration,
  type CuratorSession,
} from "./service.js";

console.log("=== Museum Exhibit Studio ===");
console.log("Curator policy: replace-mode system message, no tools allowed.");
console.log("Approved Apollo 11 facts:");
apollo11Facts.forEach((fact, index) => console.log(`${index + 1}. ${fact}`));

const prompt = buildExhibitPrompt(apollo11Facts);
console.log(
  `\nBounded prompt (at most ${maximumFactCount} facts, ` +
    `${maximumFactLength} characters each):`,
);
console.log("--------");
console.log(prompt);
console.log("--------");

const client = createCopilotCuratorClient();
let session: CuratorSession | undefined;
await client.start();
try {
  session = await client.createSession(
    createSessionConfiguration(process.env.COPILOT_MODEL),
  );
  const response = await session.sendAndWait(prompt, 120_000);
  console.log(`\nExhibit draft:\n${response?.data.content ?? ""}`);
} finally {
  await session?.disconnect();
  await client.stop();
}
```
:::

:::language python
Append this function to `museum-workshop-app/curator_prompts.py`, and add
`from collections.abc import Iterable` below the existing `from __future__` line:

```python
def build_exhibit_prompt(approved_facts: Iterable[str]) -> str:
    facts = tuple(fact.strip() for fact in approved_facts if fact and fact.strip())
    if not facts:
        raise ValueError("Provide at least one approved fact.")
    if len(facts) > MAXIMUM_FACT_COUNT:
        raise ValueError(
            f"Provide no more than {MAXIMUM_FACT_COUNT} approved facts."
        )
    if any(len(fact) > MAXIMUM_FACT_LENGTH for fact in facts):
        raise ValueError(
            f"Each approved fact must be {MAXIMUM_FACT_LENGTH} characters or fewer."
        )

    fact_list = "\n".join(f"- {fact}" for fact in facts)
    return f"""Create visitor-facing exhibit text about Apollo 11 using only these supplied facts:

{fact_list}

Return exactly this structure:

# <an engaging exhibit title>
## Narrative
<100-140 words, excluding the title and questions>
## Visitor questions
1. <question>
2. <question>
3. <question>

Write exactly three distinct visitor reflection questions. Do not add a preface,
conclusion, software discussion, or facts not supplied above. Do not inspect the
filesystem or use tools."""
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
    build_exhibit_prompt,
)
from museum_exhibit_service import create_session_configuration


async def main() -> None:
    print("=== Museum Exhibit Studio ===")
    print("Curator policy: replace-mode system message, no tools allowed.")
    print("Approved Apollo 11 facts:")
    for index, fact in enumerate(APOLLO_11_FACTS, start=1):
        print(f"{index}. {fact}")

    prompt = build_exhibit_prompt(APOLLO_11_FACTS)
    print(
        f"\nBounded prompt (at most {MAXIMUM_FACT_COUNT} facts, "
        f"{MAXIMUM_FACT_LENGTH} characters each):"
    )
    print("--------")
    print(prompt)
    print("--------")

    client = CopilotClient()
    session = None
    await client.start()
    try:
        session = await client.create_session(
            **create_session_configuration(os.getenv("COPILOT_MODEL"))
        )
        response = await session.send_and_wait(prompt, timeout=120.0)
        print(f"\nExhibit draft:\n{response.data.content}")
    finally:
        if session is not None:
            await session.disconnect()
        await client.stop()


if __name__ == "__main__":
    asyncio.run(main())
```
:::

:::language go
Insert this import block into `museum-workshop-app/prompts.go`, between `package main` and the
existing `const` block:

```go
import (
	"fmt"
	"strings"
)
```

Then append this function to the end of the same file:

```go
func buildExhibitPrompt(approvedFacts []string) (string, error) {
	facts := make([]string, 0, len(approvedFacts))
	for _, fact := range approvedFacts {
		if fact = strings.TrimSpace(fact); fact != "" {
			facts = append(facts, fact)
		}
	}
	if len(facts) == 0 {
		return "", fmt.Errorf("provide at least one approved fact")
	}
	if len(facts) > maximumFactCount {
		return "", fmt.Errorf("provide no more than %d approved facts", maximumFactCount)
	}
	for _, fact := range facts {
		if len([]rune(fact)) > maximumFactLength {
			return "", fmt.Errorf("each approved fact must be %d characters or fewer", maximumFactLength)
		}
	}

	var factList strings.Builder
	for _, fact := range facts {
		fmt.Fprintf(&factList, "- %s\n", fact)
	}
	return fmt.Sprintf(`Create visitor-facing exhibit text about Apollo 11 using only these supplied facts:

%s
Return exactly this structure:

# <an engaging exhibit title>
## Narrative
<100-140 words, excluding the title and questions>
## Visitor questions
1. <question>
2. <question>
3. <question>

Write exactly three distinct visitor reflection questions. Do not add a preface,
conclusion, software discussion, or facts not supplied above. Do not inspect the
filesystem or use tools.`, factList.String()), nil
}
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

func main() {
	fmt.Println("=== Museum Exhibit Studio ===")
	fmt.Println("Curator policy: replace-mode system message, no tools allowed.")
	fmt.Println("Approved Apollo 11 facts:")
	for index, fact := range apollo11Facts {
		fmt.Printf("%d. %s\n", index+1, fact)
	}

	if err := draftExhibit(); err != nil {
		fmt.Fprintln(os.Stderr, "Could not generate the exhibit:", err)
		os.Exit(1)
	}
}

func draftExhibit() (err error) {
	prompt, err := buildExhibitPrompt(apollo11Facts)
	if err != nil {
		return err
	}
	fmt.Printf("\nBounded prompt (at most %d facts, %d characters each):\n",
		maximumFactCount, maximumFactLength)
	fmt.Println("--------")
	fmt.Println(prompt)
	fmt.Println("--------")

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

	generationContext, cancel := context.WithTimeout(ctx, 2*time.Minute)
	defer cancel()
	content, err := session.SendAndWait(generationContext, prompt)
	if err != nil {
		return err
	}
	fmt.Printf("\nExhibit draft:\n%s\n", content)
	return nil
}
```
:::

:::language rust
Add the prompt error type and builder to `museum-workshop-app/src/lib.rs`, directly below
`create_session_configuration`. Extend the standard-library imports at the top of the file with
`use std::fmt;`:

```rust
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PromptError(String);

impl fmt::Display for PromptError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str(&self.0)
    }
}

impl Error for PromptError {}

pub fn build_exhibit_prompt<I, S>(approved_facts: I) -> Result<String, PromptError>
where
    I: IntoIterator<Item = S>,
    S: AsRef<str>,
{
    let facts: Vec<String> = approved_facts
        .into_iter()
        .map(|fact| fact.as_ref().trim().to_owned())
        .filter(|fact| !fact.is_empty())
        .collect();

    if facts.is_empty() {
        return Err(PromptError(
            "Provide at least one approved fact.".to_owned(),
        ));
    }
    if facts.len() > MAXIMUM_FACT_COUNT {
        return Err(PromptError(format!(
            "Provide no more than {MAXIMUM_FACT_COUNT} approved facts."
        )));
    }
    if facts
        .iter()
        .any(|fact| fact.chars().count() > MAXIMUM_FACT_LENGTH)
    {
        return Err(PromptError(format!(
            "Each approved fact must be {MAXIMUM_FACT_LENGTH} characters or fewer."
        )));
    }

    let fact_list = facts
        .iter()
        .map(|fact| format!("- {fact}"))
        .collect::<Vec<_>>()
        .join("\n");
    Ok(format!(
        r#"Create visitor-facing exhibit text about Apollo 11 using only these supplied facts:

{fact_list}

Return exactly this structure:

# <an engaging exhibit title>
## Narrative
<100-140 words, excluding the title and questions>
## Visitor questions
1. <question>
2. <question>
3. <question>

Write exactly three distinct visitor reflection questions. Do not add a preface,
conclusion, software discussion, or facts not supplied above. Do not inspect the
filesystem or use tools."#
    ))
}
```

Replace `museum-workshop-app/src/main.rs`:

```rust
use std::time::Duration;

use museum_exhibit_studio::{
    APOLLO_11_FACTS, CopilotCuratorClient, CuratorClient, CuratorSession, MAXIMUM_FACT_COUNT,
    MAXIMUM_FACT_LENGTH, RuntimeError, build_exhibit_prompt, create_session_configuration,
};

async fn draft_exhibit() -> Result<(), RuntimeError> {
    let facts: Vec<String> = APOLLO_11_FACTS.map(str::to_owned).to_vec();
    let prompt = build_exhibit_prompt(&facts)?;
    println!(
        "\nBounded prompt (at most {MAXIMUM_FACT_COUNT} facts, \
         {MAXIMUM_FACT_LENGTH} characters each):"
    );
    println!("--------");
    println!("{prompt}");
    println!("--------");

    let mut client = CopilotCuratorClient::new();
    client.start().await?;
    let mut session = client
        .create_session(create_session_configuration(
            std::env::var("COPILOT_MODEL").ok().as_deref(),
        ))
        .await?;
    let content = session
        .send_and_wait(prompt, Duration::from_secs(120))
        .await;
    session.disconnect().await?;
    client.stop().await?;
    println!("\nExhibit draft:\n{}", content?.unwrap_or_default());
    Ok(())
}

#[tokio::main]
async fn main() {
    println!("=== Museum Exhibit Studio ===");
    println!("Curator policy: replace-mode system message, no tools allowed.");
    println!("Approved Apollo 11 facts:");
    for (index, fact) in APOLLO_11_FACTS.iter().enumerate() {
        println!("{}. {fact}", index + 1);
    }

    if let Err(error) = draft_exhibit().await {
        eprintln!("Could not generate the exhibit: {error}");
        std::process::exit(1);
    }
}
```
:::

:::language java
Add this method to `CuratorPrompts` in
`museum-workshop-app/src/main/java/workshop/CuratorPrompts.java`, and extend its imports with
`java.util.ArrayList` and `java.util.Objects`:

```java
    public static String buildExhibitPrompt(Iterable<String> approvedFacts) {
        Objects.requireNonNull(approvedFacts, "approvedFacts");
        List<String> facts = new ArrayList<>();
        for (String fact : approvedFacts) {
            if (fact != null && !fact.isBlank()) {
                facts.add(fact.trim());
            }
        }

        if (facts.isEmpty()) {
            throw new IllegalArgumentException("Provide at least one approved fact.");
        }
        if (facts.size() > MAXIMUM_FACT_COUNT) {
            throw new IllegalArgumentException(
                    "Provide no more than " + MAXIMUM_FACT_COUNT + " approved facts.");
        }
        if (facts.stream().anyMatch(fact -> fact.length() > MAXIMUM_FACT_LENGTH)) {
            throw new IllegalArgumentException(
                    "Each approved fact must be " + MAXIMUM_FACT_LENGTH + " characters or fewer.");
        }

        String factList = facts.stream()
                .map(fact -> "- " + fact)
                .reduce((left, right) -> left + System.lineSeparator() + right)
                .orElseThrow();
        return """
                Create visitor-facing exhibit text about Apollo 11 using only these supplied facts:

                %s

                Return exactly this structure:

                # <an engaging exhibit title>
                ## Narrative
                <100-140 words, excluding the title and questions>
                ## Visitor questions
                1. <question>
                2. <question>
                3. <question>

                Write exactly three distinct visitor reflection questions. Do not add a preface,
                conclusion, software discussion, or facts not supplied above. Do not inspect the
                filesystem or use tools.
                """.formatted(factList);
    }
```

Replace `museum-workshop-app/src/main/java/workshop/MuseumExhibitStudio.java`:

```java
package workshop;

public final class MuseumExhibitStudio {
    private MuseumExhibitStudio() {
    }

    public static void main(String[] args) throws Exception {
        System.out.println("=== Museum Exhibit Studio ===");
        System.out.println("Curator policy: replace-mode system message, no tools allowed.");
        System.out.println("Approved Apollo 11 facts:");
        for (int index = 0; index < CuratorPrompts.APOLLO_11_FACTS.size(); index++) {
            System.out.printf("%d. %s%n", index + 1, CuratorPrompts.APOLLO_11_FACTS.get(index));
        }

        String prompt = CuratorPrompts.buildExhibitPrompt(CuratorPrompts.APOLLO_11_FACTS);
        System.out.printf(
                "%nBounded prompt (at most %d facts, %d characters each):%n",
                CuratorPrompts.MAXIMUM_FACT_COUNT,
                CuratorPrompts.MAXIMUM_FACT_LENGTH);
        System.out.println("--------");
        System.out.println(prompt);
        System.out.println("--------");

        try (CuratorClient client = new CopilotCuratorClient()) {
            client.start();
            CuratorSession session = null;
            try {
                session = client.createSession(
                        MuseumExhibitService.createSessionConfiguration(
                                System.getenv("COPILOT_MODEL")));
                String content = session.sendAndWait(prompt, 120_000L);
                System.out.printf("%nExhibit draft:%n%s%n", content);
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

The run prints the exact prompt, then the first exhibit draft:

```text
=== Museum Exhibit Studio ===
Curator policy: replace-mode system message, no tools allowed.
Approved Apollo 11 facts:
1. Apollo 11 launched July 16, 1969.
2. It landed on the Moon July 20, 1969.
3. Neil Armstrong and Buzz Aldrin walked on the Moon.
4. Michael Collins remained in lunar orbit.
5. The mission returned to Earth July 24, 1969.

Bounded prompt (at most 20 facts, 500 characters each):
--------
Create visitor-facing exhibit text about Apollo 11 using only these supplied facts:

- Apollo 11 launched July 16, 1969.
- It landed on the Moon July 20, 1969.
- Neil Armstrong and Buzz Aldrin walked on the Moon.
- Michael Collins remained in lunar orbit.
- The mission returned to Earth July 24, 1969.

Return exactly this structure:

# <an engaging exhibit title>
## Narrative
<100-140 words, excluding the title and questions>
## Visitor questions
1. <question>
2. <question>
3. <question>

Write exactly three distinct visitor reflection questions. Do not add a preface,
conclusion, software discussion, or facts not supplied above. Do not inspect the
filesystem or use tools.
--------

Exhibit draft:
# Footprints Beyond Earth
## Narrative
On July 16, 1969, Apollo 11 rose from Earth...
## Visitor questions
1. What would you have packed for a journey to the Moon?
2. How would you describe the Moon to someone who has never seen it?
3. Who else must succeed for one person to take a first step?
```

The exhibit wording changes on every run. The prompt block above it must not: it is produced by
your code from the approved facts, and it is the only material the curator receives.

Read the draft closely. It very likely contains at least one plausible detail that is not in the
five approved facts, such as a spacecraft name, a crew role, or a quotation. Nothing in the
application has checked for that yet. Lesson 4 adds the checks a program can make, and lesson 6
makes the human review explicit.

## Check your understanding

1. The prompt already says "use only these supplied facts." Which of the five rules in the table
   above would still hold if the model ignored that sentence entirely?
2. Why does the builder run before the client is started rather than after the session exists?
3. The approved facts are passed in as an argument instead of being read inside the builder. Which
   later lesson depends on that?

Continue to [Validate the exhibit deterministically](museum-04-deterministic-validation.md).
