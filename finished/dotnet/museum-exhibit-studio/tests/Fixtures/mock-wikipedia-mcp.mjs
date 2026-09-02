import readline from "node:readline";

const input = readline.createInterface({
  input: process.stdin,
  crlfDelay: Infinity,
});

let searched = false;

input.on("line", (line) => {
  const request = JSON.parse(line);
  const respond = (result) => process.stdout.write(
    `${JSON.stringify({ jsonrpc: "2.0", id: request.id, result })}\n`,
  );
  const fail = (message) => process.stdout.write(
    `${JSON.stringify({
      jsonrpc: "2.0",
      id: request.id,
      error: { code: -32000, message },
    })}\n`,
  );

  if (request.method === "initialize") {
    respond({
      protocolVersion: "2025-03-26",
      capabilities: { tools: {} },
      serverInfo: { name: "mock-wikipedia", version: "1.0.0" },
    });
    return;
  }
  if (request.method === "tools/list") {
    respond({
      tools: [
        {
          name: "search",
          description: "Search fixture Wikipedia",
          inputSchema: { type: "object", properties: { query: { type: "string" } } },
        },
        {
          name: "readArticle",
          description: "Read one fixture article",
          inputSchema: { type: "object", properties: { title: { type: "string" } } },
        },
      ],
    });
    return;
  }
  if (request.method === "tools/call" && request.params?.name === "search") {
    searched = true;
    respond({
      content: [{
        type: "text",
        text: JSON.stringify([{
          title: "Apollo 11",
          url: "https://en.wikipedia.org/wiki/Apollo_11",
        }]),
      }],
    });
    return;
  }
  if (request.method === "tools/call" && request.params?.name === "readArticle") {
    if (!searched) {
      fail("search must be called before readArticle");
      return;
    }
    respond({
      content: [{
        type: "text",
        text: "Apollo 11 fixture article content.",
      }],
    });
    return;
  }

  fail("unsupported fixture request");
});
