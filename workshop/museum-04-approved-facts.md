# Step 4: Ground it in approved facts

> **Time:** 15 minutes

## What you'll build

Until now the curator has been writing from model memory. That is unacceptable for a museum: an
exhibit label is an institutional claim, and "the model knew it" is not a source.

In this step the educator supplies the facts and the **application** hands them to the curator
through a tool it owns. You register the pre-built `approved_fact_lookup` tool, make it the one
tool the model may call, and write a prompt that orders the curator to call it before writing a
word. You also let the educator pick one of three approved fact sets or type their own.

## Why the facts belong behind a tool, not inside the prompt

You could paste the fact list into the prompt text. Many applications do. But then the facts are
just more words in a request the model is free to read loosely, and every run carries the whole
catalog whether the model needs it or not.

A **local tool** is different. It runs inside your process, your code decides what it returns, and
the transcript records the moment the model asked for it. `approved_fact_lookup` is that tool. It
takes no arguments and returns the bounded approved fact list, so two runs on the same fact set ask
the same question and get the same answer — grounding stays deterministic.

The helpers already own the tool and the bounds. `boundFacts` trims every fact, drops blanks, and
rejects the batch when it is empty, longer than 20 facts, or contains a fact over 500 characters.
The tool factory applies those bounds to whatever it is given, so the model can never be handed an
unbounded list. Bounds are not politeness: an unbounded fact list is unpredictable cost, latency,
and attack surface.

`skip permission` is set on this tool because it only reads application-owned data that the
educator just approved on screen. The external Wikipedia process in Step 7 gets a permission
boundary instead.

## Two lists, two different jobs

Registering a tool takes two settings, and confusing them is the most common mistake in this
workshop:

- **`tools`** carries the *implementation*. This is where the runtime learns that a function called
  `approved_fact_lookup` exists and how to execute it.
- **`availableTools`** is the *allowlist*. It names which tools the model is permitted to call in
  this session. A tool that is registered but not allowlisted cannot be called.

You need both. Step 5 returns to the allowlist and shows what it prevents.

The prompt is the third piece, and it is the weakest one: it *asks* the model to call the tool. It
does not make the call happen, and it cannot stop a call. Keep the explicit "call
`approved_fact_lookup` first" instruction — at this stage you want the tool call to be reliable so
you can see it.

## Register the tool and build the prompt

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
    Tools = [CuratorFacts.CreateApprovedFactLookup(approvedFacts)],
    AvailableTools = [CuratorFacts.ApprovedFactLookupName],
    SystemMessage = new SystemMessageConfig
    {
        Mode = SystemMessageMode.Replace,
        Content = SystemMessage
    }
});

await CuratorStreamer.StreamExhibitAsync(session, BuildExhibitPrompt());

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

