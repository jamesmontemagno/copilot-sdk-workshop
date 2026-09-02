# Node.js/TypeScript guide: Wikipedia MCP

Final implementation reference for museum step 7 on the Node.js track. It assumes
`museum-workshop-app` is the application you built through
[Run and review the exhibit](../museum-06-run-review.md) and then extended in
[Wikipedia MCP](../museum-07-wikipedia-grounding.md) with `createResearchSessionConfiguration` and
`createWikipediaPermissionHandler`.

The completed counterpart of every file below is in `finished/nodejs/museum-exhibit-studio`.

## Final layout

| File in `museum-workshop-app` | Introduced in | Responsibility |
|---|---|---|
| `package.json` | Preflight | ESM project, `@github/copilot-sdk` 1.0.11, `@github/copilot` 1.0.80, `tsx`, `typescript` |
| `package-lock.json` | Preflight | Deterministic install |
| `tsconfig.json` | Preflight | `NodeNext`, `ES2022`, `strict`, `noUncheckedIndexedAccess` |
| `src/prompts.ts` | Steps 1 and 3 | Curator policy, Apollo 11 facts, fact limits, `buildExhibitPrompt` |
| `src/validator.ts` | Step 4 | Structural result classes and `validateExhibit` |
| `src/service.ts` | Steps 2, 5, 7 | Client/session interfaces, both session configurations, permission handler, `MuseumExhibitService` |
| `src/research.ts` | Step 7 | Research contract, prompt builder, strict parser, approval helper |
| `src/index.ts` | Steps 1-7 | Interactive CLI, approval gate, printed sources |

`src/runtime.ts` from the starter was removed in step 2 when `src/service.ts` took over the SDK
boundary. The completed project has no such file either. The only remaining difference from the
completed project is the `name` field in `package.json`, which does not affect behavior.

## Files that already match

After step 6, two files are byte-identical to their completed counterparts. Confirm before you
continue:

```bash
diff museum-workshop-app/src/prompts.ts finished/nodejs/museum-exhibit-studio/src/prompts.ts
diff museum-workshop-app/src/validator.ts finished/nodejs/museum-exhibit-studio/src/validator.ts
```

Each command must print nothing. A difference means an earlier step was edited by hand; take the
completed file as the correct version.

## 1. Complete the research contract

Step 7 created `museum-workshop-app/src/research.ts` with the limits and the research policy.
Replace it with the completed module, which keeps those exports and adds the rest:

```bash
cp finished/nodejs/museum-exhibit-studio/src/research.ts museum-workshop-app/src/research.ts
```

`src/research.ts` is the whole research contract in one module.

**Limits.**

| Export | Value |
|---|---|
| `researchTimeoutMs` | `45_000` |
| `maximumResearchResponseBytes` | `65_536` |
| `maximumResearchSearchCalls` | `5` |
| `maximumResearchArticleReads` | `1` |

**Policy.** `researchSystemMessage` is the research assistant policy from the lesson, applied in
`replace` mode so the researcher never inherits curator or coding-agent defaults.

**Types.** `factReviewStatuses` is the literal tuple
`["supported", "contradicted", "not found", "not checked"]`, and `FactReviewStatus` is derived from
it, so an unknown status cannot type-check. `FactReview`, `ProposedAddition`, `Source`, and
`ResearchResult` mirror the contract in the lesson.

**Prompt.** `buildResearchPrompt(approvedFacts)` normalizes and bounds the facts through
`normalizeFacts`, then returns both the normalized `facts` array and the `prompt`. Returning the
normalized facts matters: the parser compares reviews against exactly the strings that were sent.
The prompt requires `search` before `readArticle`, at most five searches and exactly one article
read, no more than three additions, separate arrays for supplied facts and additions, and raw JSON
in the documented shape.

**Parser.** `parseResearchResult(content, suppliedFacts)` throws rather than repairing. It rejects:

| Condition | Reason |
|---|---|
| More than `maximumResearchResponseBytes` of UTF-8 | Bounded input before parsing |
| Content that is not a JSON object, or missing any of the three arrays | Contract violation |
| `completed !== true` or `failureMessage !== null` | A completed result cannot report failure |
| A review count that differs from the supplied facts, or reviews that do not map one-to-one | One review per supplied fact |
| A status outside `factReviewStatuses` | Only documented statuses exist |
| An evidence title without a URL, or a URL without a title | Provenance is a pair |
| `supported` or `contradicted` without evidence | Evidence claims require provenance |
| A consulted-source count other than `maximumResearchArticleReads` | Exactly one article was permitted |
| Evidence or an addition referencing a source that was not consulted | No invented provenance |
| An addition longer than `maximumFactLength`, or with `approved !== false` | Approval is the educator's decision |
| More additions than `min(3, maximumFactCount - suppliedFacts.length)` | Additions cannot overflow the fact budget |

