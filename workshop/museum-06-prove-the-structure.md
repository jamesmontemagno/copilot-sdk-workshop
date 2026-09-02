# Step 6: Prove the structure

> **Time:** 10 minutes

## What you'll build

A PASS/FAIL report printed under every exhibit. Two lines of new code: capture the text the session
runner already returned, then hand it to the pre-built validator.

## What deterministic checks can and cannot prove

The validator in the helper module is ordinary code with no model in it. Given the same text it
always returns the same verdict. It checks:

- exactly one level-one title
- a `## Narrative` section
- a narrative of 100–140 words
- a `## Visitor questions` section with exactly three numbered items
- every numbered item ending in a question mark
- no prohibited vocabulary (`software`, `codebase`, `repository`, `terminal`, `GitHub Copilot`)

That is a **structural** contract, and it is genuinely enforceable. It is not a **factual** one.
A perfectly structured exhibit can still contain a claim no approved fact supports. The report ends
by saying so, and that sentence is the honest boundary of this application:

```text
Structural checks do not prove factual grounding. Unsupported claims require human review or a separate evaluator.
```

You are not writing the validator. Learning to *react* to a machine verdict — and to know exactly
what it does not cover — is the lesson.

## Wire the validator

:::language dotnet
Open `museum-workshop-app/Program.cs`. Capture the returned exhibit and print the report:

```csharp
    Console.WriteLine();
    var exhibit = await RunSessionAsync(
        GenerationConfig(approvedFacts),
        BuildExhibitPrompt(),
        CuratorStreamer.GenerationTimeout);

    Console.WriteLine();
    Console.WriteLine(CuratorValidation.FormatValidation(CuratorValidation.ValidateExhibit(exhibit)));

    return 0;
```

`CuratorValidation` is already in the `MuseumExhibitStudio.Helpers` namespace you imported in
Step 2, so there is nothing new to add at the top of the file.
:::

:::language nodejs
Open `museum-workshop-app/src/index.ts`. Add `formatValidation` and `validateExhibit` to the helper
import, then capture the returned exhibit and print the report:

```typescript
    console.log();
    const exhibit = await runSession(
      generationConfig(approvedFacts),
      buildExhibitPrompt(),
      generationTimeoutMs,
    );

    console.log();
    console.log(formatValidation(validateExhibit(exhibit)));
```
:::

:::language python
Open `museum-workshop-app/main.py`. Add `format_validation` and `validate_exhibit` to the helper
import, then capture the returned exhibit and print the report:

```python
    try:
        print()
        exhibit = await run_session(
            generation_config(facts),
            build_exhibit_prompt(),
            GENERATION_TIMEOUT_SECONDS,
        )

        print()
        print(format_validation(validate_exhibit(exhibit)))
        return 0
```
:::

:::language go
Open `museum-workshop-app/main.go`. Capture the returned exhibit and print the report:

```go
	fmt.Println()
	exhibit, err := runSession(ctx, exhibitConfig, buildExhibitPrompt(), GenerationTimeout)
	if err != nil {
		return err
	}

	fmt.Println()
	fmt.Println(FormatValidation(ValidateExhibit(exhibit)))
	return nil
```

`FormatValidation` and `ValidateExhibit` live in `curator.go` in the same package, so there is no
import to add.
:::

:::language rust
Open `museum-workshop-app/src/main.rs`. Add `format_validation` and `validate_exhibit` to the crate
import, then capture the returned exhibit and print the report:

```rust
    println!();
    let exhibit = run_session(
        generation_config(&facts)?,
        build_exhibit_prompt(),
        GENERATION_TIMEOUT,
    )
    .await?;

    println!();
    println!("{}", format_validation(&validate_exhibit(&exhibit)));

    Ok(())
```
:::

:::language java
Open `museum-workshop-app/src/main/java/workshop/MuseumExhibitStudio.java`. Capture the returned
exhibit and print the report:

```java
            System.out.println();
            String exhibit = runSession(
                    generationConfig(facts),
                    buildExhibitPrompt(),
                    CuratorStreamer.GENERATION_TIMEOUT);

            System.out.println();
            System.out.println(CuratorValidation.formatValidation(CuratorValidation.validateExhibit(exhibit)));
```

`CuratorValidation` sits in the same `workshop` package, so there is no import to add.
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

The exhibit streams as before, and then a verdict appears under it:

```text
Structural checks passed.
- One level-one title: true
- Narrative section: true
- Narrative length: 126 words (within 100-140: true)
- Visitor questions section: true
- Numbered questions: 3 (exactly three: true)
- Every item is a question: true
- Prohibited vocabulary: none

Structural checks do not prove factual grounding. Unsupported claims require human review or a separate evaluator.
```

A failing run is just as informative, and you will see one eventually — narrative length is the
usual culprit:

```text
Structural checks found issues:
- One level-one title: true
- Narrative section: true
- Narrative length: 163 words (within 100-140: false)
- Visitor questions section: true
- Numbered questions: 3 (exactly three: true)
- Every item is a question: true
- Prohibited vocabulary: none
  - The narrative must contain 100-140 words; found 163.

Structural checks do not prove factual grounding. Unsupported claims require human review or a separate evaluator.
```

The run still exits successfully. That is deliberate: the report is for a human curator deciding
whether to publish, not a build gate. Rerun the exhibit, or tighten the fact list, and try again.

Force a failure on purpose to see the vocabulary rule fire. Supply your own single fact:

```text
The museum's ticketing terminal was installed in 1998.
```

The exhibit will repeat the word `terminal`, and the report flags it — the check reads the output,
not your intent.

## Check your understanding

- The report says the structure passed. What has it *not* told you about the exhibit?
- Structural failure does not stop the program. When would making it a hard failure be right, and
  when would it be wrong?
- The validator is deterministic. Why does that matter more for a museum than a slightly smarter
  model-based reviewer would?

Continue to [Research with Wikipedia MCP](museum-07-wikipedia-research.md).
