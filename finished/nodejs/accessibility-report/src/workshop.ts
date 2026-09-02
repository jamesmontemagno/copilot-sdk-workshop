import { defineTool, type CopilotSession, type PermissionHandler } from "@github/copilot-sdk";
import { z } from "zod";
import { lstat, readdir, readFile } from "node:fs/promises";
import { resolve } from "node:path";
import { accessibilityRules } from "./accessibility-rule-catalog.js";

const maxSnapshotBytes = 1_000_000;
const noMatch = { criterion: "No exact match", title: "Criterion not found", whenItApplies: "The issue is not represented in the workshop catalog.", recommendation: "Verify the evidence and consult the complete WCAG reference.", keywords: [] };

export const accessibilityRuleLookup = defineTool("accessibility_rule_lookup", {
  description: "Looks up read-only WCAG guidance maintained by this application.",
  parameters: z.object({ query: z.string().describe("The accessibility issue or WCAG criterion to look up.") }),
  skipPermission: true,
  handler: async ({ query }) => {
    const normalized = query.trim().toLowerCase();
    return accessibilityRules.find((rule) => normalized.includes(rule.criterion.toLowerCase()) || normalized.includes(rule.title.toLowerCase()) || rule.keywords.some((keyword) => normalized.includes(keyword))) ?? noMatch;
  },
});

export function createSnapshotReader(workingDirectory: string) {
  const outputDirectory = resolve(workingDirectory, ".playwright-mcp");
  const existingSnapshots = safeSnapshotNames(outputDirectory).then((names) => new Set(names.map((name) => resolve(outputDirectory, name))));
  return defineTool("read_latest_accessibility_snapshot", {
    description: "Reads the newest Playwright accessibility snapshot created during this run.",
    parameters: z.object({}),
    skipPermission: true,
    handler: async () => {
      const baseline = await existingSnapshots;
      const candidates = await Promise.all((await safeSnapshotNames(outputDirectory)).map(async (name) => {
        const path = resolve(outputDirectory, name);
        const details = await lstat(path);
        return { path, details };
      }));
      const snapshot = candidates
        .filter(({ path, details }) => !baseline.has(path) && !details.isSymbolicLink() && details.isFile() && details.size > 0 && details.size <= maxSnapshotBytes)
        .sort((left, right) => right.details.mtimeMs - left.details.mtimeMs)[0];
      if (!snapshot) throw new Error("No current-run Playwright snapshot is available. Call browser_navigate first.");
      return readFile(snapshot.path, "utf8");
    },
  });
}

async function safeSnapshotNames(directory: string): Promise<string[]> {
  try { return (await readdir(directory)).filter((name) => /^page-.*\.yml$/.test(name)); }
  catch { return []; }
}

export function permissionForTarget(target: URL): PermissionHandler {
  return (request) => {
    if (request.kind === "mcp" && request.serverName === "playwright" &&
      (request.toolName === "browser_navigate" || request.toolName === "playwright-browser_navigate")) {
      const args = request.args;
      const requestedUrl = args !== null && typeof args === "object" && !Array.isArray(args) &&
        typeof args.url === "string" ? args.url : undefined;
      if (requestedUrl && sameUrl(new URL(requestedUrl), target)) return { kind: "approve-once" };
    }
    return { kind: "reject", feedback: "This workshop allows Playwright to navigate only to the exact requested target." };
  };
}

function sameUrl(requested: URL, allowed: URL): boolean {
  return requested.protocol.toLowerCase() === allowed.protocol.toLowerCase() &&
    requested.hostname.toLowerCase() === allowed.hostname.toLowerCase() &&
    requested.port === allowed.port && requested.username === allowed.username &&
    requested.password === allowed.password && requested.pathname === allowed.pathname &&
    requested.search === allowed.search && requested.hash === allowed.hash;
}

export async function streamResponse(session: CopilotSession, prompt: string): Promise<void> {
  await new Promise<void>((resolve, reject) => {
    let receivedDelta = false;
    const unsubscribe = session.on((event) => {
      if (event.type === "assistant.message_delta" && event.data.deltaContent) { receivedDelta = true; process.stdout.write(event.data.deltaContent); }
      else if (event.type === "assistant.message" && !receivedDelta) process.stdout.write(event.data.content);
      else if (event.type === "tool.execution_start") console.log(`\n[tool:start] ${event.data.toolName}`);
      else if (event.type === "tool.execution_complete") console.log(`[tool:done] success=${event.data.success}`);
      else if (event.type === "session.error") reject(new Error(event.data.message));
      else if (event.type === "session.idle") { console.log(); unsubscribe(); resolve(); }
    });
    void session.send({ prompt }).catch(reject);
  });
}

export function reportPrompt(target: URL): string {
  return `Prepare an evidence-based accessibility review of ${target.href}.
1. Use browser_navigate to open that exact URL.
2. Call read_latest_accessibility_snapshot to inspect its accessibility tree.
3. Identify three to five high-confidence issues supported by the snapshot.
4. Call accessibility_rule_lookup for each issue before recommending a fix.

Return only this structure:
# Accessibility review
## Finding 1: <short name>
- Evidence: <specific element or page structure observed in the browser>
- WCAG criterion: <criterion and title returned by the catalog>
- Recommended remediation: <specific implementation change>
Repeat the finding section as needed.
## Review limits
State that this is a focused review of browser-observable evidence, not a full WCAG conformance audit.
Do not invent evidence, report unsupported statistics, or claim the page is WCAG compliant.`;
}
