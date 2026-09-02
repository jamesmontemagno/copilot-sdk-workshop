# Step 4: Ground it in approved facts

> **Time:** 15 minutes

## What you'll build

Until now the curator has been writing from model memory. That is unacceptable for a museum: an
exhibit label is an institutional claim, and "the model knew it" is not a source.

In this step the educator supplies the facts. You add a prompt builder that puts those approved
facts into the request, bounds them first, and demands an exact output structure. You also let the
educator pick one of three approved fact sets or type their own.

## Application-owned policy versus task data

You now have both halves of the contract in front of you:

- The **system message** is policy. It rarely changes and it belongs to the application.
- The **prompt** is task data. It changes every run and carries the educator's facts.

The helpers already own the fact catalog and the bounds. `boundFacts` trims every fact, drops
blanks, and rejects the batch when it is empty, longer than 20 facts, or contains a fact over 500
characters. Bounds are not politeness: an unbounded fact list is an unbounded prompt, and an
unbounded prompt is unpredictable cost, latency, and attack surface. Call it before every send.

The helpers also own the terminal prompts, so there is exactly one reader of standard input in the
application. Your prompt builder is the only new logic.

## Add the fact-driven prompt

:::language dotnet
Open `museum-workshop-app/Program.cs`. Widen nothing at the top — you already have
`using MuseumExhibitStudio.Helpers;`. Replace everything from the first `Console.WriteLine` to the
end of the file:

