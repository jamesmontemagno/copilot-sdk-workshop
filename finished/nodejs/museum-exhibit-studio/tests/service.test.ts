import assert from "node:assert/strict";
import test from "node:test";
import type { SessionConfig } from "@github/copilot-sdk";
import { apollo11Facts, systemMessage } from "../src/prompts.js";
import { researchTimeoutMs } from "../src/research.js";
import {
  createSessionConfiguration,
  generationTimeoutMs,
  MuseumExhibitService,
  type CuratorClient,
  type CuratorSession,
} from "../src/service.js";

test("session config owns complete prompt and exposes no tools", () => {
  const config = createSessionConfiguration(" test-model ");
  assert.equal(config.clientName, "museum-exhibit-studio");
  assert.equal(config.model, "test-model");
  assert.deepEqual(config.availableTools, []);
  assert.equal(config.streaming, false);
  assert.deepEqual(config.systemMessage, { mode: "replace", content: systemMessage });
});

test("generation returns validated content with separate user prompt and cleans up", async () => {
  const harness = createHarness(validExhibit());
  const result = await new MuseumExhibitService(harness.client).generate(apollo11Facts);
  assert.equal(result.validation.valid, true);
  assert.equal(result.validation.narrative.valid, true);
  assert.equal(harness.started, true);
  assert.equal(harness.stopped, true);
  assert.equal(harness.disconnected, true);
  assert.equal(harness.timeout, generationTimeoutMs);
  apollo11Facts.forEach((fact) => assert.match(harness.prompt, new RegExp(escapeRegex(fact))));
  assert.equal(harness.prompt.includes(systemMessage), false);
});

test("generation rejects empty output and cleans up", async () => {
  const harness = createHarness(" ");
  await assert.rejects(
    new MuseumExhibitService(harness.client).generate(apollo11Facts),
    /no exhibit content/,
  );
  assert.equal(harness.disconnected, true);
  assert.equal(harness.stopped, true);
});

test("generation failure disconnects the session and stops the client", async () => {
  const harness = createHarness(undefined, new Error("Timed out."));
  await assert.rejects(new MuseumExhibitService(harness.client).generate(apollo11Facts), /Timed out/);
  assert.equal(harness.disconnected, true);
  assert.equal(harness.stopped, true);
});

test("client is stopped when session creation fails", async () => {
  let stopped = false;
  const client: CuratorClient = {
    start: async () => {},
    createSession: async () => { throw new Error("create failed"); },
    stop: async () => { stopped = true; },
  };
  await assert.rejects(new MuseumExhibitService(client).generate(apollo11Facts), /create failed/);
  assert.equal(stopped, true);
});

test("research returns validated data with a shorter timeout and cleans up", async () => {
  const harness = createHarness(validResearch());
  const result = await new MuseumExhibitService(harness.client).research(apollo11Facts);
  assert.equal(result.completed, true);
  assert.equal(result.reviews.length, apollo11Facts.length);
  assert.equal(harness.timeout, researchTimeoutMs);
  assert.equal(harness.disconnected, true);
  assert.equal(harness.stopped, true);
});

test("research startup and malformed output failures return incomplete reviews", async () => {
  const startup = createHarness(undefined, new Error("startup failed"), true);
  const startupResult = await new MuseumExhibitService(startup.client).research(apollo11Facts);
  assert.equal(startupResult.completed, false);
  assert.match(startupResult.failureMessage ?? "", /startup failed/);
  assert.equal(startup.stopped, true);

  const malformed = createHarness("{bad json");
  const malformedResult = await new MuseumExhibitService(malformed.client).research(apollo11Facts);
  assert.equal(malformedResult.completed, false);
  assert.ok(malformedResult.reviews.every((review) => review.status === "not checked"));
  assert.equal(malformed.disconnected, true);
  assert.equal(malformed.stopped, true);

  const timeout = createHarness(undefined, new Error("Timed out."));
  const timeoutResult = await new MuseumExhibitService(timeout.client).research(apollo11Facts);
  assert.equal(timeoutResult.completed, false);
  assert.match(timeoutResult.failureMessage ?? "", /Timed out/);
  assert.equal(timeout.disconnected, true);
  assert.equal(timeout.stopped, true);
});

function createHarness(content?: string, failure?: Error, failStart = false) {
  const state = {
    started: false,
    stopped: false,
    disconnected: false,
    prompt: "",
    timeout: 0,
  };
  const session: CuratorSession = {
    sendAndWait: async (prompt, timeout) => {
      state.prompt = prompt;
      state.timeout = timeout ?? 0;
      if (failure) throw failure;
      return content === undefined ? undefined : { data: { content } };
    },
    disconnect: async () => { state.disconnected = true; },
  };
  const client: CuratorClient = {
    start: async () => {
      state.started = true;
      if (failStart && failure) throw failure;
    },
    createSession: async (_config: SessionConfig) => session,
    stop: async () => { state.stopped = true; },
  };
  return Object.assign(state, { client });
}

function validResearch(): string {
  return JSON.stringify({
    reviews: apollo11Facts.map((fact) => ({
      fact,
      status: "supported",
      evidenceTitle: "Apollo 11",
      evidenceUrl: "https://en.wikipedia.org/wiki/Apollo_11",
      explanation: "Supported by the article.",
    })),
    additions: [],
    consultedSources: [{
      title: "Apollo 11",
      url: "https://en.wikipedia.org/wiki/Apollo_11",
    }],
    completed: true,
    failureMessage: null,
  });
}

function validExhibit(): string {
  const narrative = Array.from({ length: 110 }, (_, index) => `word${index + 1}`).join(" ");
  return `# A Journey\n## Narrative\n${narrative}\n## Visitor questions\n1. What do you notice?\n2. What would you ask?\n3. What will you remember?`;
}

function escapeRegex(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}
