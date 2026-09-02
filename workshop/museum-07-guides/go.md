# Go guide: Wikipedia MCP

Final implementation reference for museum step 7 on the Go track. It assumes `museum-workshop-app`
is the application you built through [Run and review the exhibit](../museum-06-run-review.md) and
then extended in [Wikipedia MCP](../museum-07-wikipedia-grounding.md) with
`createResearchSessionConfiguration` and `newWikipediaPermissionHandler`.

The completed counterpart of every file below is in `finished/go/museum-exhibit-studio`.

## Final layout

| File in `museum-workshop-app` | Introduced in | Responsibility |
|---|---|---|
| `go.mod` | Preflight | Module definition, `github.com/github/copilot-sdk/go v1.0.11` |
| `go.sum` | Preflight | Deterministic module verification |
| `prompts.go` | Steps 1 and 3 | Curator policy, Apollo 11 facts, fact limits, `buildExhibitPrompt` |
| `validator.go` | Step 4 | Structural result types and `validateExhibit` |
| `service.go` | Steps 2, 5, 7 | Client/session interfaces, SDK adapter, both session configurations, permission handler, `Generate` |
| `research.go` | Step 7 | Research contract, prompt builder, strict parser, approval helper |
| `main.go` | Steps 1-7 | Interactive CLI, approval gate, printed sources |

`curator_runtime.go` from the starter was removed in step 2 when `service.go` took over the same
package-level types; keeping both files would be a duplicate-declaration compile error. The
completed project has no such file either. The only remaining difference from the completed project
is the module path in `go.mod`, which does not affect a single-package `main` program.

## Files that already match

After step 6, two files are byte-identical to their completed counterparts. Confirm before you
continue:

```bash
diff museum-workshop-app/prompts.go finished/go/museum-exhibit-studio/prompts.go
diff museum-workshop-app/validator.go finished/go/museum-exhibit-studio/validator.go
```

Each command must print nothing. A difference means an earlier step was edited by hand; take the
completed file as the correct version.

## 1. Complete the research contract

Step 7 created `museum-workshop-app/research.go` with the limits and the research policy. Replace it
with the completed file, which keeps those constants and adds the rest:

```bash
cp finished/go/museum-exhibit-studio/research.go museum-workshop-app/research.go
```

`research.go` holds the whole research contract.

**Limits.**

| Constant | Value |
|---|---|
| `researchTimeout` | `45 * time.Second` |
| `maximumResearchResponse` | `64 * 1024` bytes |
| `maximumResearchAdditions` | `2` |
| `maximumConsultedSources` | `1` |

**Policy.** `researchSystemMessage` is the research assistant policy from the lesson plus two
formatting rules that keep the response parseable: the first output character must be `{`, the last
must be `}`, and Markdown fences are forbidden.

**Types.** `FactStatus` is a string type with the four documented constants. `FactReview`,
`ProposedAddition`, `Source`, and `ResearchResult` carry `json` tags matching the camelCase contract,
with `*string` for the nullable evidence fields.

**`museumExhibitService.Research`.** It returns a `ResearchResult` and never an error, because a
failure is a research outcome rather than a program fault. Its sequence is:

1. `buildResearchPrompt` normalizes and bounds the facts first, so an input that could not be
   generated from is rejected before Wikipedia is contacted.
2. Start the client; on failure, stop it and return `incompleteResearch` with both errors joined.
3. Create the session from `createResearchSessionConfiguration(model)`; on failure, stop and return
   an incomplete result.
4. Send the prompt under a `context.WithTimeout` of `researchTimeout`.
5. Disconnect the session and stop the client, joining both cleanup errors, before inspecting the
   response. A cleanup failure produces an incomplete result rather than a silent success.
6. Parse with `parseResearchResult`, converting any failure into `incompleteResearch`.

**Parser.** `parseResearchResult(content, approvedFacts)` uses a `json.Decoder` with
`DisallowUnknownFields`, then `ensureJSONEnd` to reject trailing JSON. It rejects:

