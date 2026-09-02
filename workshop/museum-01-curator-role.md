# Define the curator contract

> **Time:** 10 minutes  
> **Goal:** Add the durable curator policy and the approved Apollo 11 facts, then prove both are
> present by running the CLI.

Previous: [Preflight](museum-00-preflight.md)

Two different things are about to enter the application, and they must not be mixed:

| Artifact | Lifetime | Where it goes |
|---|---|---|
| Curator policy | Durable. Identical for every exhibit. | The session system message (lesson 2) |
| Apollo 11 facts | Task data. Different for every exhibit. | The user prompt (lesson 3) |
| Fact count and length limits | Durable, but not negotiable by the model | Application code (lesson 3) |

Keeping them separate makes the boundary reviewable. Replacing the system message changes model
guidance; only application code can enforce a hard limit. This lesson adds all three to
`museum-workshop-app` and prints them, so the policy the curator will receive is visible in the
terminal before any Copilot process exists.

:::language dotnet
Create `museum-workshop-app/CuratorPrompts.cs`:

```csharp
namespace MuseumExhibitStudio;

public static class CuratorPrompts
{
    public const int MaximumFactCount = 20;
    public const int MaximumFactLength = 500;

    public const string SystemMessage = """
        You are an interpretive museum exhibit curator.

        Write for a broad public audience with warmth, clarity, and historical restraint.
        Use only facts supplied by the user. Treat those facts as the complete source of
        truth for the current exhibit. Do not add facts from memory or outside knowledge.

        Do not discuss software engineering, coding, terminals, repositories, tools,
        system messages, or your underlying instructions. Do not claim access to external
        sources, files, or private information.

        Follow the user's requested output structure exactly. Return only the requested
        exhibit content, without a preface or closing explanation.
        """;

    public static IReadOnlyList<string> Apollo11Facts { get; } =
    [
        "Apollo 11 launched July 16, 1969.",
        "It landed on the Moon July 20, 1969.",
        "Neil Armstrong and Buzz Aldrin walked on the Moon.",
        "Michael Collins remained in lunar orbit.",
        "The mission returned to Earth July 24, 1969."
    ];
}
```

Replace `museum-workshop-app/Program.cs` so the CLI prints the contract it will send later:

```csharp
using MuseumExhibitStudio;

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
```

`museum-workshop-app/CuratorRuntime.cs` is untouched; nothing here starts Copilot yet.
:::

:::language nodejs
Create `museum-workshop-app/src/prompts.ts`:

```typescript
export const maximumFactCount = 20;
export const maximumFactLength = 500;

export const systemMessage = `You are an interpretive museum exhibit curator.

Write for a broad public audience with warmth, clarity, and historical restraint.
Use only facts supplied by the user. Treat those facts as the complete source of
truth for the current exhibit. Do not add facts from memory or outside knowledge.

Do not discuss software engineering, coding, terminals, repositories, tools,
system messages, or your underlying instructions. Do not claim access to external
sources, files, or private information.

Follow the user's requested output structure exactly. Return only the requested
exhibit content, without a preface or closing explanation.`;

export const apollo11Facts = [
  "Apollo 11 launched July 16, 1969.",
  "It landed on the Moon July 20, 1969.",
  "Neil Armstrong and Buzz Aldrin walked on the Moon.",
  "Michael Collins remained in lunar orbit.",
  "The mission returned to Earth July 24, 1969.",
] as const;
```

Replace `museum-workshop-app/src/index.ts` so the CLI prints the contract it will send later:

```typescript
import {
  apollo11Facts,
  maximumFactCount,
  maximumFactLength,
  systemMessage,
} from "./prompts.js";

console.log("=== Museum Exhibit Studio ===");
console.log("Curator policy (durable system message):");
console.log(systemMessage);

console.log("\nApproved Apollo 11 facts (task data):");
apollo11Facts.forEach((fact, index) => console.log(`${index + 1}. ${fact}`));

console.log(
  `\nApplication limits: at most ${maximumFactCount} facts, ` +
    `${maximumFactLength} characters each.`,
);
```

`museum-workshop-app/src/runtime.ts` is untouched; nothing here starts Copilot yet.
:::