```csharp
Console.WriteLine("=== Museum Exhibit Studio ===");
Console.WriteLine();
Console.WriteLine("Approved fact sets:");
for (var index = 0; index < CuratorFacts.FactSets.Count; index++)
{
    Console.WriteLine($"{index + 1}. {CuratorFacts.FactSets[index].Label}");
}

Console.WriteLine();

var selectedFactSet = ReadFactSetSelection();
var approvedFacts = CuratorFacts.BoundFacts(selectedFactSet.Facts);
for (var index = 0; index < approvedFacts.Length; index++)
{
    Console.WriteLine($"{index + 1}. {approvedFacts[index]}");
}

Console.WriteLine();

if (!CuratorTerminal.AskYesNo("Use these facts?", defaultYes: true))
{
    approvedFacts = CuratorFacts.BoundFacts(CuratorTerminal.ReadFacts());
}

Console.WriteLine();

await using var client = new CopilotClient();
await client.StartAsync();

await using var session = await client.CreateSessionAsync(new SessionConfig
{
    ClientName = "museum-exhibit-studio",
    Streaming = true,
    SystemMessage = new SystemMessageConfig
    {
        Mode = SystemMessageMode.Replace,
        Content = SystemMessage
    }
});

await CuratorStreamer.StreamExhibitAsync(session, BuildExhibitPrompt(approvedFacts));

await client.StopAsync();
CuratorTerminal.CloseTerminal();

CuratorFactSet ReadFactSetSelection()
{
    var input = CuratorTerminal.AskLine("Choose a fact set [1-3, default 1]: ");
    if (int.TryParse(input, out var selection) &&
        selection >= 1 &&
        selection <= CuratorFacts.FactSets.Count)
    {
        return CuratorFacts.FactSets[selection - 1];
    }

    return CuratorFacts.FactSets[0];
}

static string BuildExhibitPrompt(IEnumerable<string?> approvedFacts)
{
    var facts = CuratorFacts.BoundFacts(approvedFacts);
    var factList = string.Join(Environment.NewLine, facts.Select(fact => $"- {fact}"));

    return $"""
        Create visitor-facing exhibit text about the supplied subject using only these supplied facts:

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

Local functions come after the top-level statements. `BuildExhibitPrompt` calls `BoundFacts` again
even though `main` already bounded the list, so the bound holds no matter who calls the builder.
:::

:::language nodejs
Open `museum-workshop-app/src/index.ts` and widen the helper import:

```typescript
import {
  askLine,
  askYesNo,
  boundFacts,
  closeTerminal,
  factSets,
  readFacts,
  streamExhibit,
} from "./curator.js";
```

Add the prompt builder and the fact-set chooser below the system message:

```typescript
function buildExhibitPrompt(approvedFacts: Iterable<string>): string {
  const facts = boundFacts(approvedFacts);

  return `Create visitor-facing exhibit text about the supplied subject using only these supplied facts:

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

async function chooseFactSet(): Promise<(typeof factSets)[number]> {
  const answer = await askLine("Choose a fact set [1-3, default 1]: ");
  const choice = Number.parseInt(answer, 10);
  if (Number.isInteger(choice) && choice >= 1 && choice <= factSets.length) {
    return factSets[choice - 1] ?? factSets[0];
  }
  return factSets[0];
}
```

Replace `main` with:

```typescript
async function main(): Promise<void> {
  console.log("=== Museum Exhibit Studio ===");
  console.log();
  console.log("Approved fact sets:");
  factSets.forEach((factSet, index) => console.log(`${index + 1}. ${factSet.label}`));
  console.log();

  const chosenSet = await chooseFactSet();
  let approvedFacts = boundFacts(chosenSet.facts);
  approvedFacts.forEach((fact, index) => console.log(`${index + 1}. ${fact}`));
  console.log();

  if (!(await askYesNo("Use these facts?", true))) {
    approvedFacts = boundFacts(await readFacts());
  }

  console.log();
  const client = new CopilotClient();
  await client.start();
  const session = await client.createSession({
    clientName: "museum-exhibit-studio",
    streaming: true,
    systemMessage: { mode: "replace", content: systemMessage },
  });

  await streamExhibit(session, buildExhibitPrompt(approvedFacts));

  await session.disconnect();
  await client.stop();
  closeTerminal();
}
```

`buildExhibitPrompt` calls `boundFacts` again even though `main` already bounded the list, so the
bound holds no matter who calls the builder.
:::

:::language python
Open `museum-workshop-app/main.py` and widen the helper import:

```python
from curator import (
    FACT_SETS,
    ask_line,
    ask_yes_no,
    bound_facts,
    read_facts,
    stream_exhibit,
)
```

Add the prompt builder below `SYSTEM_MESSAGE`:

```python
def build_exhibit_prompt(facts: Iterable[str]) -> str:
    approved_facts = bound_facts(facts)
    fact_list = "\n".join(f"- {fact}" for fact in approved_facts)
    return f"""Create visitor-facing exhibit text about the supplied subject using only these supplied facts:

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

Add `from collections.abc import Iterable` to the imports at the top of the file, then replace
`main`:

```python
async def main() -> None:
    print("=== Museum Exhibit Studio ===")
    print()
    print("Approved fact sets:")
    for index, fact_set in enumerate(FACT_SETS, start=1):
        print(f"{index}. {fact_set.label}")
    print()

    choice = ask_line("Choose a fact set [1-3, default 1]: ")
    selected_index = int(choice) - 1 if choice in {"1", "2", "3"} else 0
    facts = list(FACT_SETS[selected_index].facts)
    for index, fact in enumerate(facts, start=1):
        print(f"{index}. {fact}")
    print()

    if not ask_yes_no("Use these facts?", True):
        facts = read_facts()
    facts = bound_facts(facts)

    print()
    async with CopilotClient() as client:
        async with await client.create_session(
            client_name="museum-exhibit-studio",
            streaming=True,
            system_message={"mode": "replace", "content": SYSTEM_MESSAGE},
        ) as session:
            await stream_exhibit(session, build_exhibit_prompt(facts))
```

`build_exhibit_prompt` calls `bound_facts` again even though `main` already bounded the list, so the
bound holds no matter who calls the builder.
:::

:::language go
Open `museum-workshop-app/main.go`. Add `"strconv"` and `"strings"` to the import block, then add
the prompt builder below the system message:

```go
func buildExhibitPrompt(approvedFacts []string) (string, error) {
	facts, err := BoundFacts(approvedFacts)
	if err != nil {
		return "", err
	}

	var factList strings.Builder
	for _, fact := range facts {
		fmt.Fprintf(&factList, "- %s\n", fact)
	}
	return fmt.Sprintf(`Create visitor-facing exhibit text about the supplied subject using only these supplied facts:

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

Replace `main`:

```go
func main() {
	fmt.Println("=== Museum Exhibit Studio ===")
	fmt.Println()
	fmt.Println("Approved fact sets:")
	for index, factSet := range FactSets {
		fmt.Printf("%d. %s\n", index+1, factSet.Label)
	}
	fmt.Println()

	choice := AskLine(fmt.Sprintf("Choose a fact set [1-%d, default 1]: ", len(FactSets)))
	selectedIndex := 0
	if parsed, err := strconv.Atoi(choice); err == nil && parsed >= 1 && parsed <= len(FactSets) {
		selectedIndex = parsed - 1
	}

	facts := append([]string(nil), FactSets[selectedIndex].Facts...)
	for index, fact := range facts {
		fmt.Printf("%d. %s\n", index+1, fact)
	}
	fmt.Println()

	if !AskYesNo("Use these facts?", true) {
		facts = ReadFacts()
	}
	facts, err := BoundFacts(facts)
	if err != nil {
		panic(err)
	}

	prompt, err := buildExhibitPrompt(facts)
	if err != nil {
		panic(err)
	}

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
		SystemMessage: &copilot.SystemMessageConfig{
			Mode:    "replace",
			Content: systemMessage,
		},
	})
	if err != nil {
		panic(err)
	}
	defer func() { _ = session.Disconnect() }()

	if _, err := StreamExhibit(session, prompt, GenerationTimeout); err != nil {
		panic(err)
	}
}
```

`buildExhibitPrompt` calls `BoundFacts` again even though `main` already bounded the list, so the
bound holds no matter who calls the builder.
:::

:::language rust
Open `museum-workshop-app/src/main.rs` and widen the crate import:

```rust
use museum_exhibit_studio::{
    FactBoundsError, GENERATION_TIMEOUT, ask_line, ask_yes_no, bound_facts, fact_sets, read_facts,
    stream_exhibit,
};
```

Add the prompt builder below `SYSTEM_MESSAGE`:

```rust
fn build_exhibit_prompt<I, S>(approved_facts: I) -> Result<String, FactBoundsError>
where
    I: IntoIterator<Item = S>,
    S: AsRef<str>,
{
    let facts = bound_facts(approved_facts)?;
    let fact_list = facts
        .iter()
        .map(|fact| format!("- {fact}"))
        .collect::<Vec<_>>()
        .join("\n");
    Ok(format!(
        r#"Create visitor-facing exhibit text about the supplied subject using only these supplied facts:

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

Replace `main`:

```rust
#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    println!("=== Museum Exhibit Studio ===");
    println!();
    println!("Approved fact sets:");
    for (index, fact_set) in fact_sets().iter().enumerate() {
        println!("{}. {}", index + 1, fact_set.label);
    }
    println!();

    let choice = ask_line("Choose a fact set [1-3, default 1]: ")?;
    let selected_index = choice
        .trim()
        .parse::<usize>()
        .ok()
        .filter(|index| (1..=fact_sets().len()).contains(index))
        .unwrap_or(1)
        - 1;
    let mut facts = fact_sets()[selected_index]
        .facts
        .iter()
        .map(|fact| (*fact).to_owned())
        .collect::<Vec<_>>();
    for (index, fact) in facts.iter().enumerate() {
        println!("{}. {fact}", index + 1);
    }
    println!();

    if !ask_yes_no("Use these facts?", true)? {
        facts = read_facts()?;
    }
    let facts = bound_facts(facts)?;

    println!();
    let client = Client::start(ClientOptions::default()).await?;
    let mut config = SessionConfig::default();
    config.client_name = Some("museum-exhibit-studio".to_owned());
    config.streaming = Some(true);
    config.system_message = Some(
        SystemMessageConfig::new()
            .with_mode("replace")
            .with_content(SYSTEM_MESSAGE),
    );
    let session = client.create_session(config).await?;

    stream_exhibit(&session, build_exhibit_prompt(&facts)?, GENERATION_TIMEOUT).await?;

    session.disconnect().await?;
    client.stop().await?;
    Ok(())
}
```

`build_exhibit_prompt` calls `bound_facts` again even though `main` already bounded the list, so the
bound holds no matter who calls the builder.
:::

:::language java
Open `museum-workshop-app/src/main/java/workshop/MuseumExhibitStudio.java`. Add
`import java.util.List;` to the imports, then add the prompt builder to the class:

```java
    public static String buildExhibitPrompt(Iterable<String> approvedFacts) {
        List<String> facts = CuratorFacts.boundFacts(approvedFacts);
        String factList = String.join("\n", facts.stream().map(fact -> "- " + fact).toList());
        return """
                Create visitor-facing exhibit text about the supplied subject using only these supplied facts:

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

    private static CuratorFacts.FactSet selectFactSet(String input) {
        if (input != null && !input.isBlank()) {
            try {
                int selected = Integer.parseInt(input.trim());
                if (selected >= 1 && selected <= CuratorFacts.factSets.size()) {
                    return CuratorFacts.factSets.get(selected - 1);
                }
            } catch (NumberFormatException ignored) {
            }
        }
        return CuratorFacts.factSets.get(0);
    }
```

Replace `main`:

```java
    public static void main(String[] args) throws Exception {
        System.out.println("=== Museum Exhibit Studio ===");
        System.out.println();
        System.out.println("Approved fact sets:");
        for (int index = 0; index < CuratorFacts.factSets.size(); index++) {
            System.out.printf("%d. %s%n", index + 1, CuratorFacts.factSets.get(index).label());
        }
        System.out.println();

        CuratorFacts.FactSet selected =
                selectFactSet(CuratorTerminal.askLine("Choose a fact set [1-3, default 1]: "));
        List<String> facts = selected.facts();
        for (int index = 0; index < facts.size(); index++) {
            System.out.printf("%d. %s%n", index + 1, facts.get(index));
        }
        System.out.println();

        if (!CuratorTerminal.askYesNo("Use these facts?", true)) {
            facts = CuratorTerminal.readFacts();
        }
        facts = CuratorFacts.boundFacts(facts);

        System.out.println();
        try (var client = new CopilotClient()) {
            client.start().get();
            var session = client.createSession(new SessionConfig()
                    .setClientName("museum-exhibit-studio")
                    .setStreaming(true)
                    .setSystemMessage(new SystemMessageConfig()
                            .setMode(SystemMessageMode.REPLACE)
                            .setContent(SYSTEM_MESSAGE))).get();
            try {
                CuratorStreamer.streamExhibit(session, buildExhibitPrompt(facts));
            } finally {
                session.close();
                client.stop().get();
            }
        } finally {
            CuratorTerminal.close();
        }
    }
```

`buildExhibitPrompt` calls `boundFacts` again even though `main` already bounded the list, so the
bound holds no matter who calls the builder.
:::

## Run it

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
museum-workshop-app/.venv/bin/python museum-workshop-app/main.py
```
:::
:::language go
```bash
go -C museum-workshop-app run .
```
:::
:::language rust
```bash
cargo run --manifest-path museum-workshop-app/Cargo.toml
```
:::
:::language java
```bash
mvn -f museum-workshop-app/pom.xml compile exec:java
```
:::

The application now interviews you before it writes anything:

```text
=== Museum Exhibit Studio ===

Approved fact sets:
1. Apollo 11
2. Great Barrier Reef
3. Terracotta Army

Choose a fact set [1-3, default 1]: 2
1. The Great Barrier Reef lies off the coast of Queensland, Australia.
2. It stretches for about 2,300 kilometres.
3. It is made up of more than 2,900 individual reefs.
4. It was added to the UNESCO World Heritage List in 1981.
5. Rising sea temperatures have caused repeated coral bleaching events.

Use these facts? [Y/n]: y

# A Reef the Size of a Country
## Narrative
Off the Queensland coast, more than two thousand nine hundred reefs...
## Visitor questions
1. ...
```

Choose set 2 or 3 and the exhibit changes subject completely — the fact list is doing the work, not
the model's memory. Then answer `n` at the confirmation, type two or three facts of your own, and
submit a blank line: the curator writes about your subject instead.

Try the failure case too. Answer `n` and immediately submit a blank line without typing any facts.
The run stops with `Provide at least one approved fact.` — your code refused to send an empty
exhibit request. Step 5 turns that crash into a civil error message.

## Check your understanding

- Why does the prompt builder bound the facts even though `main` bounded them a moment earlier?
- The prompt says "Do not... use tools." Does that sentence prevent a tool call? What would?
- The output structure is requested in the prompt. What has actually verified that the model
  followed it so far?

Continue to [Set the guardrails](museum-05-guardrails.md).