| Condition | Reason |
|---|---|
| More than `maximumResearchResponse` bytes | Bounded input before parsing |
| Any unknown field, or trailing content after the object | Contract violation |
| `Completed` false, or a `FailureMessage` present | A completed result cannot report failure |
| A review count that differs from the supplied facts | One review per supplied fact |
| A review whose `Fact` differs from the supplied fact at that index | The researcher may not rewrite an input |
| A status outside the four constants | Only documented statuses exist |
| A blank `Explanation` | Every verdict must be explainable |
| `supported` or `contradicted` without a title and canonical URL | Evidence claims require provenance |
| An addition with a blank fact, a blank source title, or a non-canonical URL | Provenance is required |
| More than `maximumResearchAdditions` additions, or more than `maximumConsultedSources` sources | Bounded proposals |
| A consulted source with a blank title or a non-canonical URL | Sources must be citable |

Every parsed addition has `Approved` forced to `false`, whatever the response said.
`canonicalWikipediaURL` requires `https`, host `en.wikipedia.org`, a `/wiki/` path, and no query or
fragment.

**Fallback and approval.** `incompleteResearch(approvedFacts, err)` returns every fact as
`not checked` with `Completed: false` and the error text preserved.
`approvedResearchFacts(original, additions)` returns the original facts plus only the additions
whose `Approved` is `true`.

## 2. Replace the service

```bash
cp finished/go/museum-exhibit-studio/service.go museum-workshop-app/service.go
```

This keeps `Generate`, `createSessionConfiguration` with `AvailableTools: []string{}`, and
`generationTimeout = 120 * time.Second` exactly as they were after step 5, together with the
research session configuration and permission handler you added in the lesson. It imports
`github.com/github/copilot-sdk/go/rpc` for the permission decision types.

The handler is the fail-closed control. It rejects anything that is not a
`copilot.PermissionRequestMCP`, anything whose `ServerName` is not `wikipedia`, anything the runtime
marks with `ManagedApprovalRequired`, any tool other than the two allowed names, a second `search`,
a `readArticle` before any `search`, and a second `readArticle`. Its counters live in the closure,
so the budget is per session and enforced by application code.

## 3. Replace the entrypoint

```bash
cp finished/go/museum-exhibit-studio/main.go museum-workshop-app/main.go
```

`runCLI(bufio.NewReader(os.Stdin))` keeps the step 6 flow and inserts the approval gate:

1. Print the Apollo 11 facts and ask `Use these facts? [Y/n]`, reading custom facts on `n`.
2. Ask `Run Wikipedia research? [y/N]`. Anything other than `y` skips research entirely, so the MCP
   server is never started.
3. Call `Research` on a service built with its own `newCopilotCuratorClient()`, separate from the
   client used for generation.
4. `printResearch` prints each fact with `[status]`, its explanation, and its source when present,
   then the numbered proposed additions with their sources, and the failure detail when there is
   one.
5. On completion, `approveAdditions` asks `Approve addition N? [y/N]` for each addition and sets
   `Approved` only on `y`; `approvedResearchFacts` then builds the generation input.
6. Otherwise print
   `Wikipedia research was not completed. Generating from the original approved facts only.` and
   continue with the original facts.
7. Generate with the unchanged tool-free service, print the exhibit, print the structural result
   with `printValidation`, then print `Consulted Wikipedia sources:` with `printSources` after the
   exhibit.
8. Return the two-minute message when `errorsIsDeadline` matches `context.DeadlineExceeded`;
   `main` prints the error and exits with status 1.

`printSources` prints nothing when there are no consulted sources, so a skipped or failed research
stage cannot leave a misleading citation list behind.

## Build and run

```bash
go -C museum-workshop-app build -mod=readonly ./...
go -C museum-workshop-app run .
```

`-mod=readonly` keeps `go.mod` and `go.sum` unchanged. The run needs an authenticated GitHub Copilot
CLI, Node.js on `PATH` so the research session can launch `npx -y wikipedia-mcp@1.0.3`, and network
access to Wikipedia. Set `COPILOT_MODEL` to choose a model.

## Verify

1. Answer `N` to the research question. The output matches step 6 and no MCP server starts.
2. Answer `y`. Every supplied fact appears with one of the four statuses and an explanation.
3. Reject an addition and confirm its wording appears nowhere in the exhibit.
4. Approve an addition and confirm its article title and URL still appear under
   `Consulted Wikipedia sources:` after the exhibit.
5. Disconnect from the network and answer `y`. The CLI reports that research was not completed,
   every fact is `not checked`, and generation proceeds from the original facts.
6. Confirm `createSessionConfiguration` still sets `AvailableTools: []string{}`, so the session that
   writes exhibit copy has no way to reach Wikipedia.
