import readline from "node:readline";

const calls = [];
const input = readline.createInterface({ input: process.stdin });

input.on("line", (line) => {
  const request = JSON.parse(line);
  if (request.method === "notifications/initialized") return;

  let result;
  if (request.method === "initialize") {
    result = {
      protocolVersion: "2024-11-05",
      capabilities: { tools: {} },
      serverInfo: { name: "museum-wikipedia-fixture", version: "1.0.0" },
    };
  } else if (request.method === "tools/list") {
    result = {
      tools: [
        {
          name: "search",
          description: "Searches deterministic fixture articles.",
          inputSchema: {
            type: "object",
            properties: { query: { type: "string" } },
            required: ["query"],
          },
        },
        {
          name: "readArticle",
          description: "Reads one deterministic fixture article.",
          inputSchema: {
            type: "object",
            properties: { title: { type: "string" } },
            required: ["title"],
          },
        },
      ],
    };
  } else if (request.method === "tools/call") {
    calls.push(request.params.name);
    if (request.params.name === "search") {
      result = {
        content: [{
          type: "text",
          text: JSON.stringify([{
            title: "Apollo 11",
            url: "https://en.wikipedia.org/wiki/Apollo_11",
          }]),
        }],
      };
    } else if (request.params.name === "readArticle") {
      if (calls[0] !== "search") {
        result = { isError: true, content: [{ type: "text", text: "Call search first." }] };
      } else {
        result = {
          content: [{
            type: "text",
            text: JSON.stringify({
              title: "Apollo 11",
              url: "https://en.wikipedia.org/wiki/Apollo_11",
              text: "Apollo 11 launched July 16, 1969.",
              calls,
            }),
          }],
        };
      }
    } else {
      result = { isError: true, content: [{ type: "text", text: "Unknown tool." }] };
    }
  } else {
    result = {};
  }

  process.stdout.write(`${JSON.stringify({ jsonrpc: "2.0", id: request.id, result })}\n`);
});
