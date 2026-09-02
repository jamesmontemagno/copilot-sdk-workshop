import {
  CopilotClient,
  type SessionConfig,
} from "@github/copilot-sdk";

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

export function createCopilotCuratorClient(): CuratorClient {
  return new CopilotClient();
}
