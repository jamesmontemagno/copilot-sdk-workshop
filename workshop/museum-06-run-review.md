# Run and review the exhibit

> **Time:** 10 minutes
> **Goal:** Turn the demonstration entrypoint into the interactive CLI an educator would actually
> use, then perform the review that no automated check can perform for you.

Previous: [Own the lifecycle](museum-05-lifecycle.md)

The application now has a policy, a bounded prompt, a deterministic validator, and an enforced
lifecycle. What it does not have is a person in the loop. This lesson adds two things:

1. **An interactive entrypoint.** The educator sees the approved facts, keeps them or types their
   own set, and gets the exhibit plus its structural result.
2. **A review step.** Every claim in the generated narrative is compared against the approved facts
   by a human, because that is the only control in the whole application that can catch a fabricated
   detail.

The entrypoint stops printing diagnostics from earlier lessons. Everything it prints is now
something an educator needs.

:::language dotnet
Replace `museum-workshop-app/Program.cs`:

```csharp
using MuseumExhibitStudio;

Console.WriteLine("=== Museum Exhibit Studio ===");
Console.WriteLine("Approved Apollo 11 facts:");

for (var index = 0; index < CuratorPrompts.Apollo11Facts.Count; index++)
{
    Console.WriteLine($"{index + 1}. {CuratorPrompts.Apollo11Facts[index]}");
}

Console.Write("\nUse these facts? [Y/n]: ");
var useDefaults = Console.ReadLine()?.Trim();
var facts = useDefaults?.Equals("n", StringComparison.OrdinalIgnoreCase) == true
    ? ReadFacts()
    : CuratorPrompts.Apollo11Facts;

await using var client = new CopilotCuratorClient();
var studio = new MuseumExhibitService(client);

try
{
    var result = await studio.GenerateAsync(
        facts,
        Environment.GetEnvironmentVariable("COPILOT_MODEL"));
    Console.WriteLine($"\n{result.Content}\n");
    PrintValidation(result.Validation);
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

static IReadOnlyList<string> ReadFacts()
{
    Console.WriteLine("Enter one approved fact per line. Submit a blank line when finished:");
    var facts = new List<string>();

    while (true)
    {
        var fact = Console.ReadLine();
        if (string.IsNullOrWhiteSpace(fact))
        {
            return facts;
        }

        facts.Add(fact.Trim());
    }
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

An empty fact list from `ReadFacts` is not a special case here: `BuildExhibitPrompt` rejects it
inside `GenerateAsync`, and the catch block reports it before any session is created.
:::

:::language nodejs
Replace `museum-workshop-app/src/index.ts`:

```typescript
import { createInterface } from "node:readline/promises";
import { stdin as input, stdout as output } from "node:process";
import { apollo11Facts } from "./prompts.js";
import { createCopilotCuratorClient, MuseumExhibitService } from "./service.js";
import type { ExhibitValidation } from "./validator.js";

const terminal = createInterface({ input, output });

try {
  console.log("=== Museum Exhibit Studio ===");
  console.log("Approved Apollo 11 facts:");
  apollo11Facts.forEach((fact, index) => console.log(`${index + 1}. ${fact}`));

  const answer = (await terminal.question("\nUse these facts? [Y/n]: ")).trim();
  const facts = answer.toLocaleLowerCase() === "n" ? await readFacts() : apollo11Facts;

  const result = await new MuseumExhibitService(createCopilotCuratorClient())
    .generate(facts, process.env.COPILOT_MODEL);

  console.log(`\n${result.content}\n`);
  printValidation(result.validation);
} catch (error) {
  const message = error instanceof Error ? error.message : String(error);
  console.error(message.toLocaleLowerCase().includes("timeout")
    ? "The curator did not respond within two minutes. Try again."
    : `Could not generate the exhibit: ${message}`);
  process.exitCode = 1;
} finally {
  terminal.close();
}

