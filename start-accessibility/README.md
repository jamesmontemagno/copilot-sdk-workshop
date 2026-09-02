# Workshop starters

Choose the directory for the language selected on the workshop homepage, then copy it to
`workshop-app`. Starters are intentionally minimal scaffolds. The application-owned Web Content
Accessibility Guidelines (WCAG) catalog and scoped permission/snapshot-reader helpers may be
present for later lessons, but their executable entrypoints do not wire a Copilot client, session,
streaming flow, local tool, MCP server, or report until the corresponding step.

| Language | Prerequisite | Copy and verify |
|---|---|---|
| .NET | [.NET 10 SDK](https://learn.microsoft.com/dotnet/core/install/) | `cp -R start-accessibility/dotnet workshop-app && dotnet build workshop-app` |
| Node.js | [Node.js 22+](https://nodejs.org/) | `cp -R start-accessibility/nodejs workshop-app && cd workshop-app && npm install && npm run build` |
| Python | [Python 3.11+](https://www.python.org/downloads/) | `cp -R start-accessibility/python workshop-app && cd workshop-app && python -m pip install -r requirements.txt && python -m py_compile *.py` |
| Go | [Go 1.24+](https://go.dev/dl/) | `cp -R start-accessibility/go workshop-app && cd workshop-app && go build -mod=readonly ./...` |
| Rust | [Rust 1.94+](https://rustup.rs/) | `cp -R start-accessibility/rust workshop-app && cd workshop-app && cargo check --locked` |
| Java | [Java 17+](https://adoptium.net/) and [Maven](https://maven.apache.org/install.html) | `cp -R start-accessibility/java workshop-app && cd workshop-app && mvn compile` |

On Windows, replace `cp -R` with `Copy-Item -Recurse`. Go, Rust, and Java tracks require the
[GitHub Copilot CLI](https://docs.github.com/en/copilot/how-tos/set-up/install-copilot-cli) on
`PATH` when you later run the application. SDK setup and API references are available in the
[official Copilot SDK repository](https://github.com/github/copilot-sdk) and
[cookbook](https://github.com/github/copilot-sdk/tree/main/cookbook).

Keep using `workshop-app` throughout the workshop. Return to the interactive viewer from the
[workshop homepage](../README.md#start-the-workshop); do not open lesson Markdown directly.
