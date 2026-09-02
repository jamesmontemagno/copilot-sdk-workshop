# Museum Exhibit Studio

This Python sample uses the GitHub Copilot SDK as a focused museum exhibit
studio. The finished app now has two modules:

- `curator.py` contains the pre-built workshop helpers: approved fact sets,
  bounded fact validation, streaming, deterministic structural checks, scoped
  Wikipedia permissions, scoped `exhibit.html` write permission, and terminal
  helpers.
- `main.py` contains the learner-authored orchestration: prompts, session
  configuration, console flow, validation, and optional HTML generation.

## Run the sample

From this directory, create an environment and install the pinned dependency:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

Set `COPILOT_MODEL` to select a model; otherwise the runtime chooses its
default. An authenticated GitHub Copilot CLI is required.

Wikipedia research requires Node.js because the research session launches the
pinned `wikipedia-mcp@1.0.3` package through `npx`. Declining research does not
start the MCP server.

Check the source without contacting a model:

```powershell
python -m py_compile *.py
```

## What the sample teaches

Generation allowlists exactly one application-owned tool,
`approved_fact_lookup`, which returns the bounded approved facts. It also uses a
replace-mode
curator system message, streaming, a 120-second timeout, and deterministic
structural validation. Imported modules have no side effects; `main.py` only
runs behind the `if __name__ == "__main__"` guard.

Optional Wikipedia research is intentionally separate from generation. The
research session exposes only scoped Wikipedia search and article-read tools,
uses a deny-by-default permission handler, asks for a prose summary, and parses
a trailing `## Sources` list. Research notes and cited sources are shown to the
human, but they are never merged into the approved facts used to generate the
exhibit. There is no strict JSON contract and no proposed-addition approval
loop.

After validation, the optional HTML capstone exposes only `builtin:apply_patch`
and approves writing exactly `exhibit.html` in the application working
directory. The prompt asks for one standalone semantic HTML file with embedded
CSS and JavaScript, a human-review caveat, and an accessible question filter.

Prompt guidance and structural validation are not authorization or grounding
boundaries. Generated claims still require human review or a separate evaluator.

## Manual check

1. Run with each built-in fact set and confirm the selected facts print before
   generation.
2. Confirm the exhibit has one title, a 100-140-word narrative, and three
   visitor questions.
3. Inspect the validation summary and grounding disclaimer.
4. Decline research and confirm the only tool event is `approved_fact_lookup`.
5. Opt into research and confirm sources print after the exhibit, not inside it.
6. Opt into `exhibit.html` and confirm only that file is written.

This is the application a learner ends up with after the museum lessons, not a separate reference
architecture. The entrypoint keeps one small session runner that starts the client, creates the
session, enforces the timeout, rejects blank output, and cleans up on every path; the research,
generation, and optional HTML steps reuse it with different session configurations. Follow the
track from
[`workshop/museum-00-preflight.md`](https://github.com/jamesmontemagno/copilot-sdk-workshop/blob/main/workshop/museum-00-preflight.md).
