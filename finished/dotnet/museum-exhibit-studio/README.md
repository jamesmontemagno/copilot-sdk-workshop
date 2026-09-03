# Museum Exhibit Studio

This completed .NET sample uses the GitHub Copilot SDK to generate a small museum exhibit from
approved facts. The pre-built `Helpers/Curator*.cs` files provide fact sets, bounds checking,
streaming, deterministic validation, scoped Wikipedia permissions, scoped `exhibit.html` write
permission, and terminal input helpers. `Program.cs` stays learner-authored: it defines the curator
and research system messages, builds prompts, creates the three session configurations inline, and
orchestrates the console flow.

## Run the sample

From the repository root:

```bash
dotnet run --project finished/dotnet/museum-exhibit-studio
```

Set `COPILOT_MODEL` before running to select a model. Otherwise, the Copilot runtime chooses its
default. The sample requires an authenticated GitHub Copilot CLI.

Build without contacting a model:

```bash
dotnet build finished/dotnet/museum-exhibit-studio
```

## What the sample teaches

The generation session allowlists exactly one application-owned tool,
`approved_fact_lookup`, and uses a replace-mode system message, so the model can only write exhibit
text from facts this application handed it. `CuratorFacts.CreateApprovedFactLookup` bounds those
facts before the model can ever see them, `CuratorFacts.BoundFacts` trims and validates facts before
every generation or research send, and `CuratorStreamer.StreamExhibitAsync` streams
model output with explicit timeouts.

Optional Wikipedia research is intentionally lightweight: a separate session exposes only scoped
`search` and `readArticle` MCP tools through `CuratorSafety.WikipediaPermissionHandler`. The model
writes prose notes and a trailing `## Sources` list. The app extracts cited source titles and URLs
for display after the exhibit; research notes are background only and are never merged into the
approved facts.

After generation, deterministic validation checks the title, `## Narrative`, 100-140 word narrative
length, `## Visitor questions`, exactly three numbered questions, question marks, and prohibited
vocabulary. These structural checks do not prove factual grounding, so human review remains
required.

The optional capstone creates `exhibit.html` with `builtin:apply_patch`.
`CuratorSafety.ExhibitWritePermission` allows only that single file in the application working
directory and rejects every other write, shell, or MCP request.

## Manual check

1. Run the sample and accept one of the built-in fact sets.
2. Optionally run Wikipedia research and confirm sources print after the exhibit, not inside it.
3. Confirm the exhibit contains one title, a 100-140-word narrative, and three questions.
4. Confirm the validation summary and human-review caveat are displayed.
5. Optionally generate `exhibit.html` and review the standalone interactive page in a browser.

This is the application a learner ends up with after the museum lessons, not a separate reference
architecture. The entrypoint keeps one small session runner that starts the client, creates the
session, enforces the timeout, rejects blank output, and cleans up on every path; the research,
generation, and optional HTML steps reuse it with different session configurations. Follow the
track from
[`workshop/museum-00-preflight.md`](https://github.com/jamesmontemagno/copilot-sdk-workshop/blob/main/workshop/museum-00-preflight.md).
