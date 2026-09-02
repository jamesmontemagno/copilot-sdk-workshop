export class TitleValidation {
  constructor(readonly titleCount: number) {}
  get present(): boolean { return this.titleCount === 1; }
  get valid(): boolean { return this.present; }
}

export class NarrativeValidation {
  constructor(readonly present: boolean, readonly wordCount: number) {}
  get withinLimit(): boolean { return this.wordCount >= 100 && this.wordCount <= 140; }
  get valid(): boolean { return this.present && this.withinLimit; }
}

export class VisitorQuestionsValidation {
  constructor(
    readonly present: boolean,
    readonly questionCount: number,
    readonly allItemsAreQuestions: boolean,
  ) {}
  get exactlyThree(): boolean { return this.questionCount === 3; }
  get valid(): boolean { return this.present && this.exactlyThree && this.allItemsAreQuestions; }
}

export class VocabularyValidation {
  readonly prohibitedTerms: readonly string[];
  constructor(prohibitedTerms: readonly string[]) {
    this.prohibitedTerms = Object.freeze([...prohibitedTerms]);
  }
  get valid(): boolean { return this.prohibitedTerms.length === 0; }
}

export class ExhibitValidation {
  readonly errors: readonly string[];
  constructor(
    readonly title: TitleValidation,
    readonly narrative: NarrativeValidation,
    readonly visitorQuestions: VisitorQuestionsValidation,
    readonly vocabulary: VocabularyValidation,
    errors: readonly string[],
  ) {
    this.errors = Object.freeze([...errors]);
  }
  get valid(): boolean { return this.errors.length === 0; }
}

const prohibitedVocabulary = ["software", "codebase", "repository", "terminal", "GitHub Copilot"];
const titlePattern = /^# [^#].*$/;
const wordPattern = /\b[\p{L}\p{N}]+(?:['’-][\p{L}\p{N}]+)*\b/gu;
const questionPattern = /^\s*\d+\.\s+(.+?)\s*$/;

export function validateExhibit(content: string): ExhibitValidation {
  const lines = content.replace(/\r\n?/g, "\n").split("\n");
  const titleCount = lines.filter((line) => titlePattern.test(line)).length;
  const narrativeIndex = findHeading(lines, "## Narrative");
  const questionsIndex = findHeading(lines, "## Visitor questions");
  const narrative = narrativeIndex >= 0 && questionsIndex > narrativeIndex
    ? lines.slice(narrativeIndex + 1, questionsIndex).join(" ")
    : "";
  const narrativeWordCount = [...narrative.matchAll(wordPattern)].length;
  const questions = questionsIndex >= 0
    ? lines.slice(questionsIndex + 1)
      .map((line) => line.match(questionPattern)?.[1]?.trim())
      .filter((question): question is string => question !== undefined)
    : [];
  const title = new TitleValidation(titleCount);
  const narrativeValidation = new NarrativeValidation(
    narrativeIndex >= 0,
    narrativeWordCount,
  );
  const visitorQuestions = new VisitorQuestionsValidation(
    questionsIndex >= 0,
    questions.length,
    questions.length > 0 && questions.every((question) => question.endsWith("?")),
  );
  const vocabulary = new VocabularyValidation(prohibitedVocabulary.filter((term) =>
    content.toLocaleLowerCase().includes(term.toLocaleLowerCase())));
  const errors: string[] = [];

  if (!title.valid) errors.push("The exhibit must contain exactly one level-one title.");
  if (!narrativeValidation.present) errors.push("The exhibit must contain a Narrative section.");
  if (!narrativeValidation.withinLimit) errors.push(`The narrative must contain 100-140 words; found ${narrativeWordCount}.`);
  if (!visitorQuestions.present) errors.push("The exhibit must contain a Visitor questions section.");
  if (!visitorQuestions.exactlyThree) errors.push(`The exhibit must contain exactly three numbered questions; found ${questions.length}.`);
  if (!visitorQuestions.allItemsAreQuestions) errors.push("Every numbered visitor item must end with a question mark.");
  if (!vocabulary.valid) {
    errors.push(`The exhibit contains prohibited vocabulary: ${vocabulary.prohibitedTerms.join(", ")}.`);
  }

  return new ExhibitValidation(title, narrativeValidation, visitorQuestions, vocabulary, errors);
}

function findHeading(lines: string[], heading: string): number {
  const normalized = heading.toLocaleLowerCase();
  return lines.findIndex((line) => line.trim().toLocaleLowerCase() === normalized);
}