`isWikipediaUrl` parses with `new URL` and requires `https:`, a hostname ending in `.wikipedia.org`,
and a `/wiki/` path.

**Fallback and approval.** `incompleteResearch(suppliedFacts, failureMessage)` returns every fact as
`not checked` with `completed: false`. `selectApprovedFacts(originalFacts, additions)` returns the
original facts plus only the additions whose `approved` is `true`, and re-applies the fact count and
length limits.

## 2. Replace the service

```bash
cp finished/nodejs/museum-exhibit-studio/src/service.ts museum-workshop-app/src/service.ts
```

This keeps `generate`, `createSessionConfiguration` with `availableTools: []`, and
`generationTimeoutMs = 120_000` exactly as they were after step 5, and adds `research`:

1. `buildResearchPrompt` normalizes and bounds the facts before the client starts.
2. The client starts, the research session is created from
   `createResearchSessionConfiguration(model)`, and the prompt is sent with `researchTimeoutMs`.
3. A blank response throws `The researcher returned no result.`
4. `parseResearchResult` validates the payload.
5. Any thrown error becomes `incompleteResearch(facts, message)`; `research` never rejects.
6. The `finally` block disconnects the session inside its own `try`, with `this.client.stop()` in
   the inner `finally`, so a failed disconnect cannot skip the stop.

The permission handler you added in the lesson lives in this file and is wired through
`onPermissionRequest`. Its counters live in the closure, so the five-search and one-article budget
and the search-before-read order are enforced per session by application code.

## 3. Replace the entrypoint

```bash
cp finished/nodejs/museum-exhibit-studio/src/index.ts museum-workshop-app/src/index.ts
```

The CLI keeps the step 6 `node:readline/promises` flow and inserts the approval gate:

1. Print the Apollo 11 facts and ask `Use these facts? [Y/n]`, reading custom facts on `n`.
2. Ask `Run Wikipedia research? [y/N]`. Anything other than `y` skips research entirely, so the MCP
   server is never started.
3. Run `new MuseumExhibitService(createCopilotCuratorClient()).research(facts, process.env.COPILOT_MODEL)`
   in its own service instance, separate from the one that generates.
4. `printResearch` prints each fact with `[status]`, its explanation, and its source when present,
   then each proposed addition with its article title and URL.
5. On completion, ask `Approve addition "<fact>"? [y/N]` for each addition and set `approved` only
   on `y`, then build the generation input with `selectApprovedFacts`.
6. Otherwise print
   `Wikipedia research was not completed. Generating from the original approved facts only.` and,
   when present, the failure message.
7. Generate with the unchanged tool-free service, print the exhibit, print the structural result
   with `printValidation`, then print `Consulted Wikipedia sources:` after the exhibit.
8. On error, print the two-minute message when the message mentions a timeout, otherwise
   `Could not generate the exhibit: <message>`, and set `process.exitCode = 1`.
9. Close the terminal in `finally` on every path.

## Build and run

```bash
npm --prefix museum-workshop-app run build
npm --prefix museum-workshop-app start
```

`npm run build` is `tsc --noEmit`, so it type-checks without contacting a model. The run needs an
authenticated GitHub Copilot CLI and network access to Wikipedia; `npx` is already available because
this track ships Node.js. Set `COPILOT_MODEL` to choose a model.

## Verify

1. Answer `N` to the research question. The output matches step 6 and no MCP server starts.
2. Answer `y`. Every supplied fact appears with one of the four statuses and an explanation.
3. Reject an addition and confirm its wording appears nowhere in the exhibit.
4. Approve an addition and confirm its article title and URL still appear under
   `Consulted Wikipedia sources:` after the exhibit.
5. Disconnect from the network and answer `y`. The CLI reports that research was not completed,
   every fact is `not checked`, and generation proceeds from the original facts.
6. Confirm `createSessionConfiguration` still sets `availableTools: []`, so the session that writes
   exhibit copy has no way to reach Wikipedia.