async function readFacts(): Promise<string[]> {
  console.log("Enter one approved fact per line. Submit a blank line when finished:");
  const facts: string[] = [];
  while (true) {
    const fact = (await terminal.question("")).trim();
    if (!fact) return facts;
    facts.push(fact);
  }
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

The `finally` block closes the terminal on every path, so a failed run does not leave the shell
waiting for input.
:::

:::language python
Replace `museum-workshop-app/main.py`:

```python
from __future__ import annotations

import asyncio
import os
import sys

from copilot import CopilotClient

from curator_prompts import APOLLO_11_FACTS
from exhibit_validator import ExhibitValidation
from museum_exhibit_service import MuseumExhibitService

GROUNDING_DISCLAIMER = (
    "Structural checks do not prove factual grounding. "
    "Unsupported claims require human review or a separate evaluator."
)


def read_facts() -> list[str]:
    print("Enter one approved fact per line. Submit a blank line when finished:")
    facts: list[str] = []
    while fact := input().strip():
        facts.append(fact)
    return facts


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

    use_defaults = input("\nUse these facts? [Y/n]: ").strip()
    facts = read_facts() if use_defaults.casefold() == "n" else list(APOLLO_11_FACTS)

    try:
        studio = MuseumExhibitService(CopilotClient())
        result = await studio.generate(facts, os.getenv("COPILOT_MODEL"))
        print(f"\n{result.content}\n")
        print_validation(result.validation)
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

An empty fact list from `read_facts` is not a special case here: `build_exhibit_prompt` rejects it
inside `generate`, and the `except` block reports it before any session is created.
:::

:::language go
Replace `museum-workshop-app/main.go`:

```go
package main

import (
	"bufio"
	"context"
	"errors"
	"fmt"
	"os"
	"strings"
)

func main() {
	if err := runCLI(bufio.NewReader(os.Stdin)); err != nil {
		fmt.Fprintln(os.Stderr, "Could not generate the exhibit:", err)
		os.Exit(1)
	}
}

func runCLI(input *bufio.Reader) error {
	fmt.Println("=== Museum Exhibit Studio ===")
	fmt.Println("Approved Apollo 11 facts:")
	for index, fact := range apollo11Facts {
		fmt.Printf("%d. %s\n", index+1, fact)
	}

	fmt.Print("\nUse these facts? [Y/n]: ")
	answer, _ := input.ReadString('\n')
	facts := append([]string(nil), apollo11Facts...)
	if strings.EqualFold(strings.TrimSpace(answer), "n") {
		facts = readFacts(input)
	}

	result, err := (museumExhibitService{client: newCopilotCuratorClient()}).Generate(
		context.Background(),
		facts,
		os.Getenv("COPILOT_MODEL"),
	)
	if err != nil {
		if errorsIsDeadline(err) {
			return fmt.Errorf("the curator did not respond within two minutes; try again")
		}
		return err
	}
	fmt.Printf("\n%s\n\n", result.Content)
	printValidation(result.Validation)
	return nil
}

func errorsIsDeadline(err error) bool {
	return errors.Is(err, context.DeadlineExceeded)
}

func readFacts(input *bufio.Reader) []string {
	fmt.Println("Enter one approved fact per line. Submit a blank line when finished:")
	var facts []string
	for {
		fact, err := input.ReadString('\n')
		fact = strings.TrimSpace(fact)
		if fact != "" {
			facts = append(facts, fact)
		}
		if fact == "" || err != nil {
			return facts
		}
	}
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

An empty fact list from `readFacts` is not a special case here: `buildExhibitPrompt` rejects it
inside `Generate`, and `runCLI` reports it before any session is created.
:::

:::language rust
Replace `museum-workshop-app/src/main.rs`:

```rust
use std::io::{self, Write};

use museum_exhibit_studio::{
    APOLLO_11_FACTS, CopilotCuratorClient, ExhibitValidation, RuntimeError, build_exhibit_prompt,
    generate_exhibit, is_timeout_error,
};

fn read_facts() -> io::Result<Vec<String>> {
    println!("Enter one approved fact per line. Submit a blank line when finished:");
    let mut facts = Vec::new();
    loop {
        let mut fact = String::new();
        io::stdin().read_line(&mut fact)?;
        let fact = fact.trim();
        if fact.is_empty() {
            return Ok(facts);
        }
        facts.push(fact.to_owned());
    }
}

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

    print!("\nUse these facts? [Y/n]: ");
    io::stdout().flush()?;
    let mut choice = String::new();
    io::stdin().read_line(&mut choice)?;
    let facts = if choice.trim().eq_ignore_ascii_case("n") {
        read_facts()?
    } else {
        APOLLO_11_FACTS.map(str::to_owned).to_vec()
    };
    build_exhibit_prompt(&facts)?;

    let model = std::env::var("COPILOT_MODEL").ok();
    let mut client = CopilotCuratorClient::new();
    let result = generate_exhibit(&mut client, &facts, model.as_deref()).await?;
    println!("\n{}\n", result.content);
    print_validation(&result.validation);
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

`build_exhibit_prompt(&facts)?` runs before the client is created, so an empty or oversized fact
set fails immediately instead of starting a Copilot process.
:::

:::language java
Replace `museum-workshop-app/src/main/java/workshop/MuseumExhibitStudio.java`:

```java
package workshop;

import java.util.ArrayList;
import java.util.List;
import java.util.Scanner;
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

        Scanner input = new Scanner(System.in);
        System.out.print("\nUse these facts? [Y/n]: ");
        String choice = input.hasNextLine() ? input.nextLine().trim() : "";
        List<String> facts = choice.equalsIgnoreCase("n")
                ? readFacts(input)
                : CuratorPrompts.APOLLO_11_FACTS;

        try (var generationClient = new CopilotCuratorClient()) {
            var studio = new MuseumExhibitService(generationClient);
            var result = studio.generate(facts, System.getenv("COPILOT_MODEL"));
            System.out.printf("%n%s%n%n", result.content());
            printValidation(result.validation());
        } catch (Exception exception) {
            if (hasCause(exception, TimeoutException.class)) {
                System.err.println("The curator did not respond within two minutes. Try again.");
            } else {
                System.err.println("Could not generate the exhibit: " + rootMessage(exception));
            }
            System.exit(1);
        }
    }

    private static List<String> readFacts(Scanner input) {
        System.out.println("Enter one approved fact per line. Submit a blank line when finished:");
        List<String> facts = new ArrayList<>();
        while (input.hasNextLine()) {
            String fact = input.nextLine();
            if (fact.isBlank()) {
                break;
            }
            facts.add(fact.trim());
        }
        return facts;
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

An empty fact list from `readFacts` is not a special case here: `buildExhibitPrompt` rejects it
inside `generate`, and the catch block reports it before any session is created.
:::

## Run it

Build, then run interactively. Answer `Y` at the first prompt to keep the Apollo 11 facts.

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

A complete session looks like this:

```text
=== Museum Exhibit Studio ===
Approved Apollo 11 facts:
1. Apollo 11 launched July 16, 1969.
2. It landed on the Moon July 20, 1969.
3. Neil Armstrong and Buzz Aldrin walked on the Moon.
4. Michael Collins remained in lunar orbit.
5. The mission returned to Earth July 24, 1969.

Use these facts? [Y/n]: Y

# Footprints Beyond Earth
## Narrative
On July 16, 1969, Apollo 11 climbed away from Earth carrying three travelers toward a
destination no one had ever touched. Four days later, on July 20, the landing craft settled
onto the Moon. Neil Armstrong and Buzz Aldrin stepped onto that gray, silent ground while
Michael Collins circled overhead in lunar orbit, alone above a world of craters. On July 24
the mission came home, returning to Earth with something no expedition had brought back
before: the memory of standing somewhere else. The journey lasted eight days. What it
changed has lasted far longer, and it began with a single launch on a summer morning.
## Visitor questions
1. What would you have wanted to see first from lunar orbit?
2. How does it change the story to know one crew member never landed?
3. What journey today feels as far away as the Moon did in 1969?

Structural checks passed.
- One level-one title: true
- Narrative section: true
- Narrative length: 118 words (within 100-140: true)
- Visitor questions section: true
- Numbered questions: 3 (exactly three: true)
- Every item is a question: true

Structural checks do not prove factual grounding. Unsupported claims require human review
or a separate evaluator.
```

Run it again and answer `n` at the prompt. Enter two or three facts of your own, then a blank line.
The exhibit follows your facts instead of Apollo 11's, which confirms that the approved facts are
task data and not part of the durable policy.

Then run it once more, answer `n`, and press Enter immediately. Generation never starts:

```text
Could not generate the exhibit: Provide at least one approved fact.
```

## Manual factual review

Take the narrative from your own run and check it line by line against the five approved facts. The
example above survives that review: every date, name, and role in it traces back to a supplied fact,
and the interpretive language ("gray, silent ground", "a summer morning") adds tone rather than
claims.

Now look for the failures the validator cannot see. A generated narrative might say:

```text
Aboard the command module Columbia, Michael Collins circled the Moon while Eagle descended
with Armstrong and Aldrin, who planted the flag and collected 47 pounds of lunar rock.
```

Every structural check still passes. But `Columbia`, `Eagle`, the flag, and the mass of returned
material are nowhere in the approved facts. They may be historically accurate, and that is exactly
the problem: an unverified claim that happens to be true is indistinguishable, from inside the
application, from one that is not.

Work through this checklist on your run:

1. Underline every proper noun, number, and date in the narrative.
2. Match each one to a specific approved fact.
3. Mark anything unmatched, whether or not you believe it.
4. Decide, as the educator, to remove the claim or to add it to the approved facts and regenerate.
5. Check that the three visitor questions ask something rather than assert something.

That is the loop the application is built to support: the model drafts, the code bounds and checks,
and the human decides. Lesson 7 adds a bounded research stage so that step 4 can be done with cited
sources instead of memory, while keeping the human approval requirement in place.

## Check your understanding

1. The structural result says `Structural checks passed.` and the narrative names the command
   module. Which of the two statements is wrong, and which control is responsible for catching it?
2. The educator can type arbitrary facts at the prompt. Which application-level rules still apply to
   that input, and where do they run?
3. Why does the CLI print the grounding disclaimer on every run, including successful ones?

Continue to [Wikipedia MCP](museum-07-wikipedia-grounding.md).
