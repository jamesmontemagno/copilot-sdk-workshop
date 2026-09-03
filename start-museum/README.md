# Museum Exhibit Studio starters

Choose the directory for your workshop language and work directly inside it. After you change into
it, open that same folder in your editor (`code .` from inside it, or any other editor's open-folder
command) and keep your terminal there. These starters contain pinned dependencies, a minimal
executable, and one pre-built curator helper module. The helpers hold the plumbing you never have
to write: the approved fact sets and their bounds, the pre-built `approved_fact_lookup` local tool
that hands those facts to the curator, a streaming printer, deterministic exhibit validation, the
scoped Wikipedia MCP server and its deny-by-default permission handler, the single-file
`exhibit.html` write permission, and small terminal prompts. You never edit the helpers.

The starters do **not** include the curator system message, the exhibit prompt, session
configuration, tool registration, or any orchestration. You write those during the lessons: one
session, then streaming, then the curator voice, the fact tool registration and its prompt, one
session runner that owns the guardrails, the validation report, scoped Wikipedia research, and an
optional `exhibit.html` page. Each starter entrypoint carries comments marking exactly where each
step's code goes. Start at [`workshop/museum-00-preflight.md`](../workshop/museum-00-preflight.md).

| Language | Helper module | Change directory, build, and run |
|---|---|---|
| .NET | `Helpers/Curator*.cs` | `cd start-museum/dotnet && dotnet build && dotnet run` |
| Node.js | `src/curator.ts` | `cd start-museum/nodejs && npm ci && npm run build && npm start` |
| Python | `curator.py` | `cd start-museum/python && python -m venv .venv && .venv/bin/python -m pip install -r requirements.txt && .venv/bin/python main.py` |
| Go | `curator.go` | `cd start-museum/go && go build -mod=readonly ./... && go run .` |
| Rust | `src/lib.rs` | `cd start-museum/rust && cargo check --locked && cargo run --locked` |
| Java | `src/main/java/workshop/Curator*.java` | `cd start-museum/java && mvn compile && mvn exec:java` |

Running the starter prints its identity and does not start Copilot or require authentication.
Because you edit these files in place, your work shows up in `git status`. That is expected. Run
`git checkout -- .` from the repository root to restore a clean starter.

Every starter already pins the dependencies the finished application needs, so you never edit a
project manifest during the workshop. The Rust starter builds the `museum_exhibit_studio` library
crate from `src/lib.rs`; import the helpers from it in `src/main.rs`.
