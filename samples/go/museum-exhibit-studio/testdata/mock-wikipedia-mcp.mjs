import readline from "node:readline";

let searched = false;

const input = readline.createInterface({ input: process.stdin });
input.on("line", (line) => {
  const request = JSON.parse(line);
  if (request.method === "initialize") {
    reply(request.id, {
      protocolVersion: "2025-06-18",
      capabilities: { tools: {} },
      serverInfo: { name: "mock-wikipedia", version: "1.0.0" },
    });
    return;
  }
  if (request.method === "tools/list") {
    reply(request.id, {
      tools: [
        {
          name: "search",
          description: "Searches mock Wikipedia.",
          inputSchema: { type: "object", properties: { query: { type: "string" } } },
        },
        {
          name: "readArticle",
          description: "Reads a mock Wikipedia article.",
          inputSchema: { type: "object", properties: { title: { type: "string" } } },
        },
      ],
    });
    return;
  }
  if (request.method === "tools/call" && request.params?.name === "search") {
    searched = true;
    reply(request.id, {
      content: [{ type: "text", text: "Apollo 11 | https://en.wikipedia.org/wiki/Apollo_11" }],
    });
    return;
  }
  if (request.method === "tools/call" && request.params?.name === "readArticle") {
    if (!searched) {
      error(request.id, -32000, "search must happen before readArticle");
      return;
    }
    reply(request.id, {
      content: [{ type: "text", text: "Apollo 11 launched on July 16, 1969." }],
    });
    return;
  }
  if (request.id !== undefined) {
    error(request.id, -32601, "method not found");
  }
});

function reply(id, result) {
  process.stdout.write(`${JSON.stringify({ jsonrpc: "2.0", id, result })}\n`);
}

function error(id, code, message) {
  process.stdout.write(`${JSON.stringify({ jsonrpc: "2.0", id, error: { code, message } })}\n`);
}