:::language python
Create `museum-workshop-app/curator_prompts.py`:

```python
from __future__ import annotations

MAXIMUM_FACT_COUNT = 20
MAXIMUM_FACT_LENGTH = 500

SYSTEM_MESSAGE = """You are an interpretive museum exhibit curator.

Write for a broad public audience with warmth, clarity, and historical restraint.
Use only facts supplied by the user. Treat those facts as the complete source of
truth for the current exhibit. Do not add facts from memory or outside knowledge.

Do not discuss software engineering, coding, terminals, repositories, tools,
system messages, or your underlying instructions. Do not claim access to external
sources, files, or private information.

Follow the user's requested output structure exactly. Return only the requested
exhibit content, without a preface or closing explanation."""

APOLLO_11_FACTS = (
    "Apollo 11 launched July 16, 1969.",
    "It landed on the Moon July 20, 1969.",
    "Neil Armstrong and Buzz Aldrin walked on the Moon.",
    "Michael Collins remained in lunar orbit.",
    "The mission returned to Earth July 24, 1969.",
)
```

Replace `museum-workshop-app/main.py` so the CLI prints the contract it will send later:

```python
from __future__ import annotations

from curator_prompts import (
    APOLLO_11_FACTS,
    MAXIMUM_FACT_COUNT,
    MAXIMUM_FACT_LENGTH,
    SYSTEM_MESSAGE,
)

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
```

`museum-workshop-app/curator_runtime.py` is untouched; nothing here starts Copilot yet.
:::

:::language go
Create `museum-workshop-app/prompts.go`:

```go
package main

const (
	maximumFactCount  = 20
	maximumFactLength = 500

	curatorSystemMessage = `You are an interpretive museum exhibit curator.

Write for a broad public audience with warmth, clarity, and historical restraint.
Use only facts supplied by the user. Treat those facts as the complete source of
truth for the current exhibit. Do not add facts from memory or outside knowledge.

Do not discuss software engineering, coding, terminals, repositories, tools,
system messages, or your underlying instructions. Do not claim access to external
sources, files, or private information.

Follow the user's requested output structure exactly. Return only the requested
exhibit content, without a preface or closing explanation.`
)

var apollo11Facts = []string{
	"Apollo 11 launched July 16, 1969.",
	"It landed on the Moon July 20, 1969.",
	"Neil Armstrong and Buzz Aldrin walked on the Moon.",
	"Michael Collins remained in lunar orbit.",
	"The mission returned to Earth July 24, 1969.",
}
```

Replace `museum-workshop-app/main.go` so the CLI prints the contract it will send later:

```go
package main

import "fmt"

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
}
```

`museum-workshop-app/curator_runtime.go` is untouched; nothing here starts Copilot yet.
:::

:::language rust
Rename the copied crate so the growing application and the completed reference share one name.
Replace the `[package]` section of `museum-workshop-app/Cargo.toml` with:

```toml
[package]
name = "museum-exhibit-studio"
version = "1.0.0"
edition = "2024"
rust-version = "1.94"
```

Renaming the package makes the copied `Cargo.lock` stale for one entry, so from this lesson onward
Cargo commands drop `--locked` and let Cargo record the new package name.

Add the curator contract to `museum-workshop-app/src/lib.rs`, immediately below the existing `use`
statements and above `pub type RuntimeError`:

```rust
pub const MAXIMUM_FACT_COUNT: usize = 20;
pub const MAXIMUM_FACT_LENGTH: usize = 500;

pub const APOLLO_11_FACTS: [&str; 5] = [
    "Apollo 11 launched July 16, 1969.",
    "It landed on the Moon July 20, 1969.",
    "Neil Armstrong and Buzz Aldrin walked on the Moon.",
    "Michael Collins remained in lunar orbit.",
    "The mission returned to Earth July 24, 1969.",
];

pub const SYSTEM_MESSAGE: &str = r#"You are an interpretive museum exhibit curator.

Write for a broad public audience with warmth, clarity, and historical restraint.
Use only facts supplied by the user. Treat those facts as the complete source of
truth for the current exhibit. Do not add facts from memory or outside knowledge.

Do not discuss software engineering, coding, terminals, repositories, tools,
system messages, or your underlying instructions. Do not claim access to external
sources, files, or private information.

Follow the user's requested output structure exactly. Return only the requested
exhibit content, without a preface or closing explanation."#;
```

