# Rust guide: Wikipedia MCP

Final implementation reference for museum step 7 on the Rust track. It assumes
`museum-workshop-app` is the application you built through
[Run and review the exhibit](../museum-06-run-review.md) and then extended in
[Wikipedia MCP](../museum-07-wikipedia-grounding.md) with `research_session_config` and the
`WikipediaPermissions` handler.

The completed counterpart of every file below is in `finished/rust/museum-exhibit-studio`.

## Final layout

| File in `museum-workshop-app` | Introduced in | Responsibility |
|---|---|---|
| `Cargo.toml` | Preflight, steps 1, 2, 7 | Package `museum-exhibit-studio`, edition 2024, SDK 1.0.11 and the crates below |
| `Cargo.lock` | Preflight | Deterministic dependency versions |
| `src/lib.rs` | Steps 1-7 | Curator policy, prompt builder, validator, generation lifecycle, research contract, MCP configuration, permission handler, SDK adapter |
| `src/main.rs` | Steps 1-7 | Interactive CLI, approval gate, printed sources |

The Rust track keeps everything except the CLI in one library crate, exactly as the completed
project does. Step 1 renamed the package to `museum-exhibit-studio`, so `src/main.rs` imports from
`museum_exhibit_studio` and the completed entrypoint compiles unchanged.

## 1. Confirm the dependencies

Step 7 replaced the `[dependencies]` section of `museum-workshop-app/Cargo.toml` with:

```toml
[dependencies]
async-trait = "=0.1.91"
github-copilot-sdk = { version = "=1.0.11", features = ["derive"] }
indexmap = "2.14"
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"
tokio = { version = "1", features = ["macros", "rt-multi-thread"] }
```

The completed project pins these with `=` requirements. The ranges above resolve to the versions
already recorded in the `Cargo.lock` you copied during preflight, so Cargo records the direct
dependencies without changing any resolved version.

## 2. Replace the library

```bash
cp finished/rust/museum-exhibit-studio/src/lib.rs museum-workshop-app/src/lib.rs
```

This preserves everything you built in steps 1 through 5 and adds the research half. Confirm the
resulting file still contains the pieces you wrote:

| Item | Introduced in |
|---|---|
| `MAXIMUM_FACT_COUNT`, `MAXIMUM_FACT_LENGTH`, `APOLLO_11_FACTS`, `SYSTEM_MESSAGE` | Step 1 |
| `create_session_configuration` with `config.available_tools = Some(Vec::new())` | Step 2 |
| `PromptError` and `build_exhibit_prompt` | Step 3 |
| The validation types, `validate_exhibit`, `find_heading`, `numbered_item`, `count_words` | Step 4 |
| `GENERATION_TIMEOUT`, `StudioError`, `is_timeout_error`, `GeneratedExhibit`, `generate_exhibit` | Step 5 |
| `RESEARCH_TIMEOUT`, `MAXIMUM_RESEARCH_RESPONSE_BYTES`, `RESEARCH_SYSTEM_MESSAGE` | Step 7 lesson |
| `research_session_config`, `permission_payload`, `wikipedia_permission_allowed`, `WikipediaPermissions` | Step 7 lesson |

**Imports.** Step 7 already replaced the import block with the full list: `std::sync::Arc`,
`github_copilot_sdk::handler::PermissionHandler` and `PermissionResult`, the types
`McpServerConfig`, `McpStdioServerConfig`, `PermissionRequestData`, `RequestId`, `SessionId`,
`indexmap::IndexMap`, and `serde::{Deserialize, Serialize}`. Every one of them is used once the
contract types below exist.

**Limits.**

| Constant | Value |
|---|---|
| `GENERATION_TIMEOUT` | `Duration::from_secs(120)` |
| `RESEARCH_TIMEOUT` | `Duration::from_secs(60)` |
| `MAXIMUM_RESEARCH_RESPONSE_BYTES` | `65_536` |

**Types.** `FactStatus` is an enum whose `serde` renames are the four documented lowercase strings,
with a `Display` implementation for the CLI. `FactReview`, `ProposedAddition`, `Source`, and
`ResearchResult` derive `Serialize`/`Deserialize` with `#[serde(rename_all = "camelCase")]`, so the
JSON contract and the Rust field names stay in sync automatically.

**Prompt.** `build_research_prompt(approved_facts)` serializes the facts with `serde_json` and asks
for `search` before `readArticle`, at most three search results, one article retrieval, at most
three short additions, canonical `https://en.wikipedia.org/wiki/...` URLs, one review per supplied
fact in the same order, and no addition marked approved.

**Parser.** `parse_research_result` enforces the byte limit, deserializes with `serde_json`, then
hands off to `validate_research_result`, which returns `StudioError` for any of:

