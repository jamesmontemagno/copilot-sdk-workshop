import readline from "node:readline";

let searched = false;
const input = readline.createInterface({ input: process.stdin, crlfDelay: Infinity });

function respond(id, result, error) {
  process.stdout.write(`${JSON.stringify({
    jsonrpc: "2.0",
    id,
    ...(error ? { error } : { result }),
  })}\n`);
}

input.on("line", (line) => {
  const request = JSON.parse(line);
  if (request.method === "initialize") {
    respond(request.id, {
      protocolVersion: "2025-06-18",
      capabilities: { tools: {} },
      serverInfo: { name: "mock-wikipedia", version: "1.0.0" },
    });
  } else if (request.method === "tools/list") {
    respond(request.id, {
      tools: [
        {
          name: "search",
          description: "Search deterministic Wikipedia fixtures.",
          inputSchema: { type: "object", properties: { query: { type: "string" } } },
        },
        {
          name: "readArticle",
          description: "Read the selected deterministic article.",
          inputSchema: { type: "object", properties: { title: { type: "string" } } },
        },
      ],
    });
  } else if (request.method === "tools/call" && request.params?.name === "search") {
    searched = true;
    respond(request.id, {
      content: [{
        type: "text",
        text: JSON.stringify([{
          title: "Apollo 11",
          url: "https://en.wikipedia.org/wiki/Apollo_11",
        }]),
      }],
    });
  } else if (request.method === "tools/call" && request.params?.name === "readArticle") {
    if (!searched) {
      respond(request.id, null, { code: -32000, message: "search must run first" });
    } else {
      respond(request.id, {
        content: [{
          type: "text",
          text: "Apollo 11 launched on July 16, 1969.",
        }],
      });
    }
  } else if (request.id !== undefined) {
    respond(request.id, null, { code: -32601, message: "method not found" });
  }
});
