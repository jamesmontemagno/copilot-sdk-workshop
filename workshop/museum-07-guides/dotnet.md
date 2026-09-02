# .NET guide: Wikipedia MCP

Final implementation reference for museum step 7 on the .NET track. It assumes
`museum-workshop-app` is the application you built through
[Run and review the exhibit](../museum-06-run-review.md) and then extended in
[Wikipedia MCP](../museum-07-wikipedia-grounding.md) with `CreateResearchSessionConfiguration` and
`WikipediaPermissionHandler.cs`.

The completed counterpart of every file below is in `finished/dotnet/museum-exhibit-studio`.

## Final layout

| File in `museum-workshop-app` | Introduced in | Responsibility |
|---|---|---|
| `museum-exhibit-studio.csproj` | Preflight | `net10.0` executable, `GitHub.Copilot.SDK` 1.0.11, lock file |
| `packages.lock.json` | Preflight | Deterministic restore |
| `CuratorRuntime.cs` | Preflight | `ICuratorClient` / `ICuratorSession` and the `CopilotClient` adapter |
| `CuratorPrompts.cs` | Steps 1 and 3 | Curator policy, Apollo 11 facts, fact limits, `BuildExhibitPrompt` |
| `ExhibitValidator.cs` | Step 4 | Structural result records and `ExhibitValidator.Validate` |
| `MuseumExhibitService.cs` | Steps 2, 5, 7 | Both session configurations, `GenerateAsync`, `ResearchAsync` |
| `WikipediaPermissionHandler.cs` | Step 7 | Deny-by-default MCP permission decisions |
| `ResearchModels.cs` | Step 7 | Research contract types, approval helper, strict parser |
| `Program.cs` | Steps 1-7 | Interactive CLI, approval gate, printed sources |

`museum-exhibit-studio.csproj` keeps `RestorePackagesWithLockFile` from the starter, which the
completed project does not set. Everything else converges on the completed implementation.

## Files that already match

After step 6, three files are byte-identical to their completed counterparts. Confirm before you
continue:

```bash
diff museum-workshop-app/CuratorRuntime.cs finished/dotnet/museum-exhibit-studio/CuratorRuntime.cs
diff museum-workshop-app/CuratorPrompts.cs finished/dotnet/museum-exhibit-studio/CuratorPrompts.cs
diff museum-workshop-app/ExhibitValidator.cs finished/dotnet/museum-exhibit-studio/ExhibitValidator.cs
```

Each command must print nothing. A difference means an earlier step was edited by hand; take the
completed file as the correct version.

## 1. Add the research contract

```bash
cp finished/dotnet/museum-exhibit-studio/ResearchModels.cs museum-workshop-app/ResearchModels.cs
```

`ResearchModels.cs` contains four kinds of thing:

**Contract types.** `FactReviewStatus` is an enum whose JSON names are the exact lowercase strings
`supported`, `contradicted`, `not found`, and `not checked`, applied with
`[JsonStringEnumMemberName]`. `FactReview`, `ProposedAddition`, `ResearchSource`, and
`ResearchResult` are `sealed record` types that mirror the contract in the step 7 lesson.

**The incomplete result.** `ResearchResult.Incomplete(facts, failureMessage)` returns every supplied
fact as `NotChecked` with no evidence, `Completed = false`, and the failure message preserved. This
is what the service returns for every failure, so an outage can never look like a clean review.

**The approval helper.** `ResearchApproval.BuildApprovedFacts(originalFacts, additions)` concatenates
the original facts with the `Fact` of each addition whose `Approved` is `true`, then calls
`CuratorPrompts.BuildExhibitPrompt` on the result purely to re-apply the 20-fact and 500-character
limits before generation.

**The strict parser.** `ResearchResultParser.Parse(content, suppliedFacts)` throws `JsonException`
rather than repairing anything. It rejects:

| Condition | Reason |
|---|---|
| `Completed` is false, or `FailureMessage` is set | A completed result cannot report failure |
| Review count differs from supplied facts, or any fact is missing or added | One review per supplied fact, ordinal string comparison |
| An undefined `Status` | Only the four documented statuses exist |
| A blank `Explanation` | Every verdict must be explainable |
| `Supported` or `Contradicted` without a title and canonical URL | Evidence claims require provenance |
| More additions than `MaximumProposedAdditions`, or than the remaining fact slots | Additions cannot overflow the fact budget |
| An addition with `Approved = true` on arrival | Approval is the educator's decision, not the model's |
| A consulted source without a title or canonical URL | Sources must be citable |

`IsCanonicalWikipediaUrl` accepts only `https`, a host ending in `.wikipedia.org`, and either a
`/wiki/` path or a `/?curid=<positive integer>` article identifier.

## 2. Replace the service

```bash
cp finished/dotnet/museum-exhibit-studio/MuseumExhibitService.cs museum-workshop-app/MuseumExhibitService.cs
```

