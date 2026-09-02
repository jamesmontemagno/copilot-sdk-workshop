import assert from "node:assert/strict";
import test from "node:test";
import { validateExhibit } from "../src/validator.js";

test("validator accepts narrative boundaries", () => {
  for (const count of [100, 140]) {
    const result = validateExhibit(createExhibit(count, 3));
    assert.equal(result.valid, true);
    assert.equal(result.narrative.wordCount, count);
  }
});

test("validator rejects narrative outside boundaries", () => {
  for (const count of [99, 141]) {
    assert.equal(validateExhibit(createExhibit(count, 3)).narrative.withinLimit, false);
  }
});

test("validator requires exactly one title and both sections", () => {
  const valid = createExhibit(110, 3);
  assert.equal(validateExhibit(valid.replace("# A Journey\n", "")).title.present, false);
  assert.equal(validateExhibit(`${valid}\n# Another`).title.present, false);
  assert.equal(validateExhibit(valid.replace("## Narrative\n", "")).narrative.present, false);
  assert.equal(
    validateExhibit(valid.replace("## Visitor questions\n", "")).visitorQuestions.present,
    false,
  );
});

test("validator requires exactly three numbered questions ending in question marks", () => {
  assert.equal(validateExhibit(createExhibit(110, 2)).visitorQuestions.exactlyThree, false);
  assert.equal(validateExhibit(createExhibit(110, 4)).visitorQuestions.exactlyThree, false);
  assert.equal(
    validateExhibit(createExhibit(110, 3).replace("3. Reflection question?", "3. Reflection prompt."))
      .visitorQuestions.allItemsAreQuestions,
    false,
  );
});

test("validator reports every prohibited term case-insensitively", () => {
  const result = validateExhibit(
    createExhibit(105, 3).replace(
      "word1 word2 word3 word4 word5",
      "SOFTWARE codebase repository terminal GitHub Copilot",
    ),
  );
  assert.deepEqual(result.vocabulary.prohibitedTerms, [
    "software", "codebase", "repository", "terminal", "GitHub Copilot",
  ]);
  assert.equal(result.valid, false);
});

function createExhibit(narrativeWordCount: number, questionCount: number): string {
  const narrative = Array.from({ length: narrativeWordCount }, (_, index) => `word${index + 1}`).join(" ");
  const questions = Array.from({ length: questionCount }, (_, index) => `${index + 1}. Reflection question?`).join("\n");
  return `# A Journey\n## Narrative\n${narrative}\n## Visitor questions\n${questions}`;
}