| Condition | Reason |
|---|---|
| `completed` false | A result that did not finish is not a result |
| A `failure_message` on a completed result | A completed result cannot report failure |
| A review count that differs from the facts, or a review whose `fact` differs from the fact at that position | One review per supplied fact, in order |
| A blank `explanation` | Every verdict must be explainable |
| `Supported` or `Contradicted` without a title and canonical URL | Evidence claims require provenance |
| Any non-canonical `evidence_url` | Provenance must be citable |
| More than three additions | Bounded proposals |
| An addition with a blank fact, a fact longer than `MAXIMUM_FACT_LENGTH`, a blank source title, or a non-canonical URL | Provenance is required |
| An addition whose source is not in `consulted_sources` | No invented provenance |
| A consulted source with a blank title or non-canonical URL | Sources must be citable |

Every accepted addition has `approved` forced to `false`. `is_canonical_wikipedia_url` requires the
`https://en.wikipedia.org/wiki/` prefix, a non-empty article segment, and no `?` or `#`.

**Lifecycle.** `research_wikipedia(client, approved_facts, model)` returns a `ResearchResult` and
never an error:

1. `build_exhibit_prompt` runs first, so an input that could not be generated from is rejected
   before Wikipedia is contacted.
2. `client.start()` failure stops the client and returns `incomplete_research`.
3. The session is created, the prompt is sent with `RESEARCH_TIMEOUT`, and the session is
   disconnected inside the same async block.
4. `client.stop()` runs after that block on every path. A failed stop produces an incomplete result
   rather than a silent success.
5. Any error becomes `incomplete_research`, which marks every fact `not checked` and preserves the
   message.

**Approval helper.** `approved_facts_with_additions(original_facts, additions)` returns the original
facts plus only the additions whose `approved` is `true`, and re-applies the fact count and length
limits through `build_exhibit_prompt`.

## 3. Replace the entrypoint

```bash
cp finished/rust/museum-exhibit-studio/src/main.rs museum-workshop-app/src/main.rs
```

The CLI keeps the step 6 flow and inserts the approval gate:

1. Print the Apollo 11 facts and ask `Use these facts? [Y/n]`, reading custom facts on `n`, then
   validate them with `build_exhibit_prompt` before anything else runs.
2. `read_default_no("\nRun Wikipedia research?")` asks `[y/N]`. Anything other than `y` skips
   research entirely, so the MCP server is never started.
3. Research runs on its own `CopilotCuratorClient`, separate from the generation client.
4. `review_research` prints each fact as `- <status>: <fact>`, its evidence title and URL when
   present, and its explanation, then asks `Approve this addition? [y/N]` for each proposed
   addition.
5. `remaining_slots` starts at `MAXIMUM_FACT_COUNT` minus the original fact count. When it reaches
   zero the CLI states that the 20-fact generation limit is reached and stops offering approvals.
6. When research did not complete, print
   `Wikipedia research was not completed. Generating from the original approved facts only.` and the
   failure message, then continue with the original facts.
7. `approved_facts_with_additions` builds the generation input, `generate_exhibit` runs on the
   unchanged tool-free session, and `print_validation` prints the structural result and the
   grounding disclaimer.
8. `print_sources` prints `Consulted Wikipedia sources:` after the exhibit, and prints nothing when
   there are none.
9. `main` maps a timeout through `is_timeout_error` to the two-minute message and exits with status
   1; any other error prints `Could not generate the exhibit: <error>`.

## Build and run

```bash
cargo check --manifest-path museum-workshop-app/Cargo.toml
cargo run --manifest-path museum-workshop-app/Cargo.toml
```

`--locked` is not used from step 1 onward, because renaming the package and adding these direct
dependencies both update `Cargo.lock`. The run needs an authenticated GitHub Copilot CLI, Node.js on
`PATH` so the research session can launch `npx -y wikipedia-mcp@1.0.3`, and network access to
Wikipedia. Set `COPILOT_MODEL` to choose a model.

## Verify

1. Answer `N` to the research question. The output matches step 6 and no MCP server starts.
2. Answer `y`. Every supplied fact appears with one of the four statuses and an explanation.
3. Reject an addition and confirm its wording appears nowhere in the exhibit.
4. Approve an addition and confirm its article title and URL still appear under
   `Consulted Wikipedia sources:` after the exhibit.
5. Disconnect from the network and answer `y`. The CLI reports that research was not completed,
   every fact is `not checked`, and generation proceeds from the original facts.
6. Confirm `create_session_configuration` still sets `config.available_tools = Some(Vec::new())`, so
   the session that writes exhibit copy has no way to reach Wikipedia.
