# Java/Maven guide: Wikipedia MCP

Final implementation reference for museum step 7 on the Java track. It assumes
`museum-workshop-app` is the application you built through
[Run and review the exhibit](../museum-06-run-review.md) and then extended in
[Wikipedia MCP](../museum-07-wikipedia-grounding.md) with
`createResearchSessionConfiguration` and `isAllowedWikipediaRequest`.

The completed counterpart of every file below is in `finished/java/museum-exhibit-studio`.

## Final layout

| File in `museum-workshop-app` | Introduced in | Responsibility |
|---|---|---|
| `pom.xml` | Preflight, step 7 | SDK 1.0.11, Jackson Databind, compiler and exec plugins |
| `src/main/java/workshop/CuratorRuntime.java` | Preflight | `CuratorClient` / `CuratorSession` and the `CopilotClient` adapter |
| `src/main/java/workshop/CuratorPrompts.java` | Steps 1 and 3 | Curator policy, Apollo 11 facts, fact limits, `buildExhibitPrompt` |
| `src/main/java/workshop/TitleValidation.java` | Step 4 | Title result record |
| `src/main/java/workshop/NarrativeValidation.java` | Step 4 | Narrative result record |
| `src/main/java/workshop/VisitorQuestionsValidation.java` | Step 4 | Visitor questions result record |
| `src/main/java/workshop/VocabularyValidation.java` | Step 4 | Prohibited vocabulary result record |
| `src/main/java/workshop/ExhibitValidation.java` | Step 4 | Combined structural result |
| `src/main/java/workshop/ExhibitValidator.java` | Step 4 | `ExhibitValidator.validate` |
| `src/main/java/workshop/MuseumExhibitService.java` | Steps 2, 5, 7 | Both session configurations, permission predicate, `generate`, `research`, parser |
| `src/main/java/workshop/ResearchModels.java` | Step 7 | Research contract records and status enum |
| `src/main/java/workshop/MuseumExhibitStudio.java` | Steps 1-7 | Interactive CLI, approval gate, printed sources |

After this guide the project differs from the completed one only in the `artifactId`.

## Files that already match

After step 6, these files are byte-identical to their completed counterparts. Confirm before you
continue:

```bash
cd museum-workshop-app/src/main/java/workshop
diff CuratorRuntime.java ../../../../../finished/java/museum-exhibit-studio/src/main/java/workshop/CuratorRuntime.java
diff CuratorPrompts.java ../../../../../finished/java/museum-exhibit-studio/src/main/java/workshop/CuratorPrompts.java
diff ExhibitValidator.java ../../../../../finished/java/museum-exhibit-studio/src/main/java/workshop/ExhibitValidator.java
cd -
```

Each `diff` must print nothing. A difference means an earlier step was edited by hand; take the
completed file as the correct version. The four small validation records and `ExhibitValidation`
match as well.

## 1. Add the JSON dependency

The parser reads the research response with Jackson. Add this dependency to the `<dependencies>`
section of `museum-workshop-app/pom.xml`, next to the existing SDK dependency:

```xml
    <dependency>
      <groupId>com.fasterxml.jackson.core</groupId>
      <artifactId>jackson-databind</artifactId>
      <version>2.22.1</version>
    </dependency>
```

Keep `-Acopilot.experimental.allowed=true` in the compiler plugin arguments and
`workshop.MuseumExhibitStudio` as the exec plugin main class.

Resolve the new dependency before building offline:

```bash
mvn -f museum-workshop-app/pom.xml dependency:go-offline
```

## 2. Add the research records

```bash
cp finished/java/museum-exhibit-studio/src/main/java/workshop/ResearchModels.java museum-workshop-app/src/main/java/workshop/ResearchModels.java
```

`ResearchModels.java` declares four package-private types in one file:

- `FactReviewStatus` is an enum whose labels are the exact lowercase strings `supported`,
  `contradicted`, `not found`, and `not checked`. `fromLabel` throws
  `IllegalArgumentException` for anything else, and `toString` returns the label so the CLI prints
  the contract spelling.
- `FactReview(fact, status, evidenceTitle, evidenceUrl, explanation)`.
- `ProposedAddition(fact, sourceTitle, sourceUrl, approved)` with `withApproved(boolean)`, so an
  approval creates a new record instead of mutating the parsed one.
- `ResearchSource(title, url)` and `ResearchResult(reviews, additions, consultedSources, completed,
  failureMessage)`, whose compact constructor copies every list defensively.

## 3. Replace the service

```bash
cp finished/java/museum-exhibit-studio/src/main/java/workshop/MuseumExhibitService.java museum-workshop-app/src/main/java/workshop/MuseumExhibitService.java
```

This keeps `generate`, `createSessionConfiguration` with `.setAvailableTools(List.of())` and its
reject-all permission handler, and `GENERATION_TIMEOUT` exactly as they were after step 5, together
with the research session configuration and permission predicate you added in the lesson.

**Limits.**

