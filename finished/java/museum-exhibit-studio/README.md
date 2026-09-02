# Museum Exhibit Studio

This Maven CLI sample uses the GitHub Copilot SDK as a focused, non-software-engineering agent
harness. A museum educator can accept the Apollo 11 fixture or enter another approved fact set,
optionally research those facts through a tightly allowlisted Wikipedia MCP session, approve
sourced additions one by one, generate visitor-facing exhibit copy, and inspect deterministic
structural checks.

## Run

From this directory:

```bash
mvn compile exec:java
```

Set `COPILOT_MODEL` to select a model; otherwise the Copilot runtime chooses its default. The sample
requires an authenticated GitHub Copilot CLI.

Run the fake-based tests without contacting a model:

```bash
mvn test
```

The tests start only the deterministic local mock MCP fixture. They do not contact Wikipedia.

## What it demonstrates

`CuratorPrompts.SYSTEM_MESSAGE` completely replaces the default system message and contains the
durable curator policy. Approved facts are separate task data in the user prompt.

Prompt guidance is not an authorization boundary, so the application also:

- keeps generation tool-free with an empty available-tools list and a reject-all permission handler;
- limits research to `wikipedia-search` and `wikipedia-readArticle` with an exact permission handler;
- caps research at 45 seconds, retries malformed formatting once for 15 seconds, and limits the
  accepted response to 50,000 characters;
- validates every review status, source title, and canonical Wikipedia URL before presenting it;
- requires an explicit, default-no decision before a proposed addition reaches generation;
- bounds input to 20 facts of at most 500 characters each;
- uses the SDK's 120-second response timeout;
- rejects an empty response;
- disconnects the session and stops the client on success and failure; and
- checks one H1, required sections, a 100-140-word narrative, exactly three numbered questions
  ending in `?`, and prohibited software vocabulary.

The validator cannot prove semantic factual grounding. Generated claims still require human review
or a separate evaluator.