static string BuildExhibitPrompt()
{
    return $"""
        Create visitor-facing exhibit text about this application's approved subject.

        Call {CuratorFacts.ApprovedFactLookupName} first. Use only the facts it returns, and
        treat them as the complete source of truth for this exhibit.

        Return exactly this structure:

        # <an engaging exhibit title>
        ## Narrative
        <100-140 words, excluding the title and questions>
        ## Visitor questions
        1. <question>
        2. <question>
        3. <question>

        Write exactly three distinct visitor reflection questions. Do not add a preface,
        conclusion, software discussion, or facts the tool did not return.
        """;
}
```

Local functions come after the top-level statements. `BuildExhibitPrompt` takes no facts at all now
— it names the tool instead. `CreateApprovedFactLookup` calls `BoundFacts` internally, so the bound
holds no matter who builds the tool.
:::

:::language nodejs
Open `museum-workshop-app/src/index.ts` and widen the helper import:

```typescript
import {
  approvedFactLookupName,
  askLine,
  askYesNo,
  boundFacts,
  closeTerminal,
  createApprovedFactLookup,
  factSets,
  readFacts,
  streamExhibit,
} from "./curator.js";
```

Add the prompt builder and the fact-set chooser below the system message:

```typescript
function buildExhibitPrompt(): string {
  return `Create visitor-facing exhibit text about this application's approved subject.

Call ${approvedFactLookupName} first. Use only the facts it returns, and treat them as the
complete source of truth for this exhibit.

Return exactly this structure:

# <an engaging exhibit title>
## Narrative
<100-140 words, excluding the title and questions>
## Visitor questions
1. <question>
2. <question>
3. <question>

Write exactly three distinct visitor reflection questions. Do not add a preface,
conclusion, software discussion, or facts the tool did not return.`;
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
    tools: [createApprovedFactLookup(approvedFacts)],
    availableTools: [approvedFactLookupName],
    systemMessage: { mode: "replace", content: systemMessage },
  });

  await streamExhibit(session, buildExhibitPrompt());

  await session.disconnect();
  await client.stop();
  closeTerminal();
}
```

`buildExhibitPrompt` takes no facts at all now — it names the tool instead.
`createApprovedFactLookup` calls `boundFacts` internally, so the bound holds no matter who builds
the tool.
:::

:::language python
Open `museum-workshop-app/main.py` and widen the helper import:

```python
from curator import (
    APPROVED_FACT_LOOKUP_NAME,
    FACT_SETS,
    ask_line,
    ask_yes_no,
    bound_facts,
    create_approved_fact_lookup,
    read_facts,
    stream_exhibit,
)
```

Add the prompt builder below `SYSTEM_MESSAGE`:

```python
def build_exhibit_prompt() -> str:
    return f"""Create visitor-facing exhibit text about this application's approved subject.

Call {APPROVED_FACT_LOOKUP_NAME} first. Use only the facts it returns, and treat them as
the complete source of truth for this exhibit.

Return exactly this structure:

# <an engaging exhibit title>
## Narrative
<100-140 words, excluding the title and questions>
## Visitor questions
1. <question>
2. <question>
3. <question>

Write exactly three distinct visitor reflection questions. Do not add a preface,
conclusion, software discussion, or facts the tool did not return."""
```

Replace `main`:

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
            tools=[create_approved_fact_lookup(facts)],
            available_tools=[APPROVED_FACT_LOOKUP_NAME],
            system_message={"mode": "replace", "content": SYSTEM_MESSAGE},
        ) as session:
            await stream_exhibit(session, build_exhibit_prompt())
```

`build_exhibit_prompt` takes no facts at all now — it names the tool instead.
`create_approved_fact_lookup` calls `bound_facts` internally, so the bound holds no matter who
builds the tool.
:::

:::language go
Open `museum-workshop-app/main.go`. Add `"strconv"` to the import block, then add the prompt builder
below the system message:

```go
func buildExhibitPrompt() string {
	return fmt.Sprintf(`Create visitor-facing exhibit text about this application's approved subject.

Call %s first. Use only the facts it returns, and treat them as the complete
source of truth for this exhibit.

Return exactly this structure:

# <an engaging exhibit title>
## Narrative
<100-140 words, excluding the title and questions>
## Visitor questions
1. <question>
2. <question>
3. <question>

Write exactly three distinct visitor reflection questions. Do not add a preface,
conclusion, software discussion, or facts the tool did not return.`, ApprovedFactLookupName)
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

	lookup, err := ApprovedFactLookup(facts)
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
		ClientName:     "museum-exhibit-studio",
		Streaming:      copilot.Bool(true),
		Tools:          []copilot.Tool{lookup},
		AvailableTools: []string{ApprovedFactLookupName},
		SystemMessage: &copilot.SystemMessageConfig{
			Mode:    "replace",
			Content: systemMessage,
		},
	})
	if err != nil {
		panic(err)
	}
	defer func() { _ = session.Disconnect() }()

	if _, err := StreamExhibit(session, buildExhibitPrompt(), GenerationTimeout); err != nil {
		panic(err)
	}
}
```

`buildExhibitPrompt` takes no facts at all now — it names the tool instead. `ApprovedFactLookup`
calls `BoundFacts` internally, so the bound holds no matter who builds the tool.
:::

:::language rust
Open `museum-workshop-app/src/main.rs` and widen the crate import:

```rust
use museum_exhibit_studio::{
    APPROVED_FACT_LOOKUP_NAME, GENERATION_TIMEOUT, approved_fact_lookup, ask_line, ask_yes_no,
    bound_facts, fact_sets, read_facts, stream_exhibit,
};
```

Add the prompt builder below `SYSTEM_MESSAGE`:

