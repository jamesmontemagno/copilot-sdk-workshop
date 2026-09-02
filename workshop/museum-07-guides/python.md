# Python guide: Wikipedia MCP

Final implementation reference for museum step 7 on the Python track. It assumes
`museum-workshop-app` is the application you built through
[Run and review the exhibit](../museum-06-run-review.md) and then extended in
[Wikipedia MCP](../museum-07-wikipedia-grounding.md) with
`create_research_session_configuration` and `wikipedia_permission_handler`.

The completed counterpart of every file below is in `finished/python/museum-exhibit-studio`.

## Final layout

| File in `museum-workshop-app` | Introduced in | Responsibility |
|---|---|---|
| `requirements.txt` | Preflight | `github-copilot-sdk==1.0.11` |
| `pyproject.toml` | Preflight | Project metadata and type-checking settings |
| `.venv/` | Preflight | Isolated environment created by `python3 -m venv` |
| `curator_prompts.py` | Steps 1 and 3 | Curator policy, Apollo 11 facts, fact limits, `build_exhibit_prompt` |
| `exhibit_validator.py` | Step 4 | Structural result dataclasses and `validate_exhibit` |
| `museum_exhibit_service.py` | Steps 2, 5, 7 | Both session configurations, permission handler, `MuseumExhibitService`, research contract and parser |
| `main.py` | Steps 1-7 | Interactive CLI, approval gate, printed sources |

`curator_runtime.py` from the starter was removed in step 2 when `museum_exhibit_service.py` took
over the SDK boundary. The completed project has no such file either, and after this guide the two
projects differ only in `pyproject.toml` metadata.

## Files that already match

After step 6, two files are byte-identical to their completed counterparts. Confirm before you
continue:

```bash
diff museum-workshop-app/curator_prompts.py finished/python/museum-exhibit-studio/curator_prompts.py
diff museum-workshop-app/exhibit_validator.py finished/python/museum-exhibit-studio/exhibit_validator.py
```

Each command must print nothing. A difference means an earlier step was edited by hand; take the
completed file as the correct version.

## 1. Replace the service

```bash
cp finished/python/museum-exhibit-studio/museum_exhibit_service.py museum-workshop-app/museum_exhibit_service.py
```

This keeps `generate`, `create_session_configuration` with `"available_tools": []`, and
`GENERATION_TIMEOUT_SECONDS = 120.0` exactly as they were after step 5, and adds the research half
in the same module.

**Imports.** The research code needs `json`, `dataclass`, `urllib.parse.unquote`,
`urllib.parse.urlparse`, `copilot.rpc.PermissionDecisionApproveOnce`,
`copilot.rpc.PermissionDecisionReject`, and the session event payloads
`copilot.session_events.ToolExecutionStartData` and
`copilot.session_events.ToolExecutionCompleteData`.

**Limits.**

| Constant | Value |
|---|---|
| `GENERATION_TIMEOUT_SECONDS` | `120.0` |
| `RESEARCH_TIMEOUT_SECONDS` | `45.0` |
| `MAXIMUM_RESEARCH_RESPONSE_LENGTH` | `65_536` |
| `RESEARCH_STATUSES` | The four documented statuses, as a `frozenset` |

**Types.** `FactReview`, `ProposedAddition`, `Source`, and `ResearchResult` are frozen dataclasses
that mirror the contract in the lesson. `ProposedAddition.approved` defaults to `False`.

**Observed tool calls.** This track does not rely on the prompt to describe what happened. The
service subscribes to session events with `session.on(...)` and records every `wikipedia` tool call
through `_record_wikipedia_tool_call`, keeping the tool name, arguments, success flag, and result.
`_validate_research_tool_calls` then raises unless a successful `search` and a successful
`readArticle` both occurred, in that order, and it returns the normalized article references that
were actually retrieved.

**`MuseumExhibitService.research`.** The sequence is:

1. Normalize the facts and run `build_exhibit_prompt` on them, so an input that could not be
   generated from is rejected before Wikipedia is contacted.
2. Start the client and create the session with `on_permission_request=wikipedia_permission_handler`
   plus `**create_research_session_configuration(model)`.
3. Subscribe the tool-call recorder, then send `_build_research_prompt(facts)` with
   `timeout=RESEARCH_TIMEOUT_SECONDS`.
