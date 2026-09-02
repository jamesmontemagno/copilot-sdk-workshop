import assert from "node:assert/strict";
import test from "node:test";
import type { PermissionRequest } from "@github/copilot-sdk";
import { apollo11Facts } from "../src/prompts.js";
import {
  maximumResearchSearchCalls,
  buildResearchPrompt,
  factReviewStatuses,
  incompleteResearch,
  parseResearchResult,
  selectApprovedFacts,
} from "../src/research.js";
import {
  createResearchSessionConfiguration,
  createWikipediaPermissionHandler,
} from "../src/service.js";

test("research configuration exposes only Wikipedia search and article retrieval", () => {
  const config = createResearchSessionConfiguration(" test-model ");
  assert.equal(config.clientName, "museum-exhibit-studio-research");
  assert.equal(config.model, "test-model");
  assert.deepEqual(config.availableTools, ["wikipedia-search", "wikipedia-readArticle"]);
  assert.deepEqual(config.mcpServers?.wikipedia?.tools, ["search", "readArticle"]);
  assert.ok(config.onPermissionRequest);
});

test("permission handler approves only allowlisted calls from the Wikipedia server", async () => {
  const permissionHandler = createWikipediaPermissionHandler();
  const beforeSearch = await permissionHandler({
    kind: "mcp",
    serverName: "wikipedia",
    toolName: "readArticle",
    toolTitle: "Read",
    readOnly: false,
  }, { sessionId: "test" });
  assert.equal(beforeSearch.kind, "reject");

  const allowed = await permissionHandler({
    kind: "mcp",
    serverName: "wikipedia",
    toolName: "search",
    toolTitle: "Search",
    readOnly: false,
  }, { sessionId: "test" });
  assert.equal(allowed.kind, "approve-once");

  for (const request of [
    {
      kind: "mcp",
      serverName: "wikipedia",
      toolName: "write",
      toolTitle: "Write",
      readOnly: false,
    },
    {
      kind: "mcp",
      serverName: "other",
      toolName: "search",
      toolTitle: "Search",
      readOnly: true,
    },
    { kind: "shell", commands: ["echo denied"] },
  ] as PermissionRequest[]) {
    const result = await permissionHandler(request, { sessionId: "test" });
    assert.equal(result.kind, "reject");
  }

  for (let index = 1; index < maximumResearchSearchCalls; index += 1) {
    const result = await permissionHandler({
      kind: "mcp",
      serverName: "wikipedia",
      toolName: "wikipedia-search",
      toolTitle: "Search",
      readOnly: false,
    }, { sessionId: "test" });
    assert.equal(result.kind, "approve-once");
  }
  const excessSearch = await permissionHandler({
    kind: "mcp",
    serverName: "wikipedia",
    toolName: "search",
    toolTitle: "Search",
    readOnly: false,
  }, { sessionId: "test" });
  assert.equal(excessSearch.kind, "reject");

  const article = await permissionHandler({
    kind: "mcp",
    serverName: "wikipedia",
    toolName: "readArticle",
    toolTitle: "Read",
    readOnly: false,
  }, { sessionId: "test" });
  assert.equal(article.kind, "approve-once");
  const excessArticle = await permissionHandler({
    kind: "mcp",
    serverName: "wikipedia",
    toolName: "readArticle",
    toolTitle: "Read",
    readOnly: false,
  }, { sessionId: "test" });
  assert.equal(excessArticle.kind, "reject");
  const searchAfterArticle = await permissionHandler({
    kind: "mcp",
    serverName: "wikipedia",
    toolName: "search",
    toolTitle: "Search",
    readOnly: false,
  }, { sessionId: "test" });
  assert.equal(searchAfterArticle.kind, "reject");
});

test("research prompt requires search before article retrieval and bounded work", () => {
  const { prompt } = buildResearchPrompt(apollo11Facts);
  assert.match(prompt, /Call search before readArticle/);
  assert.match(prompt, /at most 5 total search calls/);
  assert.match(prompt, /single most relevant article/);
  apollo11Facts.forEach((fact) => assert.ok(prompt.includes(fact)));
});