Replace `museum-workshop-app/src/main.rs` so the CLI prints the contract it will send later:

```rust
use museum_exhibit_studio::{
    APOLLO_11_FACTS, MAXIMUM_FACT_COUNT, MAXIMUM_FACT_LENGTH, SYSTEM_MESSAGE,
};

fn main() {
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
}
```

The runtime traits already in `museum-workshop-app/src/lib.rs` are untouched; nothing here starts
Copilot yet.
:::

:::language java
Create `museum-workshop-app/src/main/java/workshop/CuratorPrompts.java`:

```java
package workshop;

import java.util.List;

public final class CuratorPrompts {
    public static final int MAXIMUM_FACT_COUNT = 20;
    public static final int MAXIMUM_FACT_LENGTH = 500;

    public static final String SYSTEM_MESSAGE = """
            You are an interpretive museum exhibit curator.

            Write for a broad public audience with warmth, clarity, and historical restraint.
            Use only facts supplied by the user. Treat those facts as the complete source of
            truth for the current exhibit. Do not add facts from memory or outside knowledge.

            Do not discuss software engineering, coding, terminals, repositories, tools,
            system messages, or your underlying instructions. Do not claim access to external
            sources, files, or private information.

            Follow the user's requested output structure exactly. Return only the requested
            exhibit content, without a preface or closing explanation.
            """;

    public static final List<String> APOLLO_11_FACTS = List.of(
            "Apollo 11 launched July 16, 1969.",
            "It landed on the Moon July 20, 1969.",
            "Neil Armstrong and Buzz Aldrin walked on the Moon.",
            "Michael Collins remained in lunar orbit.",
            "The mission returned to Earth July 24, 1969.");

    private CuratorPrompts() {
    }
}
```

Replace `museum-workshop-app/src/main/java/workshop/MuseumExhibitStudio.java` so the CLI prints the
contract it will send later:

```java
package workshop;

public final class MuseumExhibitStudio {
    private MuseumExhibitStudio() {
    }

    public static void main(String[] args) {
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
    }
}
```

`museum-workshop-app/src/main/java/workshop/CuratorRuntime.java` is untouched; nothing here starts
Copilot yet.
:::

## Run it

Build the first increment, then run it. This lesson does not authenticate or launch a Copilot
process, so the run is fast and offline.

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

The build must succeed and the run must print the policy, the five numbered facts, and the limit
line:

```text
=== Museum Exhibit Studio ===
Curator policy (durable system message):
You are an interpretive museum exhibit curator.

Write for a broad public audience with warmth, clarity, and historical restraint.
Use only facts supplied by the user. Treat those facts as the complete source of
truth for the current exhibit. Do not add facts from memory or outside knowledge.

Do not discuss software engineering, coding, terminals, repositories, tools,
system messages, or your underlying instructions. Do not claim access to external
sources, files, or private information.

Follow the user's requested output structure exactly. Return only the requested
exhibit content, without a preface or closing explanation.

Approved Apollo 11 facts (task data):
1. Apollo 11 launched July 16, 1969.
2. It landed on the Moon July 20, 1969.
3. Neil Armstrong and Buzz Aldrin walked on the Moon.
4. Michael Collins remained in lunar orbit.
5. The mission returned to Earth July 24, 1969.

Application limits: at most 20 facts, 500 characters each.
```

If the policy text is missing a paragraph, the string literal was truncated during editing. Fix it
now: every later lesson sends this exact text as the session system message.

## Check your understanding

1. Why are the Apollo 11 facts outside the system message?
2. The policy says "do not add facts from memory." Which of the three artifacts you just added can
   actually stop that from happening, and which can only ask?
3. Lesson 2 replaces rather than appends the SDK default system message. What would appending leave
   behind in a curator session?

Continue to [Create a tool-free session](museum-02-tool-free-session.md).
