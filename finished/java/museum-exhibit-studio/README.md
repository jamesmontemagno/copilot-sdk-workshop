# Museum Exhibit Studio

This Maven CLI sample uses the GitHub Copilot SDK as a focused museum-curation agent. A museum educator chooses one of three approved fact sets or enters their own bounded facts, optionally streams scoped Wikipedia background research, generates visitor-facing exhibit copy, validates its structure, and can opt in to an `exhibit.html` capstone.

## Run

From this directory:

```bash
mvn compile exec:java
```

Set `COPILOT_MODEL` to select a model; otherwise the Copilot runtime chooses its default. The sample requires an authenticated GitHub Copilot CLI.

Compile without contacting a model:

```bash
mvn compile
```

## What it demonstrates

The learner-authored `MuseumExhibitStudio` entrypoint builds sessions directly with `new CopilotClient()`. The pre-built `Curator*` helpers provide approved facts, streaming, validation, scoped permissions, source extraction, and terminal prompts.

Prompt guidance is not an authorization boundary, so the application also:

- keeps generation tool-free with an empty available-tools list and a reject-all permission handler;
- limits research to the configured Wikipedia MCP server and `wikipedia-search` / `wikipedia-readArticle` through a deny-by-default permission handler;
- treats Wikipedia output as background notes only, extracts cited sources from a trailing `## Sources` section, and never merges research into the approved facts;
- bounds input to 20 facts of at most 500 characters each before every model send;
- uses explicit timeouts, rejects blank exhibit output, and disconnects sessions / stops clients on success and failure;
- checks one H1, required sections, a 100-140-word narrative, exactly three numbered questions ending in `?`, and prohibited software vocabulary; and
- optionally allows `builtin:apply_patch` to write only `exhibit.html` in the application working directory.

The validator cannot prove semantic factual grounding. Generated claims still require human review or a separate evaluator.

## Optional HTML capstone and Java SDK limitation

When prompted, answer yes to generate `exhibit.html`. The default Java permission handler approves a write only when the SDK exposes a write request whose normalized `fileName` is exactly `exhibit.html` in this directory.

Current Java SDK releases may not surface those write-request fields (see <https://github.com/github/copilot-sdk/issues/2273>). For the controlled local workshop only, run with:

```bash
mvn compile exec:java -Dexec.args="--allow-local-demo-write"
```

That fallback is limited by the app to the `write` permission kind while only `builtin:apply_patch` is available, but it cannot enforce the output path. Do not use the fallback for production, shared, or untrusted worktrees.
