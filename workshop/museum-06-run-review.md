# Run and review the exhibit

> **Time:** 15 minutes  
> **Goal:** Add the CLI, generate with authenticated Copilot, and review every factual claim.

The CLI is the final application boundary: it collects approved facts, creates the production SDK
adapter, reports deterministic checks, and clearly labels what still needs human review.

:::language dotnet
Create `museum-workshop-app/Program.cs`:

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
    var result = await studio.GenerateAsync(facts, Environment.GetEnvironmentVariable("COPILOT_MODEL"));
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
:::

:::language nodejs
Create `museum-workshop-app/src/index.ts`:

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
  const studio = new MuseumExhibitService(createCopilotCuratorClient());
  const result = await studio.generate(facts, process.env.COPILOT_MODEL);

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
:::

:::language python
Create `museum-workshop-app/main.py`:

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
    studio = MuseumExhibitService(CopilotClient())
    try:
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
:::

:::language go
Create `museum-workshop-app/main.go`:

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
:::

:::language rust
Create `museum-workshop-app/src/main.rs`:

```rust
use std::io::{self, Write};

use museum_exhibit_studio::{
    APOLLO_11_FACTS, CopilotCuratorClient, ExhibitValidation, generate_exhibit,
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

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
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

    let model = std::env::var("COPILOT_MODEL").ok();
    let mut client = CopilotCuratorClient::new();
    match generate_exhibit(&mut client, &facts, model.as_deref()).await {
        Ok(result) => {
            println!("\n{}\n", result.content);
            print_validation(&result.validation);
            Ok(())
        }
        Err(error) => {
            eprintln!("Could not generate the exhibit: {error}");
            Err(error)
        }
    }
}
```
:::

:::language java
Create `museum-workshop-app/src/main/java/workshop/MuseumExhibitStudio.java`:

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

        try (var client = new CopilotCuratorClient()) {
            var studio = new MuseumExhibitService(client);
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
        System.out.printf("- Narrative length: %d words (within 100-140: %s)%n",
                validation.narrative().wordCount(), validation.narrative().withinLimit());
        System.out.println("- Visitor questions section: " + validation.visitorQuestions().present());
        System.out.printf("- Numbered questions: %d (exactly three: %s)%n",
                validation.visitorQuestions().questionCount(),
                validation.visitorQuestions().exactlyThree());
        System.out.println("- Every item is a question: "
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
        return current.getMessage() == null ? current.getClass().getSimpleName() : current.getMessage();
    }
}
```
:::

## Run it

Use an authenticated Copilot CLI. Press Enter to accept the five default facts. Set
`COPILOT_MODEL` first only if you want a specific model.

:::language dotnet
```bash
dotnet run --project museum-workshop-app
```
:::
:::language nodejs
```bash
npm --prefix museum-workshop-app start
```
:::
:::language python
```bash
PYTHONPATH=museum-workshop-app museum-workshop-app/.venv/bin/python museum-workshop-app/main.py
```
:::
:::language go
```bash
go -C museum-workshop-app run .
```
:::
:::language rust
```bash
cargo run --manifest-path museum-workshop-app/Cargo.toml --locked
```
:::
:::language java
```bash
mvn -f museum-workshop-app/pom.xml compile exec:java
```
:::

Prose varies, but a successful run resembles:

```text
# Footprints Beyond Earth
## Narrative
<100-140 words based only on the five supplied facts>
## Visitor questions
1. ...?
2. ...?
3. ...?

Structural checks passed.
- One level-one title: true
...
Structural checks do not prove factual grounding. Unsupported claims require human review or a separate evaluator.
```

If authentication fails, run `copilot` once and authenticate before retrying. A two-minute failure
should print the timeout message and still release the session and client.

## Manual factual review

Check every noun, date, person, place, sequence, and causal claim:

1. Is each claim directly supported by one of the five approved facts?
2. Did the output avoid adding remembered details such as spacecraft names, quotations, landing
   locations, durations, or "first" claims?
3. Does hedging avoid turning an unsupported inference into an apparent fact?
4. Are all five facts represented accurately, without changing dates or crew roles?
5. Did the run show no tool activity or permission request?
6. Does declining defaults and entering no facts produce the actionable input error?

## Check your understanding

1. Which observed behavior came from model guidance, and which from application code?
2. Why does a structurally valid exhibit still need factual review?
3. What authorization and publication checks would remain outside the model in production?