This keeps `GenerateAsync` and `CreateSessionConfiguration` from step 5 exactly as they were,
including `AvailableTools = []`, keeps the research constants, policy, and session configuration you
added in the step 7 lesson, and adds the bounded research method:

| Member | Value or behavior |
|---|---|
| `GenerationTimeout` | `TimeSpan.FromMinutes(2)` |
| `ResearchTimeout` | `TimeSpan.FromSeconds(45)` |
| `MaximumResearchResponseLength` | `32_000` characters |
| `MaximumProposedAdditions` | `3` |
| `ResearchSystemMessage` | The research assistant policy from the lesson |
| `CreateResearchSessionConfiguration` | The scoped MCP server, the two-tool allowlist, and `WikipediaPermissionHandler.Create()` |
| `ResearchAsync` | The bounded research lifecycle |

`ResearchAsync` never throws. Its sequence is:

1. Normalize the facts and run them through `CuratorPrompts.BuildExhibitPrompt` first, so an input
   that could not be generated from is rejected before Wikipedia is contacted.
2. Start the client, create the research session, and send the research prompt with
   `ResearchTimeout`.
3. Reject a blank response and a response longer than `MaximumResearchResponseLength`.
4. Parse with `ResearchResultParser.Parse`.
5. Convert any exception into `ResearchResult.Incomplete` with the message attached.
6. Stop the client in a `finally` block, and if the stop itself fails, return an incomplete result
   describing the cleanup failure instead of reporting success.

`BuildResearchPrompt` serializes the facts as JSON, instructs the researcher to call `search` before
`readArticle`, to retrieve only the single most relevant article, to skip retrieval when search
returns nothing relevant, and to return one JSON object in the exact camelCase shape of the
contract.

## 3. Replace the entrypoint

```bash
cp finished/dotnet/museum-exhibit-studio/Program.cs museum-workshop-app/Program.cs
```

The CLI keeps the step 6 flow and inserts the approval gate before generation:

1. Print the Apollo 11 facts and ask `Use these facts? [Y/n]`, reading custom facts on `n`.
2. Ask `Run Wikipedia research? [y/N]`. Anything other than `y` skips research entirely, so the MCP
   server is never started.
3. Call `studio.ResearchAsync(facts, COPILOT_MODEL)` and print the result with `PrintResearch`:
   each fact with its status through `FormatStatus`, its explanation, and its evidence title and
   URL when present, then the numbered proposed additions with their sources.
4. When `research.Completed` is true, ask `Approve addition N? [y/N]` for each addition and record
   the answer with `addition with { Approved = true }` only on `y`.
5. When it is false, print
   `Wikipedia research was not completed. Generating from the original approved facts only.` and
   continue.
6. Build the generation input with `ResearchApproval.BuildApprovedFacts(facts, research?.Additions ?? [])`.
7. Call the unchanged `studio.GenerateAsync`, print the exhibit, print the structural result with
   `PrintValidation`, then print consulted sources with `PrintSources` after the exhibit.
8. Return `1` after a `TimeoutException` or any other failure, with the two-minute message for the
   timeout case.

`PrintSources` prints nothing unless research completed and consulted at least one source, so a
skipped or failed research stage cannot leave a misleading citation list behind.

## 4. Confirm the permission handler

`WikipediaPermissionHandler.cs` was added in the lesson. It is identical to the completed file:

```bash
diff museum-workshop-app/WikipediaPermissionHandler.cs finished/dotnet/museum-exhibit-studio/WikipediaPermissionHandler.cs
```

It approves once only when the request is a `PermissionRequestMcp` whose `ServerName` is exactly
`wikipedia` and whose tool name, with any `wikipedia-` prefix removed, is `search` or `readArticle`.
Everything else is rejected with feedback. The `#pragma warning disable GHCP001` acknowledges that
custom permission decisions are an evaluation-only API in SDK 1.0.11; keep the pragma scoped to that
file.

## Build and run

```bash
dotnet build museum-workshop-app
dotnet run --project museum-workshop-app
```

The run needs an authenticated GitHub Copilot CLI, Node.js on `PATH` so the session can launch
`npx -y wikipedia-mcp@1.0.3`, and network access to Wikipedia. Set `COPILOT_MODEL` to choose a
model.

## Verify

1. Answer `N` to the research question. The output matches step 6 and no MCP server starts.
2. Answer `y`. Every supplied fact appears with one of the four statuses and an explanation.
3. Reject an addition and confirm its wording appears nowhere in the exhibit.
4. Approve an addition and confirm its article title and URL still appear under
   `Consulted Wikipedia sources:` after the exhibit.
5. Disconnect from the network and answer `y`. The CLI reports that research was not completed,
   every fact is `not checked`, and generation proceeds from the original facts.
6. Confirm `CreateSessionConfiguration` still sets `AvailableTools = []`, so the session that writes
   exhibit copy has no way to reach Wikipedia.
