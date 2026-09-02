# Museum Exhibit Studio

This Go sample uses the GitHub Copilot SDK as a focused, non-software-engineering agent harness. A
museum educator can accept the Apollo 11 fixture or enter another approved fact set, optionally
review Wikipedia research, explicitly approve sourced additions, generate visitor-facing exhibit
copy, and inspect deterministic structural checks.

## Run the sample

From this directory:

```bash
go run .
```

Set `COPILOT_MODEL` to select a model; otherwise the runtime chooses its default. An authenticated
GitHub Copilot CLI is required.

Tests use fakes and a local mock MCP process; they never contact a model or Wikipedia:

```bash
go test -mod=readonly ./...
```

## What the sample teaches

The complete curator system message replaces the SDK default, while approved facts remain in the
separate task prompt. Exhibit generation exposes no tools, bounds facts to 20 entries of 500
characters, and limits generation to 120 seconds. Optional research runs in a separate 45-second
session with only one Wikipedia search followed by one article read. Its strict JSON parser caps
responses at 64 KiB, accepts at most two additions and one consulted source, validates statuses and
canonical source URLs, and falls back to `not checked` without changing the original facts. Every
path disconnects an established session and stops the client. A deterministic validator checks one
H1, required sections, a 100-140-word narrative, three numbered questions ending in `?`, and
prohibited software terms.

Prompt guidance is not an authorization boundary. The research permission handler allows only the
named Wikipedia server and its two read-only-by-contract tools, rejects managed-approval requests,
enforces search-before-read order and call counts, and denies everything else. Structural validation
still cannot prove factual grounding, so generated claims require human review.