4. Reject a blank response and one longer than `MAXIMUM_RESEARCH_RESPONSE_LENGTH`.
5. Validate the observed tool calls, then parse with `_parse_research_result`.
6. Convert any exception into `_incomplete_research(facts, message)`; `research` never raises.
7. In `finally`, unsubscribe and disconnect inside a `try`, with `await self._client.stop()` in the
   inner `finally`, so a failed disconnect cannot skip the stop.

**Parser.** `_parse_research_result(content, facts, retrieved_references)` raises `ValueError`
rather than repairing anything. It rejects:

| Condition | Reason |
|---|---|
| Malformed JSON, or a payload that is not an object | Contract violation |
| `completed` that is not `True`, or a non-null `failureMessage` | A completed result cannot report failure |
| Missing `reviews`, `additions`, or `consultedSources` arrays | Contract violation |
| Reviews that are not exactly the supplied facts, in order | One review per supplied fact |
| A status outside `RESEARCH_STATUSES` | Only documented statuses exist |
| An evidence title without a URL, or a URL without a title | Provenance is a pair |
| `supported` or `contradicted` without evidence | Evidence claims require provenance |
| More than three additions | Bounded proposals |
| An addition longer than `MAXIMUM_FACT_LENGTH`, or with `approved` not `False` | Approval is the educator's decision |
| Evidence or an addition whose source is not in `consultedSources` | No invented provenance |
| A consulted source that does not match an article actually retrieved | The recorded tool calls are the ground truth |

`_optional_url` accepts only `https`, host `en.wikipedia.org`, a `/wiki/` path that is not empty,
and no params, query, or fragment.

## 2. Replace the entrypoint

```bash
cp finished/python/museum-exhibit-studio/main.py museum-workshop-app/main.py
```

The CLI keeps the step 6 flow and inserts the approval gate:

1. Print the Apollo 11 facts and ask `Use these facts? [Y/n]`, reading custom facts on `n`.
2. Ask `Run Wikipedia research? [y/N]`. Anything other than `y` skips research entirely, so the MCP
   server is never started.
3. Run `MuseumExhibitService(CopilotClient()).research(facts, os.getenv("COPILOT_MODEL"))` on its
   own client instance, separate from the one that generates.
4. `review_research` prints each fact with `[status]`, its explanation, and its source when present,
   then asks `Approve this addition? [y/N]` for each proposed addition and returns only the approved
   texts.
5. `remaining_fact_slots` is `MAXIMUM_FACT_COUNT - len(facts)`. When it reaches zero, the CLI states
   that the 20-fact limit is reached and stops offering approvals.
6. When research did not complete, print
   `Wikipedia research was not completed. Generating from the original approved facts only.` and
   continue with the original facts.
7. Generate with the unchanged tool-free service, print the exhibit, print the structural result and
   the grounding disclaimer with `print_validation`, then print `Consulted Wikipedia sources:` with
   `print_sources` after the exhibit.
8. Return `1` after a `TimeoutError` or any other failure, with the two-minute message for the
   timeout case.

## Build and run

```bash
museum-workshop-app/.venv/bin/python -m py_compile museum-workshop-app/*.py
museum-workshop-app/.venv/bin/python museum-workshop-app/main.py
```

The compile step checks the source without contacting a model. The run needs an authenticated
GitHub Copilot CLI, Node.js on `PATH` so the research session can launch
`npx -y wikipedia-mcp@1.0.3`, and network access to Wikipedia. Set `COPILOT_MODEL` to choose a
model. Declining research does not start the MCP server, so a machine without Node.js can still run
everything through step 6.

## Verify

1. Answer `N` to the research question. The output matches step 6 and no MCP server starts.
2. Answer `y`. Every supplied fact appears with one of the four statuses and an explanation.
3. Reject an addition and confirm its wording appears nowhere in the exhibit.
4. Approve an addition and confirm its article title and URL still appear under
   `Consulted Wikipedia sources:` after the exhibit.
5. Disconnect from the network and answer `y`. The CLI reports that research was not completed,
   every fact is `not checked`, and generation proceeds from the original facts.
6. Confirm `create_session_configuration` still sets `"available_tools": []`, so the session that
   writes exhibit copy has no way to reach Wikipedia.
