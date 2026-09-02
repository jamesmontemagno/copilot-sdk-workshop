import {
  CopilotClient,
  type PermissionHandler,
  type SessionConfig,
} from "@github/copilot-sdk";
import { buildExhibitPrompt, systemMessage } from "./prompts.js";
import {
  buildResearchPrompt,
  incompleteResearch,
  maximumResearchArticleReads,
  maximumResearchSearchCalls,
  parseResearchResult,
  researchSystemMessage,
  researchTimeoutMs,
  type ResearchResult,
} from "./research.js";
import { validateExhibit, type ExhibitValidation } from "./validator.js";

export const generationTimeoutMs = 120_000;

export interface CuratorSession {
  sendAndWait(prompt: string, timeout?: number): Promise<
    { data: { content: string } } | undefined
  >;
  disconnect(): Promise<void>;
}

export interface CuratorClient {
  start(): Promise<void>;
  createSession(configuration: SessionConfig): Promise<CuratorSession>;
  stop(): Promise<unknown>;
}

export interface GeneratedExhibit {
  content: string;
  validation: ExhibitValidation;
}

export function createSessionConfiguration(model?: string): SessionConfig {
  return {
    clientName: "museum-exhibit-studio",
    model: model?.trim() || undefined,
    availableTools: [],
    streaming: false,
    systemMessage: {
      mode: "replace",
      content: systemMessage,
    },
  };
}

export function createWikipediaPermissionHandler(): PermissionHandler {
  let searchCalls = 0;
  let articleReads = 0;

  return (request) => {
    if (request.kind === "mcp" && request.serverName === "wikipedia") {
      if (["search", "wikipedia-search"].includes(request.toolName) &&
          articleReads === 0 && searchCalls < maximumResearchSearchCalls) {
        searchCalls += 1;
        return { kind: "approve-once" };
      }
      if (["readArticle", "wikipedia-readArticle"].includes(request.toolName) &&
          searchCalls > 0 && articleReads < maximumResearchArticleReads) {
        articleReads += 1;
        return { kind: "approve-once" };
      }
    }
    return {
      kind: "reject",
      feedback:
        "This session permits at most 5 Wikipedia searches followed by one article retrieval.",
    };
  };
}

export function createResearchSessionConfiguration(model?: string): SessionConfig {
  return {
    clientName: "museum-exhibit-studio-research",
    model: model?.trim() || undefined,
    streaming: false,
    systemMessage: {
      mode: "replace",
      content: researchSystemMessage,
    },
    availableTools: ["wikipedia-search", "wikipedia-readArticle"],
    mcpServers: {
      wikipedia: {
        command: "npx",
        args: ["-y", "wikipedia-mcp@1.0.3"],
        workingDirectory: process.cwd(),
        tools: ["search", "readArticle"],
      },
    },
    onPermissionRequest: createWikipediaPermissionHandler(),
  };
}

export class MuseumExhibitService {
  constructor(private readonly client: CuratorClient) {}

  async research(approvedFacts: Iterable<string>, model?: string): Promise<ResearchResult> {
    const { facts, prompt } = buildResearchPrompt(approvedFacts);
    let session: CuratorSession | undefined;

    try {
      await this.client.start();
      session = await this.client.createSession(createResearchSessionConfiguration(model));
      const response = await session.sendAndWait(prompt, researchTimeoutMs);
      const content = response?.data.content;
      if (!content?.trim()) throw new Error("The researcher returned no result.");
      return parseResearchResult(content, facts);
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      return incompleteResearch(facts, message);
    } finally {
      try {
        await session?.disconnect();
      } finally {
        await this.client.stop();
      }
    }
  }

  async generate(approvedFacts: Iterable<string>, model?: string): Promise<GeneratedExhibit> {
    const prompt = buildExhibitPrompt(approvedFacts);
    let session: CuratorSession | undefined;

    try {
      await this.client.start();
      session = await this.client.createSession(createSessionConfiguration(model));
      const response = await session.sendAndWait(prompt, generationTimeoutMs);
      const content = response?.data.content;
      if (!content?.trim()) throw new Error("The curator returned no exhibit content.");
      return { content, validation: validateExhibit(content) };
    } finally {
      try {
        await session?.disconnect();
      } finally {
        await this.client.stop();
      }
    }
  }
}

export function createCopilotCuratorClient(): CuratorClient {
  return new CopilotClient();
}
