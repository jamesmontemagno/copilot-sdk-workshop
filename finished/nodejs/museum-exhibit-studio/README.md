# Museum Exhibit Studio

This completed Node.js/TypeScript sample now has two source files:

- `src/curator.ts` contains the pre-built helper module: approved facts, bounded
  streaming, deterministic validation, scoped Wikipedia permissions, the optional
  `exhibit.html` write permission, and terminal helpers.
- `src/index.ts` contains the learner-authored orchestration: prompts, session
  configs, fact-set selection, optional research, generation, validation, and the
  optional HTML capstone.

## Run the sample

```bash
cd finished/nodejs/museum-exhibit-studio
npm ci
npm start
```

Use `npm run build` to type-check without contacting a model.

## Safety shape

Generation allowlists exactly one application-owned tool, `approved_fact_lookup`,
which returns the bounded approved facts. Optional Wikipedia
research runs in a separate session with scoped `search` and `readArticle` tools,
a deny-by-default permission handler, cited `## Sources`, and no JSON contract or
proposed-addition approval loop. Research notes are shown to the educator but are
never merged into the approved facts.

After generation, deterministic checks report structure, narrative length, visitor
questions, and prohibited vocabulary. If selected, the HTML step exposes only
`builtin:apply_patch` and approves writing exactly `exhibit.html` in the app
directory.

This is the application a learner ends up with after the museum lessons, not a separate reference
architecture. The entrypoint keeps one small session runner that starts the client, creates the
session, enforces the timeout, rejects blank output, and cleans up on every path; the research,
generation, and optional HTML steps reuse it with different session configurations. Follow the
track from
[`workshop/museum-00-preflight.md`](https://github.com/jamesmontemagno/copilot-sdk-workshop/blob/main/workshop/museum-00-preflight.md).
