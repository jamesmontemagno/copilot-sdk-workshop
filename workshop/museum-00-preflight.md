# Museum Exhibit Studio: Preflight

> **Time:** Untimed  
> **Workshop:** Non-SDLC agent

## What you'll build

Museum Exhibit Studio turns educator-approved facts into visitor-ready exhibit copy:

```text
approved facts -> bounded prompt -> curator session -> structural checks -> human review
```

You build one growing console application in place, inside `start-museum/<language>`. Each
step adds one idea and ends with a real run, so the curator comes together in front of you:

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

You need an authenticated GitHub Copilot CLI, your language runtime, and a terminal. You work
directly in the minimal project under `start-museum/<language>`, not the finished app. The completed
project under `finished/<language>/museum-exhibit-studio` is optional reference material only.

## Clone the workshop repository

```bash
git clone https://github.com/jamesmontemagno/copilot-sdk-workshop.git
cd copilot-sdk-workshop
```

Confirm the terminal is at the repository root before you change into a starter:

```bash
test "$(git rev-parse --show-toplevel)" = "$PWD"
```

The command must exit successfully without output.

You build the museum application **in place**, inside the starter directory for your language.
There is no copy step. That means you are editing tracked repository files, so your work shows up in
`git status` as modified files. That is expected and correct. If you want to start over from a clean
starter, run `git checkout -- .` from the repository root to discard your edits.

Change into your language's starter directory now and stay there for every command in the museum
workshop.

:::language dotnet
Change into the .NET starter, then restore, build, and run its local entrypoint:

```bash
cd start-museum/dotnet
dotnet restore
dotnet build --no-restore
dotnet run --no-build
```

Pass condition: the build succeeds and the program prints `=== Museum Exhibit Studio starter ===`
followed by `Pre-built curator helpers are ready in Helpers/.`

You work in `start-museum/dotnet` for the rest of the workshop, so keep this terminal here. From
this folder, enter `code .` to open it in VS Code, or open the folder in your favorite editor.

Your helper module is `Helpers/Curator*.cs` in the `MuseumExhibitStudio.Helpers` namespace. You
will write every lesson change in `Program.cs`.
:::

:::language nodejs
Change into the Node.js starter. Its lockfile preserves SDK 1.0.11 and
the compatible `@github/copilot` 1.0.80 platform package:

```bash
cd start-museum/nodejs
npm ci --ignore-scripts --no-audit --fund=false
npm run build
npm start
```

Pass condition: the build succeeds and the program prints `=== Museum Exhibit Studio starter ===`
followed by `Pre-built curator helpers are ready in src/curator.ts.`

You work in `start-museum/nodejs` for the rest of the workshop, so keep this terminal here. From
this folder, enter `code .` to open it in VS Code, or open the folder in your favorite editor.

Your helper module is `src/curator.ts`. You will write every lesson change in `src/index.ts`.
:::

:::language python
Change into the Python starter, create an isolated virtual environment, and install SDK 1.0.11:

```bash
cd start-museum/python
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m py_compile *.py
.venv/bin/python main.py
```

On Windows, the interpreter lives at `.venv/Scripts/python.exe`.

Pass condition: the source compiles and the program prints `=== Museum Exhibit Studio starter ===`
followed by `Pre-built curator helpers are ready in curator.py.`

You work in `start-museum/python` for the rest of the workshop, so keep this terminal here. From
this folder, enter `code .` to open it in VS Code, or open the folder in your favorite editor.

Your helper module is `curator.py`. You will write every lesson change in `main.py`.
:::

:::language go
Change into the Go starter, download the locked SDK 1.0.11 dependency, and build it:

```bash
cd start-museum/go
go mod download
go build -mod=readonly ./...
go run .
```

Pass condition: the build succeeds and the program prints `=== Museum Exhibit Studio starter ===`
followed by `Pre-built curator helpers are ready in curator.go.`

You work in `start-museum/go` for the rest of the workshop, so keep this terminal here. From
this folder, enter `code .` to open it in VS Code, or open the folder in your favorite editor.

Your helper module is `curator.go`, in the same `main` package. You will write every lesson
change in `main.go`.
:::

:::language rust
Change into the Rust starter, fetch locked dependencies, and check it:

```bash
cd start-museum/rust
cargo fetch --locked
cargo check --locked
cargo run --locked
```

Pass condition: Cargo leaves `Cargo.lock` unchanged and the program prints
`=== Museum Exhibit Studio starter ===` followed by
`Pre-built curator helpers are ready in src/lib.rs.`

You work in `start-museum/rust` for the rest of the workshop, so keep this terminal here. From
this folder, enter `code .` to open it in VS Code, or open the folder in your favorite editor.

Your helper module is the `museum_exhibit_studio` library crate in `src/lib.rs`. You will write
every lesson change in `src/main.rs`.
:::

:::language java
Change into the Maven starter, resolve SDK 1.0.11, compile, and run it:

```bash
cd start-museum/java
mvn dependency:go-offline
mvn compile
mvn exec:java
```

Pass condition: Maven succeeds and the program prints `=== Museum Exhibit Studio starter ===`
followed by `Pre-built curator helpers are ready in src/main/java/workshop/.`

You work in `start-museum/java` for the rest of the workshop, so keep this terminal here. From
this folder, enter `code .` to open it in VS Code, or open the folder in your favorite editor.

Your helper module is `src/main/java/workshop/Curator*.java`. You will write every lesson change
in `src/main/java/workshop/MuseumExhibitStudio.java`.
:::

## Establish the trust boundary

| Control | What it can do |
|---|---|
| System message | Guide role, tone, scope, and output shape |
| Tool allowlist | Decide exactly which tools exist for a session |
| Application code | Own the data behind a tool, and enforce limits, timeout, validation, and cleanup |
| Human review | Decide whether every historical claim is supported |

The educator's approved facts are the only approved source, and the curator reaches them through
one application-owned tool. Model memory is not verified museum knowledge, and prompt guidance is
not an authorization boundary: only the allowlist and the permission handler decide what the
session may actually do.

Continue to [Your first curator session](museum-01-first-curator-session.md).
