# Museum Exhibit Studio

This Python sample uses the GitHub Copilot SDK as a focused, non-software-engineering
agent harness. A museum educator can accept the Apollo 11 fixture or enter another
approved fact set, optionally research it through a constrained Wikipedia MCP session,
approve sourced additions, then generate visitor-facing copy and inspect deterministic
checks.

## Run the sample

From this directory, create an environment and install the pinned dependency:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

Set `COPILOT_MODEL` to select a model; otherwise the runtime chooses its default. An
authenticated GitHub Copilot CLI is required.

Wikipedia research also requires Node.js because the research session launches the
pinned `wikipedia-mcp@1.0.3` package through `npx`. Declining research does not start
the MCP server.

Run the mocked tests without contacting a model:

```bash
python -m unittest discover -s tests -v
```

## What the sample teaches

`SYSTEM_MESSAGE` is the complete durable curator definition and uses replace mode.
Approved facts remain in the separate user prompt because they are task data. Hard
controls expose no tools, bound facts to 20 items of 500 characters each, enforce a
120-second timeout, and disconnect the session and stop the client on every outcome.
The validator checks one H1, required sections, a 100-140-word narrative, exactly
three numbered questions ending in `?`, and prohibited software vocabulary.

The optional research stage uses a separate 45-second session. It exposes only
Wikipedia search and article retrieval, rejects all other permission requests, limits
the structured response to 65,536 characters, validates every status and canonical
source URL, and falls back to the original facts when research is incomplete. Proposed
facts remain outside the generation prompt until the educator explicitly approves them.
Consulted sources print after the exhibit rather than inside its Markdown.

Prompt guidance and structural validation are not authorization or grounding
boundaries. Generated claims still require human review or a separate evaluator.

## Manual check

1. Run with the default Apollo 11 facts.
2. Confirm one title, a 100-140-word narrative, and three questions.
3. Inspect the validation summary and grounding disclaimer.
4. Review the prose for claims absent from the approved facts.
5. Decline research and confirm no tool events or permission requests appear.
6. Opt into research and confirm every original fact receives a visible status.
7. Reject and approve proposed additions, then confirm only approved facts reach the
   exhibit while consulted sources remain separately visible.
