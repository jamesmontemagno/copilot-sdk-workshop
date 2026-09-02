# Museum Exhibit Studio

This Rust sample uses the GitHub Copilot SDK as a focused, non-software-engineering agent harness. Pre-built helpers live in `src/lib.rs`; the learner-authored orchestration lives in `src/main.rs`.

## Run the sample

```bash
cargo run --manifest-path finished/rust/museum-exhibit-studio/Cargo.toml --locked
```

Set `COPILOT_MODEL` to select a generation model. The sample requires an authenticated GitHub Copilot CLI.

Check without contacting a model:

```bash
cargo check --locked --manifest-path finished/rust/museum-exhibit-studio/Cargo.toml
```

## What the sample teaches

The generation session uses a replacement curator system message, validates approved facts, streams with a 120-second timeout, exposes an empty tool allowlist, rejects blank output, and prints deterministic structural validation.

Optional Wikipedia research is separate: it exposes only scoped `search` and `readArticle` MCP tools, uses a deny-by-default permission handler, asks for prose notes plus cited sources, and never merges research into the approved facts.

Optional HTML generation uses `builtin:apply_patch` with a single-file permission handler that can write only `exhibit.html` in the application working directory.
