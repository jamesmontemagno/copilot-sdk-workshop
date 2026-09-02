import assert from "node:assert/strict";
import { spawn, type ChildProcessWithoutNullStreams } from "node:child_process";
import { once } from "node:events";
import { createInterface } from "node:readline";
import test from "node:test";

test("mock MCP exposes only search and readArticle in required order", async () => {
  const server = spawn(process.execPath, ["tests/fixtures/wikipedia-mcp.mjs"], {
    cwd: new URL("..", import.meta.url),
    stdio: ["pipe", "pipe", "pipe"],
  });
  const responses = createInterface({ input: server.stdout });
  const pending: Array<(value: unknown) => void> = [];
  responses.on("line", (line) => pending.shift()?.(JSON.parse(line).result));

  try {
    await call(server, pending, 1, "initialize", {});
    const list = await call(server, pending, 2, "tools/list", {}) as {
      tools: Array<{ name: string }>;
    };
    assert.deepEqual(list.tools.map((tool) => tool.name), ["search", "readArticle"]);

    await call(server, pending, 3, "tools/call", {
      name: "search",
      arguments: { query: "Apollo 11" },
    });
    const article = await call(server, pending, 4, "tools/call", {
      name: "readArticle",
      arguments: { title: "Apollo 11" },
    }) as { content: Array<{ text: string }> };
    assert.deepEqual(JSON.parse(article.content[0]!.text).calls, ["search", "readArticle"]);
  } finally {
    responses.close();
    server.kill("SIGTERM");
    await once(server, "exit");
  }
  assert.equal(server.signalCode, "SIGTERM");
});

function call(
  server: ChildProcessWithoutNullStreams,
  pending: Array<(value: unknown) => void>,
  id: number,
  method: string,
  params: object,
): Promise<unknown> {
  const result = new Promise<unknown>((resolve) => pending.push(resolve));
  server.stdin.write(`${JSON.stringify({ jsonrpc: "2.0", id, method, params })}\n`);
  return result;
}
