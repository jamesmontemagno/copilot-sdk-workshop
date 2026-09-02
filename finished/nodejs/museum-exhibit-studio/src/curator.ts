import type {
  CopilotSession,
  MCPServerConfig,
  PermissionHandler,
} from "@github/copilot-sdk";
import { stdin as input, stdout as output } from "node:process";
import { createInterface, type Interface } from "node:readline/promises";
import { resolve } from "node:path";

export const apollo11Facts = [
  "Apollo 11 launched July 16, 1969.",
  "It landed on the Moon July 20, 1969.",
  "Neil Armstrong and Buzz Aldrin walked on the Moon.",
  "Michael Collins remained in lunar orbit.",
  "The mission returned to Earth July 24, 1969.",
] as const;

export const greatBarrierReefFacts = [
  "The Great Barrier Reef lies off the coast of Queensland, Australia.",
  "It stretches for about 2,300 kilometres.",
  "It is made up of more than 2,900 individual reefs.",
  "It was added to the UNESCO World Heritage List in 1981.",
  "Rising sea temperatures have caused repeated coral bleaching events.",
] as const;

export const terracottaArmyFacts = [
  "The Terracotta Army was buried near the tomb of China's first emperor, Qin Shi Huang.",
  "Farmers digging a well discovered the site in 1974.",
  "The pits contain thousands of life-sized clay soldiers.",
  "Each figure was assembled from moulded parts and finished by hand.",
  "The site sits near the modern city of Xi'an in Shaanxi Province.",
] as const;

export const factSets = [
  { key: "apollo11", label: "Apollo 11", facts: apollo11Facts },
  { key: "reef", label: "Great Barrier Reef", facts: greatBarrierReefFacts },
  { key: "terracotta", label: "Terracotta Army", facts: terracottaArmyFacts },
] as const;

export const maximumFactCount = 20;
export const maximumFactLength = 500;

export function boundFacts(facts: Iterable<string>): string[] {
  const bounded = [...facts].map((fact) => fact.trim()).filter(Boolean);
  if (bounded.length === 0) throw new Error("Provide at least one approved fact.");
  if (bounded.length > maximumFactCount) {
    throw new Error("Provide no more than 20 approved facts.");
  }
  if (bounded.some((fact) => fact.length > maximumFactLength)) {
    throw new Error("Each approved fact must be 500 characters or fewer.");
  }
  return bounded;
}

export const generationTimeoutMs = 120_000;
export const researchTimeoutMs = 90_000;

