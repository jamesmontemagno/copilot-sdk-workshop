# Museum Exhibit Studio: Preflight

> **Time:** Untimed  
> **Workshop:** Non-SDLC agent

## What you'll build

Museum Exhibit Studio turns educator-approved facts into visitor-ready exhibit copy:

```text
approved facts -> bounded prompt -> curator session -> structural validation -> human review
```

You need an authenticated GitHub Copilot CLI, your language runtime, and a terminal at the
repository root. Start from the minimal project under `start-museum/<language>`, not the finished app.
The completed project under `finished/<language>/museum-exhibit-studio` is optional reference
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

Pass condition: the build succeeds and the executable prints `Museum Exhibit Studio starter (.NET)`.
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

Pass condition: the build succeeds and the executable identifies the Node.js/TypeScript museum starter.
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

Pass condition: the source compiles and the executable identifies the Python museum starter.
:::

:::language go
Copy the Go starter, download the locked SDK 1.0.11 dependency, and build it:

```bash
cp -R start-museum/go museum-workshop-app
go -C museum-workshop-app mod download
go -C museum-workshop-app build -mod=readonly ./...
go -C museum-workshop-app run .
```

Pass condition: the build succeeds and the executable identifies the Go museum starter.
:::

:::language rust
Copy the Rust starter, fetch locked dependencies, and check it:

```bash
cp -R start-museum/rust museum-workshop-app
cargo fetch --manifest-path museum-workshop-app/Cargo.toml --locked
cargo check --manifest-path museum-workshop-app/Cargo.toml --locked
cargo run --manifest-path museum-workshop-app/Cargo.toml --locked
```

Pass condition: Cargo leaves `Cargo.lock` unchanged and the executable identifies the Rust museum starter.
:::

:::language java
Copy the Maven starter, resolve SDK 1.0.11, compile, and run it:

```bash
cp -R start-museum/java museum-workshop-app
mvn -f museum-workshop-app/pom.xml dependency:go-offline
mvn -f museum-workshop-app/pom.xml compile
mvn -f museum-workshop-app/pom.xml exec:java
```

Pass condition: Maven succeeds and the executable identifies the Java museum starter.
:::

## Establish the trust boundary

| Control | What it can do |
|---|---|
| System message | Guide role, tone, scope, and output shape |
| Empty tool allowlist | Prevent tool invocation |
| Application code | Enforce limits, timeout, validation, and cleanup |
| Human review | Decide whether every historical claim is supported |

The supplied facts are the only approved source. Model memory is not verified museum knowledge.
Continue to [Define the curator contract](museum-01-curator-role.md).