test("valid research keeps reviews, additions, and provenance separate", () => {
  const result = parseResearchResult(validResearchJson(), apollo11Facts);
  assert.deepEqual(result.reviews.map((review) => review.fact), [...apollo11Facts]);
  assert.ok(result.reviews.every((review) => factReviewStatuses.includes(review.status)));
  assert.equal(result.additions[0]?.approved, false);
  assert.equal(result.additions[0]?.sourceTitle, "Apollo 11");
  assert.equal(result.additions[0]?.sourceUrl, "https://en.wikipedia.org/wiki/Apollo_11");
  assert.deepEqual(selectApprovedFacts([...apollo11Facts], result.additions), [...apollo11Facts]);

  result.additions[0]!.approved = true;
  assert.deepEqual(selectApprovedFacts([...apollo11Facts], result.additions), [
    ...apollo11Facts,
    "Apollo 11 carried three astronauts.",
  ]);
});

test("malformed and empty results do not invent evidence", () => {
  assert.throws(() => parseResearchResult("", apollo11Facts), /malformed JSON/);
  assert.throws(
    () => parseResearchResult(JSON.stringify({
      reviews: [],
      additions: [{
        fact: "Invented",
        sourceTitle: "Missing",
        sourceUrl: "https://example.com/not-wikipedia",
        approved: false,
      }],
      consultedSources: [],
      completed: true,
      failureMessage: null,
    }), apollo11Facts),
    /one review for every supplied fact/,
  );
  const mismatchedEvidence = JSON.parse(validResearchJson());
  mismatchedEvidence.reviews[0].evidenceUrl = null;
  assert.throws(
    () => parseResearchResult(JSON.stringify(mismatchedEvidence), apollo11Facts),
    /both an article title and canonical URL/,
  );
  const unconsultedEvidence = JSON.parse(validResearchJson());
  unconsultedEvidence.reviews[0].evidenceTitle = "Moon";
  unconsultedEvidence.reviews[0].evidenceUrl = "https://en.wikipedia.org/wiki/Moon";
  assert.throws(
    () => parseResearchResult(JSON.stringify(unconsultedEvidence), apollo11Facts),
    /review with evidence must reference a consulted source/,
  );
  const noSource = JSON.parse(validResearchJson());
  noSource.consultedSources = [];
  noSource.additions = [];
  assert.throws(
    () => parseResearchResult(JSON.stringify(noSource), apollo11Facts),
    /exactly one consulted source/,
  );
  const overlongAddition = JSON.parse(validResearchJson());
  overlongAddition.additions[0].fact = "a".repeat(501);
  assert.throws(
    () => parseResearchResult(JSON.stringify(overlongAddition), apollo11Facts),
    /invalid proposed addition/,
  );
});

test("incomplete research marks every original fact not checked", () => {
  const result = incompleteResearch(apollo11Facts, "startup failed");
  assert.equal(result.completed, false);
  assert.equal(result.failureMessage, "startup failed");
  assert.deepEqual(result.additions, []);
  assert.ok(result.reviews.every((review) => review.status === "not checked"));
  assert.deepEqual(selectApprovedFacts([...apollo11Facts], result.additions), [...apollo11Facts]);
  assert.throws(
    () => selectApprovedFacts(
      Array.from({ length: 20 }, (_, index) => `fact ${index}`),
      [{
        fact: "approved overflow",
        sourceTitle: "Apollo 11",
        sourceUrl: "https://en.wikipedia.org/wiki/Apollo_11",
        approved: true,
      }],
    ),
    /no more than 20/,
  );
});

function validResearchJson(): string {
  return JSON.stringify({
    reviews: apollo11Facts.map((fact) => ({
      fact,
      status: "supported",
      evidenceTitle: "Apollo 11",
      evidenceUrl: "https://en.wikipedia.org/wiki/Apollo_11",
      explanation: "The article supports this fact.",
    })),
    additions: [{
      fact: "Apollo 11 carried three astronauts.",
      sourceTitle: "Apollo 11",
      sourceUrl: "https://en.wikipedia.org/wiki/Apollo_11",
      approved: false,
    }],
    consultedSources: [{
      title: "Apollo 11",
      url: "https://en.wikipedia.org/wiki/Apollo_11",
    }],
    completed: true,
    failureMessage: null,
  });
}