export async function streamExhibit(
  session: CopilotSession,
  prompt: string,
  timeout = generationTimeoutMs,
): Promise<string> {
  return await new Promise<string>((resolvePromise, rejectPromise) => {
    let content = "";
    let receivedDelta = false;
    let settled = false;
    let unsubscribe: () => void = () => {};
    let timer: ReturnType<typeof setTimeout> | undefined;

    const finish = (error?: unknown) => {
      if (settled) return;
      settled = true;
      if (timer) clearTimeout(timer);
      unsubscribe();
      if (error) {
        rejectPromise(error instanceof Error ? error : new Error(String(error)));
      } else {
        resolvePromise(content);
      }
    };

    timer = setTimeout(
      () => finish(new Error(`stream timeout after ${timeout}ms`)),
      timeout,
    );

    unsubscribe = session.on((event) => {
      if (event.type === "assistant.message_delta" && event.data.deltaContent) {
        receivedDelta = true;
        content += event.data.deltaContent;
        process.stdout.write(event.data.deltaContent);
      } else if (event.type === "assistant.message" && !receivedDelta) {
        content += event.data.content;
        process.stdout.write(event.data.content);
      } else if (event.type === "tool.execution_start") {
        console.log(`\n[tool:start] ${event.data.toolName}`);
      } else if (event.type === "tool.execution_complete") {
        console.log(`[tool:done] success=${event.data.success}`);
      } else if (event.type === "session.error") {
        finish(new Error(event.data.message));
      } else if (event.type === "session.idle") {
        console.log();
        finish();
      }
    });

    void session.send({ prompt }).catch(finish);
  });
}

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
const wordPattern = /\b[\p{L}\p{N}]+(?:['\u2019-][\p{L}\p{N}]+)*\b/gu;
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

export function formatValidation(validation: ExhibitValidation): string {
  return [
    validation.valid ? "Structural checks passed." : "Structural checks found issues:",
    `- One level-one title: ${validation.title.present}`,
    `- Narrative section: ${validation.narrative.present}`,
    `- Narrative length: ${validation.narrative.wordCount} words (within 100-140: ${validation.narrative.withinLimit})`,
    `- Visitor questions section: ${validation.visitorQuestions.present}`,
    `- Numbered questions: ${validation.visitorQuestions.questionCount} (exactly three: ${validation.visitorQuestions.exactlyThree})`,
    `- Every item is a question: ${validation.visitorQuestions.allItemsAreQuestions}`,
    `- Prohibited vocabulary: ${validation.vocabulary.prohibitedTerms.length === 0 ? "none" : validation.vocabulary.prohibitedTerms.join(", ")}`,
    ...validation.errors.map((error) => `  - ${error}`),
    "",
    "Structural checks do not prove factual grounding. Unsupported claims require human review or a separate evaluator.",
  ].join("\n");
}

function findHeading(lines: readonly string[], heading: string): number {
  const normalized = heading.toLocaleLowerCase();
  return lines.findIndex((line) => line.trim().toLocaleLowerCase() === normalized);
}

export const wikipediaTools = ["wikipedia-search", "wikipedia-readArticle"] as const;

// Return this config as the value for SessionConfig.mcpServers.wikipedia.
export function wikipediaServer(): MCPServerConfig {
  return {
    command: "npx",
    args: ["-y", "wikipedia-mcp@1.0.3"],
    workingDirectory: process.cwd(),
    tools: ["search", "readArticle"],
  };
}

export function wikipediaPermissionHandler(): PermissionHandler {
  const allowedTools = new Set([
    "search",
    "readArticle",
    "wikipedia-search",
    "wikipedia-readArticle",
  ]);
  return (request) => {
    if (
      request.kind === "mcp" &&
      request.serverName === "wikipedia" &&
      allowedTools.has(request.toolName)
    ) {
      return { kind: "approve-once" };
    }
    return {
      kind: "reject",
      feedback: "This session allows only the scoped Wikipedia search and article tools.",
    };
  };
}

export type WikipediaSource = {
  readonly title: string;
  readonly url: string;
};

export type ExtractedSources = {
  readonly body: string;
  readonly sources: readonly WikipediaSource[];
};

export function extractSources(content: string): ExtractedSources {
  try {
    const lines = content.replace(/\r\n?/g, "\n").split("\n");
    let sourcesIndex = -1;
    for (let index = lines.length - 1; index >= 0; index -= 1) {
      if (lines[index]?.trim().toLocaleLowerCase() === "## sources") {
        sourcesIndex = index;
        break;
      }
    }
    if (sourcesIndex < 0) return { body: content.trimEnd(), sources: [] };

    const sources = lines.slice(sourcesIndex + 1).flatMap((line) => {
      const match = line.match(/^\s*-\s*(.+?):\s*(https:\/\/\S+)\s*$/u);
      if (!match?.[1] || !match[2]) return [];
      return [{ title: match[1].trim(), url: match[2].trim() }];
    });

    return {
      body: lines.slice(0, sourcesIndex).join("\n").trimEnd(),
      sources,
    };
  } catch {
    return { body: content, sources: [] };
  }
}

export const exhibitFileName = "exhibit.html";

export function exhibitWritePermission(workingDirectory: string): PermissionHandler {
  const root = resolve(workingDirectory);
  const exhibitPath = resolve(root, exhibitFileName);
  return (request) => {
    if (
      request.kind === "write" &&
      typeof request.fileName === "string" &&
      resolve(root, request.fileName) === exhibitPath
    ) {
      return { kind: "approve-once" };
    }
    return {
      kind: "reject",
      feedback: "This session allows writing only exhibit.html in the application working directory.",
    };
  };
}

let terminal: Interface | undefined;

function getTerminal(): Interface {
  terminal ??= createInterface({ input, output });
  return terminal;
}

export async function askYesNo(question: string, defaultYes: boolean): Promise<boolean> {
  const answer = (await getTerminal().question(
    `${question}${defaultYes ? " [Y/n]: " : " [y/N]: "}`,
  )).trim().toLocaleLowerCase();
  if (!answer) return defaultYes;
  return answer === "y" || answer === "yes";
}

export async function askLine(question: string): Promise<string> {
  return (await getTerminal().question(question)).trim();
}

export async function readFacts(): Promise<string[]> {
  console.log("Enter one approved fact per line. Submit a blank line when finished:");
  const facts: string[] = [];
  while (true) {
    const fact = (await getTerminal().question("")).trim();
    if (!fact) return facts;
    facts.push(fact);
  }
}

export function closeTerminal(): void {
  terminal?.close();
  terminal = undefined;
}
