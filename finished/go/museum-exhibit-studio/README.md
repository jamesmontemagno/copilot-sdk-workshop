# Museum Exhibit Studio

This Go sample uses the GitHub Copilot SDK as a focused museum-curation harness. The app now has a
two-file shape:

- `curator.go` contains the pre-built helper API: approved fact sets, fact bounds, response
  streaming, structural validation, Wikipedia permissions, source extraction, the optional
  `exhibit.html` write permission, and terminal helpers.
- `main.go` contains the learner-authored orchestration: prompts, session configuration, console
  flow, and cleanup.

## Run the sample

From this directory:

```bash
go run .
```

Set `COPILOT_MODEL` to select the generation model; otherwise the runtime chooses its default. An
authenticated GitHub Copilot CLI is required.

Build without contacting a model or Wikipedia:

```bash
go build -mod=readonly ./...
```

## What the sample teaches

Generation uses a replacement system message, an empty tool allowlist, bounded approved facts, event
streaming, and a 120-second timeout. Optional Wikipedia research runs in a separate 90-second
session with only scoped search and article-read tools plus a deny-by-default permission handler.
Research is shown as background for the human curator only: it searches, reads, and cites consulted
articles in a trailing `## Sources` section. It no longer uses a strict JSON contract, proposed
additions, source URL schema validation, or an approval loop, and research findings are never merged
into the approved facts used for exhibit generation.

After generation, deterministic validation checks one H1, required sections, a 100-140-word
narrative, exactly three numbered visitor questions ending in `?`, and prohibited software terms.
The consulted Wikipedia sources are printed after the exhibit, outside the generated copy.

Optionally, the app can ask Copilot to create `exhibit.html` with `builtin:apply_patch`. That session
allows only a single normalized write to `exhibit.html` in the application working directory and
rejects every other file, shell, or MCP permission request. The HTML prompt requires a standalone
semantic document with embedded CSS and JavaScript, a human-review caveat, and an accessible question
filter.
