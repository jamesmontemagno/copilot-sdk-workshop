import { CopilotClient } from "@github/copilot-sdk";
import { createInterface } from "node:readline/promises";
import { stdin as input, stdout as output } from "node:process";
import { accessibilityRuleLookup, streamResponse } from "./local-tool.js";

async function readQuestion(): Promise<string> {
  const argument = process.argv.slice(2).join(" ").trim();
  if (argument) return argument;

  const prompt = createInterface({ input, output });
  try {
    return (await prompt.question("Accessibility question: ")).trim();
  } finally {
    prompt.close();
  }
}

const question = await readQuestion();
if (!question) {
  console.error("Enter an accessibility question to continue.");
  process.exitCode = 1;
} else {
  const client = new CopilotClient();
  await client.start();
  try {
    const session = await client.createSession({
      streaming: true,
      tools: [accessibilityRuleLookup],
      availableTools: ["accessibility_rule_lookup"],
    });
    try {
      console.log("\nCopilot:");
      await streamResponse(session, `Use accessibility_rule_lookup to answer this question: ${question}`);
    } finally {
      await session.disconnect();
    }
  } finally {
    await client.stop();
  }
}
