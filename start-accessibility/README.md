# Workshop starters

Choose the directory for the language selected on the workshop homepage, then work directly inside
it. There is no copy step. Starters are intentionally minimal scaffolds. The application-owned Web
Content Accessibility Guidelines (WCAG) catalog and scoped permission/snapshot-reader helpers may be
present for later lessons, but their executable entrypoints do not wire a Copilot client, session,
streaming flow, local tool, MCP server, or report until the corresponding step.

| Language | Prerequisite | Change directory and verify |
|---|---|---|
| .NET | [.NET 10 SDK](https://learn.microsoft.com/dotnet/core/install/) | `cd start-accessibility/dotnet && dotnet build` |
| Node.js | [Node.js 22+](https://nodejs.org/) | `cd start-accessibility/nodejs && npm install && npm run build` |
| Python | [Python 3.11+](https://www.python.org/downloads/) | `cd start-accessibility/python && python -m pip install -r requirements.txt && python -m py_compile *.py` |
| Go | [Go 1.24+](https://go.dev/dl/) | `cd start-accessibility/go && go build -mod=readonly ./...` |
| Rust | [Rust 1.94+](https://rustup.rs/) | `cd start-accessibility/rust && cargo check --locked` |
| Java | [Java 17+](https://adoptium.net/) and [Maven](https://maven.apache.org/install.html) | `cd start-accessibility/java && mvn compile` |

Because you edit these files in place, your work shows up in `git status`. That is expected. Run
`git checkout -- .` from the repository root to restore a clean starter. Go, Rust, and Java tracks
require the
[GitHub Copilot CLI](https://docs.github.com/en/copilot/how-tos/set-up/install-copilot-cli) on
`PATH` when you later run the application. SDK setup and API references are available in the
[official Copilot SDK repository](https://github.com/github/copilot-sdk) and
[cookbook](https://github.com/github/copilot-sdk/tree/main/cookbook).

Stay in your starter directory for the whole workshop. Return to the interactive viewer from the
[workshop homepage](../README.md#start-the-workshop); do not open lesson Markdown directly.
