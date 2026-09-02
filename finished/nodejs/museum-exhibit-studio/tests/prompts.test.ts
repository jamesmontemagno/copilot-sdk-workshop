import assert from "node:assert/strict";
import test from "node:test";
import {
  apollo11Facts,
  buildExhibitPrompt,
  maximumFactCount,
  maximumFactLength,
  systemMessage,
} from "../src/prompts.js";

test("prompt contains approved facts and exact requested structure", () => {
  const prompt = buildExhibitPrompt(apollo11Facts);
  apollo11Facts.forEach((fact) => assert.match(prompt, new RegExp(escapeRegex(fact))));
  assert.match(prompt, /# <an engaging exhibit title>/);
  assert.match(prompt, /## Narrative/);
  assert.match(prompt, /## Visitor questions/);
  assert.doesNotMatch(systemMessage, new RegExp(escapeRegex(apollo11Facts[0])));
});

test("prompt rejects empty and bounded fact violations", () => {
  assert.throws(() => buildExhibitPrompt([]), /at least one approved fact/);
  assert.throws(
    () => buildExhibitPrompt(Array(maximumFactCount + 1).fill("Approved fact.")),
    /no more than 20/,
  );
  assert.throws(() => buildExhibitPrompt(["a".repeat(maximumFactLength + 1)]), /500 characters/);
});

test("prompt accepts fact bounds and trims blank facts", () => {
  const facts = Array(maximumFactCount).fill("a".repeat(maximumFactLength));
  assert.doesNotThrow(() => buildExhibitPrompt(facts));
  assert.match(buildExhibitPrompt([" ", " approved "]), /- approved/);
});

function escapeRegex(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}