```rust
fn build_exhibit_prompt() -> String {
    format!(
        r#"Create visitor-facing exhibit text about this application's approved subject.

Call {APPROVED_FACT_LOOKUP_NAME} first. Use only the facts it returns, and treat them as
the complete source of truth for this exhibit.

Return exactly this structure:

# <an engaging exhibit title>
## Narrative
<100-140 words, excluding the title and questions>
## Visitor questions
1. <question>
2. <question>
3. <question>

Write exactly three distinct visitor reflection questions. Do not add a preface,
conclusion, software discussion, or facts the tool did not return."#
    )
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
    config.tools = Some(vec![approved_fact_lookup(&facts)?]);
    config.available_tools = Some(vec![APPROVED_FACT_LOOKUP_NAME.to_owned()]);
    config.system_message = Some(
        SystemMessageConfig::new()
            .with_mode("replace")
            .with_content(SYSTEM_MESSAGE),
    );
    let session = client.create_session(config).await?;

    stream_exhibit(&session, build_exhibit_prompt(), GENERATION_TIMEOUT).await?;

    session.disconnect().await?;
    client.stop().await?;
    Ok(())
}
```

`build_exhibit_prompt` takes no facts at all now — it names the tool instead.
`approved_fact_lookup` calls `bound_facts` internally, so the bound holds no matter who builds the
tool.
:::

:::language java
Open `museum-workshop-app/src/main/java/workshop/MuseumExhibitStudio.java`. Add
`import java.util.List;` to the imports, then add the prompt builder to the class:

```java
    public static String buildExhibitPrompt() {
        return """
                Create visitor-facing exhibit text about this application's approved subject.

                Call %s first. Use only the facts it returns, and treat them as the
                complete source of truth for this exhibit.

                Return exactly this structure:

                # <an engaging exhibit title>
                ## Narrative
                <100-140 words, excluding the title and questions>
                ## Visitor questions
                1. <question>
                2. <question>
                3. <question>

                Write exactly three distinct visitor reflection questions. Do not add a preface,
                conclusion, software discussion, or facts the tool did not return.
                """.formatted(CuratorFacts.APPROVED_FACT_LOOKUP_NAME);
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
                    .setTools(List.of(CuratorFacts.approvedFactLookup(facts)))
                    .setAvailableTools(List.of(CuratorFacts.APPROVED_FACT_LOOKUP_NAME))
                    .setSystemMessage(new SystemMessageConfig()
                            .setMode(SystemMessageMode.REPLACE)
                            .setContent(SYSTEM_MESSAGE))).get();
            try {
                CuratorStreamer.streamExhibit(session, buildExhibitPrompt());
            } finally {
                session.close();
                client.stop().get();
            }
        } finally {
            CuratorTerminal.close();
        }
    }
```

`buildExhibitPrompt` takes no facts at all now — it names the tool instead. `approvedFactLookup`
calls `boundFacts` internally, so the bound holds no matter who builds the tool.
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

The application now interviews you before it writes anything, and the curator visibly fetches its
facts before it writes a word:

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

[tool:start] approved_fact_lookup
[tool:done] success=true

# A Reef the Size of a Country
## Narrative
Off the Queensland coast, more than two thousand nine hundred reefs...
## Visitor questions
1. ...
```

The `[tool:start] approved_fact_lookup` line is the whole point of this step. The curator did not
recall the reef — it asked your application for the facts, and your application answered.

## Prove the tool is doing the work

Run it again and choose set 1 or 3. The exhibit changes subject completely, and the tool event
appears again each time. Nothing in the prompt changed between those runs: the same prompt text
produced a Terracotta Army exhibit because the tool returned different data. That is the difference
between a prompt that carries data and an application that owns it.

Then answer `n` at the confirmation, type two or three facts of your own, and submit a blank line.
The curator writes about your subject instead — your typed facts went into the tool, and the tool
handed them back to the model.

Try the failure case too. Answer `n` and immediately submit a blank line without typing any facts.
The run stops with `Provide at least one approved fact.` — the tool factory refused to be built
around an empty list, so no request was ever sent. Step 5 turns that crash into a civil error
message.

## Check your understanding

- You registered the tool in two places. What would happen if you put `approved_fact_lookup` in the
  tool list but left it out of the allowlist?
- The prompt says "Call `approved_fact_lookup` first." Does that sentence guarantee the call
  happens? What in this step made the tool *available* to be called at all?
- The tool takes no arguments and always returns the same bounded list for a given fact set. What
  would you lose if it took a free-text query argument instead?
- The output structure is requested in the prompt. What has actually verified that the model
  followed it so far?

Continue to [Set the guardrails](museum-05-guardrails.md).
