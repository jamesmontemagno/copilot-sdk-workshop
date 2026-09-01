# Museum Exhibit Studio

This Rust sample uses the GitHub Copilot SDK as a focused, non-software-engineering
agent harness. A museum educator can accept the Apollo 11 fixture or enter another
approved fact set, optionally research it through a tightly scoped Wikipedia MCP
session, approve sourced additions one by one, generate visitor-facing exhibit copy
in a separate tool-free session, and inspect deterministic structural checks.

## Run the sample

From the repository root:

```bash
cargo run --manifest-path samples/rust/museum-exhibit-studio/Cargo.toml --locked
```

Set `COPILOT_MODEL` to select a model. Otherwise, the Copilot runtime chooses its
default. The sample requires an authenticated GitHub Copilot CLI.

Run the mocked tests without contacting a model:

```bash
cargo test --locked --manifest-path samples/rust/museum-exhibit-studio/Cargo.toml
```

## What the sample teaches

`SYSTEM_MESSAGE` is the complete durable agent definition. Approved facts remain
in the separate user task prompt because they are task data, not reusable policy.
The generation session replaces the built-in system message, identifies itself as
`museum-exhibit-studio`, and exposes no tools. The optional research session is
separate, exposes only Wikipedia `search` and `readArticle`, and uses a fail-closed
permission handler. Retrieved additions remain proposals until the educator approves
them; consulted sources are printed outside the generated exhibit.

The application limits input to 20 facts of at most 500 characters each, applies
a 120-second generation timeout, rejects an empty response, and disconnects the
session and stops the client on success or failure. Its validator checks for one
level-one title, the required sections, a 100–140-word narrative, exactly three
numbered questions ending in `?`, and prohibited software vocabulary.

Research has a 60-second timeout and 64 KiB response limit. Strict JSON parsing
requires one review per supplied fact, one of four review statuses, and canonical
Wikipedia provenance for supported/contradicted facts and proposed additions.
Startup, timeout, empty, malformed, or provenance failures become visible
`not checked` results and generation continues from the original facts only.

The validator cannot prove semantic factual grounding. Generated claims still
require human review or a separate evaluator.
