# Museum Exhibit Studio starters

Choose the directory for your workshop language, then copy it to `museum-workshop-app`.
These starters contain pinned dependencies, a minimal executable, and only the low-level Copilot
client/session adapters used by later lessons. They do not include curator prompts, exhibit
validation, service orchestration, Wikipedia research, or finished application behavior.

| Language | Copy, build, and run |
|---|---|
| .NET | `cp -R start-museum/dotnet museum-workshop-app && dotnet build museum-workshop-app && dotnet run --project museum-workshop-app` |
| Node.js | `cp -R start-museum/nodejs museum-workshop-app && npm --prefix museum-workshop-app ci && npm --prefix museum-workshop-app run build && npm --prefix museum-workshop-app start` |
| Python | `cp -R start-museum/python museum-workshop-app && python -m venv museum-workshop-app/.venv && museum-workshop-app/.venv/bin/python -m pip install -r museum-workshop-app/requirements.txt && museum-workshop-app/.venv/bin/python museum-workshop-app/main.py` |
| Go | `cp -R start-museum/go museum-workshop-app && go -C museum-workshop-app build -mod=readonly ./... && go -C museum-workshop-app run .` |
| Rust | `cp -R start-museum/rust museum-workshop-app && cargo check --locked --manifest-path museum-workshop-app/Cargo.toml && cargo run --locked --manifest-path museum-workshop-app/Cargo.toml` |
| Java | `cp -R start-museum/java museum-workshop-app && mvn -f museum-workshop-app/pom.xml compile && mvn -f museum-workshop-app/pom.xml exec:java` |

On Windows, replace `cp -R` with `Copy-Item -Recurse`. Running the starter prints its identity and
does not start Copilot or require authentication.
