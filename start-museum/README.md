# Museum Exhibit Studio starters

Choose the directory for your workshop language, then copy it to `museum-workshop-app`.
These starters contain pinned dependencies, a minimal executable, and one pre-built curator
helper module. The helpers hold the plumbing you never have to write: the approved fact sets and
their bounds, a streaming printer, deterministic exhibit validation, the scoped Wikipedia MCP
server and its deny-by-default permission handler, the single-file `exhibit.html` write
permission, and small terminal prompts. You never edit the helpers.

The starters do **not** include the curator system message, the exhibit prompt, session
configuration, or any orchestration. You write those during the lessons: one session, then
streaming, then the curator voice, the approved-fact prompt builder, one session runner that owns
the guardrails, the validation report, scoped Wikipedia research, and an optional `exhibit.html`
page. Start at [`workshop/museum-00-preflight.md`](../workshop/museum-00-preflight.md).

| Language | Helper module | Copy, build, and run |
|---|---|---|
| .NET | `Helpers/Curator*.cs` | `cp -R start-museum/dotnet museum-workshop-app && dotnet build museum-workshop-app && dotnet run --project museum-workshop-app` |
| Node.js | `src/curator.ts` | `cp -R start-museum/nodejs museum-workshop-app && npm --prefix museum-workshop-app ci && npm --prefix museum-workshop-app run build && npm --prefix museum-workshop-app start` |
| Python | `curator.py` | `cp -R start-museum/python museum-workshop-app && python -m venv museum-workshop-app/.venv && museum-workshop-app/.venv/bin/python -m pip install -r museum-workshop-app/requirements.txt && museum-workshop-app/.venv/bin/python museum-workshop-app/main.py` |
| Go | `curator.go` | `cp -R start-museum/go museum-workshop-app && go -C museum-workshop-app build -mod=readonly ./... && go -C museum-workshop-app run .` |
| Rust | `src/lib.rs` | `cp -R start-museum/rust museum-workshop-app && cargo check --locked --manifest-path museum-workshop-app/Cargo.toml && cargo run --locked --manifest-path museum-workshop-app/Cargo.toml` |
| Java | `src/main/java/workshop/Curator*.java` | `cp -R start-museum/java museum-workshop-app && mvn -f museum-workshop-app/pom.xml compile && mvn -f museum-workshop-app/pom.xml exec:java` |

On Windows, replace `cp -R` with `Copy-Item -Recurse`. Running the starter prints its identity and
does not start Copilot or require authentication.

Every starter already pins the dependencies the finished application needs, so you never edit a
project manifest during the workshop. The Rust starter builds the `museum_exhibit_studio` library
crate from `src/lib.rs`; import the helpers from it in `src/main.rs`.
