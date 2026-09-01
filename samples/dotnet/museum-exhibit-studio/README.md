# Museum Exhibit Studio

This completed .NET sample uses the GitHub Copilot SDK as a focused, non-software-engineering
agent harness. A museum educator can accept the Apollo 11 fixture or enter another approved fact
set, optionally review Wikipedia research and explicitly approve sourced additions, then generate
visitor-facing exhibit copy and inspect deterministic structural checks.

## Run the sample

From the repository root:

```bash
dotnet run --project samples/dotnet/museum-exhibit-studio
```

Set `COPILOT_MODEL` before running to select a model. Otherwise, the Copilot runtime chooses its
default. The sample requires an authenticated GitHub Copilot CLI.

Run the mocked tests without contacting a model:

```bash
dotnet test samples/dotnet/museum-exhibit-studio/tests/museum-exhibit-studio.Tests.csproj
```

## What the sample teaches

`CuratorPrompts.SystemMessage` is the complete durable agent definition. The current approved
facts remain in the user prompt because they are task data, not reusable policy. The application
therefore owns the curator role, writing style, grounding guidance, and output contract.

Prompt guidance is not an authorization boundary. The sample separately applies hard controls:

- `AvailableTools = []` exposes no tools to the session.
- A separate research session exposes only Wikipedia `search` and `readArticle`.
- A deny-by-default permission handler rejects every other external request.
- Fact count and length are bounded before a request is sent.
- Generation has a two-minute timeout.
- Research has a 45-second timeout, a 32,000-character response limit, and at most three accepted
  proposed additions.
- The session is disposed and the client is stopped on success or failure.
- Application code checks the title, sections, narrative length, questions, and prohibited terms.

The validator cannot prove semantic factual grounding. Generated claims still require human review
or a separate evaluator.

## Manual check

1. Run the sample with the default Apollo 11 facts.
2. Confirm the response contains one title, a 100-140-word narrative, and three questions.
3. Confirm the validation summary is displayed.
4. Review the prose for claims not present in the approved facts.
5. Opt into Wikipedia research and confirm each original fact has a visible status.
6. Reject one proposed addition and approve another.
7. Confirm only the approved addition can enter the tool-free generation prompt.
8. Confirm consulted source titles and URLs appear after, not inside, the exhibit.

Automated tests use a deterministic mock MCP process and do not contact Wikipedia or a model.
