# Museum Exhibit Studio: Preflight

> **Time:** Untimed  
> **Workshop:** Non-SDLC agent

## What you'll build

Museum Exhibit Studio turns educator-approved facts into visitor-ready exhibit copy:

```text
approved facts -> bounded prompt -> tool-free curator session -> structural validation -> human review
```

Lesson 7 adds a second, separately bounded stage in front of that pipeline:

```text
approved facts -> Wikipedia research session -> educator approval -> the same tool-free curator
```

You need an authenticated GitHub Copilot CLI, your language runtime, and a terminal at the
repository root. Copy the minimal project under `start-museum/<language>` **once**, into
`museum-workshop-app`. Every later lesson edits, builds, and runs that same application, so the CLI
you finish with is the one you started here. The completed implementation under
`finished/<language>/museum-exhibit-studio` is reference material; do not copy it in place of the
starter.

## Clone a clean workshop repository

Start from a parent directory where `copilot-sdk-workshop` does not already exist:

```bash
git clone https://github.com/jamesmontemagno/copilot-sdk-workshop.git
cd copilot-sdk-workshop
```

Confirm that the terminal is at the repository root, the clone has no local changes, and no learner
project exists yet:

```bash
test "$(git rev-parse --show-toplevel)" = "$PWD"
test -z "$(git status --short)"
test ! -e museum-workshop-app
```

All three commands must exit successfully without output. If one fails, stop and use a fresh clone
instead of deleting or overwriting an existing project. Keep this terminal at the repository root
for every command in the museum workshop.

:::language dotnet
Copy the .NET starter, then restore, build, and run its local entrypoint:

```bash
cp -R start-museum/dotnet museum-workshop-app
dotnet restore museum-workshop-app
dotnet build museum-workshop-app --no-restore
dotnet run --project museum-workshop-app --no-build
```

Pass condition: the build succeeds and the executable prints `Museum Exhibit Studio starter (.NET)`.

The copied project is `museum-workshop-app/museum-exhibit-studio.csproj` with
`museum-workshop-app/Program.cs` as its entrypoint and `museum-workshop-app/CuratorRuntime.cs` as
the only SDK adapter. `packages.lock.json` pins SDK 1.0.11.
:::

:::language nodejs
Copy the Node.js starter. Its lockfile preserves SDK 1.0.11 and the compatible `@github/copilot`
1.0.80 platform package:

```bash
cp -R start-museum/nodejs museum-workshop-app
npm --prefix museum-workshop-app ci --ignore-scripts --no-audit --fund=false
npm --prefix museum-workshop-app run build
npm --prefix museum-workshop-app start
```

Pass condition: the type check succeeds and the executable prints
`Museum Exhibit Studio starter (Node.js/TypeScript)`.

The copied project is `museum-workshop-app/package.json` with `museum-workshop-app/src/index.ts` as
its entrypoint and `museum-workshop-app/src/runtime.ts` as the only SDK adapter.
:::

:::language python
Copy the Python starter, create an isolated virtual environment, and install SDK 1.0.11:

```bash
cp -R start-museum/python museum-workshop-app
python3 -m venv museum-workshop-app/.venv
museum-workshop-app/.venv/bin/python -m pip install -r museum-workshop-app/requirements.txt
museum-workshop-app/.venv/bin/python -m py_compile museum-workshop-app/*.py
museum-workshop-app/.venv/bin/python museum-workshop-app/main.py
```

Pass condition: the source compiles and the executable prints `Museum Exhibit Studio starter (Python)`.

The copied project is `museum-workshop-app/requirements.txt` with `museum-workshop-app/main.py` as
its entrypoint and `museum-workshop-app/curator_runtime.py` as the only SDK adapter.
:::

:::language go
Copy the Go starter, download the locked SDK 1.0.11 dependency, and build it:

```bash
cp -R start-museum/go museum-workshop-app
go -C museum-workshop-app mod download
go -C museum-workshop-app build -mod=readonly ./...
go -C museum-workshop-app run .
```

Pass condition: the build succeeds and the executable prints `Museum Exhibit Studio starter (Go)`.

The copied module is `museum-workshop-app/go.mod` with `museum-workshop-app/main.go` as its
entrypoint and `museum-workshop-app/curator_runtime.go` as the only SDK adapter.
:::

:::language rust
Copy the Rust starter, fetch locked dependencies, and check it:

```bash
cp -R start-museum/rust museum-workshop-app
cargo fetch --manifest-path museum-workshop-app/Cargo.toml --locked
cargo check --manifest-path museum-workshop-app/Cargo.toml --locked
cargo run --manifest-path museum-workshop-app/Cargo.toml --locked
```

Pass condition: Cargo leaves `Cargo.lock` unchanged and the executable prints
`Museum Exhibit Studio starter (Rust)`.

The copied crate is `museum-workshop-app/Cargo.toml` with `museum-workshop-app/src/main.rs` as its
binary entrypoint and `museum-workshop-app/src/lib.rs` as the only SDK adapter. Lesson 1 renames the
package, so later lessons drop `--locked` and let Cargo record the change.
:::

:::language java
Copy the Maven starter, resolve SDK 1.0.11, compile, and run it:

```bash
cp -R start-museum/java museum-workshop-app
mvn -f museum-workshop-app/pom.xml dependency:go-offline
mvn -f museum-workshop-app/pom.xml compile
mvn -f museum-workshop-app/pom.xml exec:java
```

Pass condition: Maven succeeds and the executable prints `Museum Exhibit Studio starter (Java)`.

The copied project is `museum-workshop-app/pom.xml` with
`museum-workshop-app/src/main/java/workshop/MuseumExhibitStudio.java` as its entrypoint and
`museum-workshop-app/src/main/java/workshop/CuratorRuntime.java` as the only SDK adapter.
:::

## Establish the trust boundary

| Control | What it can do |
|---|---|
| System message | Guide role, tone, scope, and output shape |
| Empty tool allowlist | Prevent tool invocation |
| Scoped MCP server plus permission handler | Limit which external operations are reachable |
| Application code | Enforce limits, timeout, validation, and cleanup |
| Human review | Decide whether every historical claim is supported |

The supplied facts are the only approved source. Model memory is not verified museum knowledge.

Continue to [Define the curator contract](museum-01-curator-role.md).
