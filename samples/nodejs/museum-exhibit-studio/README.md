# Museum Exhibit Studio

This completed Node.js/TypeScript sample uses the GitHub Copilot SDK as a focused,
non-software-engineering agent harness. A museum educator can accept the Apollo 11
fixture or enter another approved fact set, then generate visitor-facing exhibit
copy, optionally research it through a separately bounded Wikipedia session, explicitly
approve sourced additions, and inspect deterministic structural checks.

## Run the sample

From the repository root:

```bash
cd samples/nodejs/museum-exhibit-studio
npm ci
npm start
```

Set `COPILOT_MODEL` before running to select a model. Otherwise, the Copilot runtime
chooses its default. The sample requires an authenticated GitHub Copilot CLI.

Run the mocked tests without contacting a model:

```bash
npm test
npm run build
```

## What the sample teaches

`systemMessage` is the complete durable agent definition and uses replace mode. The
current approved facts remain in the user prompt because they are task data, not
reusable policy. The application therefore owns the curator role, writing style,
grounding guidance, and output contract.

Prompt guidance is not an authorization boundary. The sample separately applies
hard controls:

- `availableTools: []` exposes no tools to the session.
- A separate research session exposes only Wikipedia `search` and `readArticle`.
- Its deny-by-default permission handler allows at most five searches followed by
  one article read.
- Research has a 45-second timeout and accepts at most 64 KiB of strict JSON.
- Proposed additions remain separate until the educator explicitly approves them.
- Fact count and length are bounded before a request is sent.
- Generation has a two-minute timeout.
- The session is disconnected and the client is stopped on success or failure.
- Application code checks the title, sections, narrative length, questions, and
  prohibited terms.

The validator cannot prove semantic factual grounding. Generated claims still
require human review or a separate evaluator.

## Manual check

1. Run the sample with the default Apollo 11 facts.
2. Confirm the response contains one title, a 100-140-word narrative, and three
   questions.
3. Confirm the validation summary is displayed.
4. Review the prose for claims not present in the approved facts.
5. Decline Wikipedia research and confirm no tool events or permission requests appear.
6. Opt into research, reject one proposed addition, approve another, and confirm only
   the approved fact reaches exhibit generation.
7. Confirm consulted source titles and URLs appear after the exhibit rather than in it.
