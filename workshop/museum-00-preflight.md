# Museum Exhibit Studio: Preflight

> **Time:** Untimed  
> **Workshop:** Non-SDLC agent

## What you'll build

Museum Exhibit Studio turns educator-approved facts into visitor-ready exhibit copy:

```text
approved facts -> bounded prompt -> curator session -> structural checks -> human review
```

You build one growing console application called `museum-workshop-app`. Each step adds one idea and
ends with a real run, so the curator comes together in front of you:

| Step | You add | You see |
|---|---|---|
| 1 | A client, a session, one prompt | Museum copy in your terminal |
| 2 | The pre-built streaming printer | Text arriving live |
| 3 | The curator system message | A different voice and shape |
| 4 | The approved-fact prompt builder | Copy that tracks your facts |
| 5 | One session runner with the guardrails | Refused tools and friendly failures |
| 6 | The pre-built validator | A PASS/FAIL structural report |
| 7 | A scoped Wikipedia research session | Cited background, kept out of the exhibit |
| 8 | An optional interactive page | `exhibit.html` in your browser |

The starter already ships the plumbing you should never have to write: the approved fact sets and
their bounds, a streaming printer, deterministic exhibit validation, the scoped Wikipedia MCP server
with its deny-by-default permission handler, the single-file `exhibit.html` write permission, and
small terminal prompts. **You never edit the helper module.** You write the session setup, the two
system messages, the prompt builders, one session runner, and `main`.

You need an authenticated GitHub Copilot CLI, your language runtime, and a terminal at the
repository root. Start from the minimal project under `start-museum/<language>`, not the finished
app. The completed project under `finished/<language>/museum-exhibit-studio` is optional reference
material only.

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

Pass condition: the build succeeds and the program prints `=== Museum Exhibit Studio starter ===`
followed by `Pre-built curator helpers are ready in Helpers/.`

Your helper module is `museum-workshop-app/Helpers/Curator*.cs` in the
`MuseumExhibitStudio.Helpers` namespace. You will write every lesson change in
`museum-workshop-app/Program.cs`.
:::

:::language nodejs
Copy the Node.js starter. Its lockfile preserves SDK 1.0.11 and
the compatible `@github/copilot` 1.0.80 platform package:

```bash
cp -R start-museum/nodejs museum-workshop-app
npm --prefix museum-workshop-app ci --ignore-scripts --no-audit --fund=false
npm --prefix museum-workshop-app run build
npm --prefix museum-workshop-app start
```

Pass condition: the build succeeds and the program prints `=== Museum Exhibit Studio starter ===`
followed by `Pre-built curator helpers are ready in src/curator.ts.`

Your helper module is `museum-workshop-app/src/curator.ts`. You will write every lesson change in
`museum-workshop-app/src/index.ts`.
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

On Windows, the interpreter lives at `museum-workshop-app/.venv/Scripts/python.exe`.

Pass condition: the source compiles and the program prints `=== Museum Exhibit Studio starter ===`
followed by `Pre-built curator helpers are ready in curator.py.`

Your helper module is `museum-workshop-app/curator.py`. You will write every lesson change in
`museum-workshop-app/main.py`.
:::

:::language go
Copy the Go starter, download the locked SDK 1.0.11 dependency, and build it:

```bash
cp -R start-museum/go museum-workshop-app
go -C museum-workshop-app mod download
go -C museum-workshop-app build -mod=readonly ./...
go -C museum-workshop-app run .
```

Pass condition: the build succeeds and the program prints `=== Museum Exhibit Studio starter ===`
followed by `Pre-built curator helpers are ready in curator.go.`

Your helper module is `museum-workshop-app/curator.go`, in the same `main` package. You will write
every lesson change in `museum-workshop-app/main.go`.
:::

:::language rust
Copy the Rust starter, fetch locked dependencies, and check it:

```bash
cp -R start-museum/rust museum-workshop-app
cargo fetch --manifest-path museum-workshop-app/Cargo.toml --locked
cargo check --manifest-path museum-workshop-app/Cargo.toml --locked
cargo run --manifest-path museum-workshop-app/Cargo.toml --locked
```

Pass condition: Cargo leaves `Cargo.lock` unchanged and the program prints
`=== Museum Exhibit Studio starter ===` followed by
`Pre-built curator helpers are ready in src/lib.rs.`

Your helper module is the `museum_exhibit_studio` library crate in `museum-workshop-app/src/lib.rs`.
You will write every lesson change in `museum-workshop-app/src/main.rs`.
:::

:::language java
Copy the Maven starter, resolve SDK 1.0.11, compile, and run it:

```bash
cp -R start-museum/java museum-workshop-app
mvn -f museum-workshop-app/pom.xml dependency:go-offline
mvn -f museum-workshop-app/pom.xml compile
mvn -f museum-workshop-app/pom.xml exec:java
```

Pass condition: Maven succeeds and the program prints `=== Museum Exhibit Studio starter ===`
followed by `Pre-built curator helpers are ready in src/main/java/workshop/.`

Your helper module is `museum-workshop-app/src/main/java/workshop/Curator*.java`. You will write
every lesson change in `museum-workshop-app/src/main/java/workshop/MuseumExhibitStudio.java`.
:::

On Windows, replace `cp -R` with `Copy-Item -Recurse`.

## Establish the trust boundary

| Control | What it can do |
|---|---|
| System message | Guide role, tone, scope, and output shape |
| Empty tool allowlist | Prevent tool invocation |
| Application code | Enforce limits, timeout, validation, and cleanup |
| Human review | Decide whether every historical claim is supported |

The supplied facts are the only approved source. Model memory is not verified museum knowledge, and
prompt guidance is not an authorization boundary: only the allowlist and the permission handler
decide what the session may actually do.

Continue to [Your first curator session](museum-01-first-curator-session.md).