| Constant | Value |
|---|---|
| `GENERATION_TIMEOUT` | `Duration.ofSeconds(120)` |
| `RESEARCH_TIMEOUT` | `Duration.ofSeconds(45)` |
| `RESEARCH_FORMAT_RETRY_TIMEOUT` | `Duration.ofSeconds(15)` |
| `MAXIMUM_RESEARCH_RESPONSE_LENGTH` | `50_000` characters |

**`research(approvedFacts, model)`.** It returns a `ResearchResult` and never throws:

1. `normalizedFacts` trims, drops blanks, and runs `CuratorPrompts.buildExhibitPrompt` on the
   result, so an input that could not be generated from is rejected before Wikipedia is contacted.
2. The client starts and the research session is created.
3. The research prompt is sent with `RESEARCH_TIMEOUT`.
4. If parsing throws `IllegalArgumentException`, one bounded reformat request is sent with
   `RESEARCH_FORMAT_RETRY_TIMEOUT`. That request explicitly forbids calling tools again and forbids
   new claims, so the retry can only restate the result that already came back.
5. Any other failure becomes `incompleteResearch(facts, message)`.
6. The `finally` block disconnects the session and stops the client, collecting both failures. If
   cleanup failed, the returned result is replaced with an incomplete one that names the cleanup
   failure, so a leaked process is never reported as a clean review.

**Parser.** `parseResearchResult(response, facts)` strips a single ```` ```json ```` fence if
present, requires the payload to start with `{`, and rejects:

| Condition | Reason |
|---|---|
| A blank response, or one longer than `MAXIMUM_RESEARCH_RESPONSE_LENGTH` | Bounded input before parsing |
| A payload that is not an object, or is missing the three arrays or the `completed` boolean | Contract violation |
| A review whose `fact` is not one of the supplied facts | The researcher may not rewrite an input |
| A review count that differs from the facts, or any fact reviewed other than exactly once | One review per supplied fact |
| A status outside `FactReviewStatus` | Only documented statuses exist |
| `SUPPORTED` or `CONTRADICTED` whose evidence pair is not in `consultedSources` | Evidence claims require consulted provenance |
| An addition whose source pair is not in `consultedSources` | No invented provenance |
| More than three additions | Bounded proposals |
| `completed` false | Reported as the failure message when present |

`requiredWikipediaUrl` and `nullableWikipediaUrl` accept only values beginning with
`https://en.wikipedia.org/wiki/`. Every parsed addition is constructed with `approved` set to
`false`.

**Approval helper.** `applyApprovedAdditions(originalFacts, additions)` returns the normalized
original facts plus only the additions whose `approved()` is `true`.

## 4. Replace the entrypoint

```bash
cp finished/java/museum-exhibit-studio/src/main/java/workshop/MuseumExhibitStudio.java museum-workshop-app/src/main/java/workshop/MuseumExhibitStudio.java
```

The CLI keeps the step 6 `Scanner` flow and inserts the approval gate:

1. Print the Apollo 11 facts and ask `Use these facts? [Y/n]`, reading custom facts on `n`.
2. Ask `Run Wikipedia research? [y/N]`. Anything other than `y` skips research entirely, so the MCP
   server is never started.
3. Research runs inside its own `try (var researchClient = new CopilotCuratorClient())`, so the
   research client is closed before generation begins on a separate client.
4. `printResearch` prints each fact as `- [status] fact`, its explanation, and its source when
   present.
5. `approveAdditions` prints each proposed addition with its article title and URL, asks
   `Approve this addition? [y/N]`, and records the decision with `withApproved`. With no additions
   it prints `Wikipedia proposed no additions.`
6. When research did not complete, print
   `Wikipedia research was not completed. Generating from the original approved facts only.` and the
   failure message, then continue with the original facts.
7. `MuseumExhibitService.applyApprovedAdditions` builds the generation input, `generate` runs on the
   unchanged tool-free session, and `printValidation` prints the structural result and the grounding
   disclaimer.
8. `printSources` prints `Consulted Wikipedia sources:` after the exhibit, and nothing when there
   are none.
9. `hasCause(exception, TimeoutException.class)` selects the two-minute message; any other failure
   prints `Could not generate the exhibit: ` plus `rootMessage(exception)`, and the process exits
   with status 1.

## Tool-name discovery

The pinned `wikipedia-mcp@1.0.3` server exposes the bare names `search` and `readArticle`, which the
runtime prefixes to `wikipedia-search` and `wikipedia-readArticle`. `isAllowedWikipediaRequest`
accepts both spellings because the permission payload can carry either. If you point the
configuration at a different server version, run one discovery pass with `.setTools(List.of("*"))`,
record the names the connected server reports, restore the two-name list immediately, and update the
predicate to match. Never leave wildcard access in the finished application.

## Build and run

```bash
mvn -f museum-workshop-app/pom.xml compile
mvn -f museum-workshop-app/pom.xml compile exec:java
```

`exec:java` runs in the same JVM, so `System.in` reaches the `Scanner` prompts. The run needs an
authenticated GitHub Copilot CLI, Node.js on `PATH` so the research session can launch
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
6. Confirm `createSessionConfiguration` still calls `.setAvailableTools(List.of())`, so the session
   that writes exhibit copy has no way to reach Wikipedia.
