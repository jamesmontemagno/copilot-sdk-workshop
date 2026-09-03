import { defineTool, type CopilotSession } from "@github/copilot-sdk";
import { z } from "zod";
import { accessibilityRules } from "./accessibility-rule-catalog.js";

const noMatch = {
  criterion: "No exact match",
  title: "Criterion not found",
  whenItApplies: "The issue is not represented in the workshop catalog.",
  recommendation: "Verify the evidence and consult the complete WCAG reference.",
  keywords: [],
};

export const accessibilityRuleLookup = defineTool("accessibility_rule_lookup", {
  description: "Looks up read-only WCAG guidance maintained by this application.",
  parameters: z.object({
    query: z.string().describe("The accessibility issue or WCAG criterion to look up."),
  }),
  skipPermission: true,
  handler: async ({ query }) => {
    const normalized = query.trim().toLowerCase();
    return accessibilityRules.find((rule) =>
      normalized.includes(rule.criterion.toLowerCase()) ||
      normalized.includes(rule.title.toLowerCase()) ||
      rule.keywords.some((keyword) => normalized.includes(keyword)),
    ) ?? noMatch;
  },
});

export async function streamResponse(session: CopilotSession, prompt: string): Promise<void> {
  await new Promise<void>((resolve, reject) => {
    let receivedDelta = false;
    let settled = false;
    let unsubscribe = () => {};
    const finish = (callback: () => void) => {
      if (settled) return;
      settled = true;
      unsubscribe();
      callback();
    };
    unsubscribe = session.on((event) => {
      if (event.type === "assistant.message_delta" && event.data.deltaContent) {
        receivedDelta = true;
        process.stdout.write(event.data.deltaContent);
      } else if (event.type === "assistant.message" && !receivedDelta) {
        process.stdout.write(event.data.content);
      } else if (event.type === "session.error") {
        finish(() => reject(new Error(event.data.message)));
      } else if (event.type === "session.idle") {
        finish(() => {
          console.log();
          resolve();
        });
      }
    });
    void session.send({ prompt }).catch((error: unknown) => finish(() => reject(error)));
  });
}
