# Museum Exhibit Studio: Preflight

> **Time:** Untimed  
> **Workshop:** Non-SDLC agent

## What you'll build

Museum Exhibit Studio turns educator-approved facts into visitor-ready exhibit copy:

```text
approved facts -> bounded prompt -> curator session -> structural validation -> human review
```

You need an authenticated GitHub Copilot CLI, your language runtime, and a terminal at the
repository root. Start with dependencies and empty source directories, not the finished app.
The completed project under `samples/<language>/museum-exhibit-studio` is optional reference
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
Create the learner project with the two project manifests and a temporary entrypoint, then restore
SDK 1.0.11 and the test packages:

```bash
mkdir -p museum-workshop-app/tests
cp samples/dotnet/museum-exhibit-studio/museum-exhibit-studio.csproj museum-workshop-app/
cp samples/dotnet/museum-exhibit-studio/tests/museum-exhibit-studio.Tests.csproj museum-workshop-app/tests/
printf 'Console.WriteLine("Museum Exhibit Studio starter");\n' > museum-workshop-app/Program.cs
dotnet restore museum-workshop-app/tests/museum-exhibit-studio.Tests.csproj
```

Pass condition: restore completes without changing either project file. Lesson 6 replaces the
temporary entrypoint with the finished CLI.
:::

:::language nodejs
Copy only the package and TypeScript configuration files. The lockfile preserves SDK 1.0.11 and
the compatible `@github/copilot` 1.0.80 platform package:

```bash
mkdir -p museum-workshop-app/src museum-workshop-app/tests
cp samples/nodejs/museum-exhibit-studio/package.json museum-workshop-app/
cp samples/nodejs/museum-exhibit-studio/package-lock.json museum-workshop-app/
cp samples/nodejs/museum-exhibit-studio/tsconfig.json museum-workshop-app/
npm --prefix museum-workshop-app ci --ignore-scripts --no-audit --fund=false
```

Pass condition: `npm` exits successfully and `museum-workshop-app/src` remains empty.
:::

:::language python
Copy only Python dependency metadata, create an isolated virtual environment, and install SDK
1.0.11:

```bash
mkdir -p museum-workshop-app/tests
cp samples/python/museum-exhibit-studio/pyproject.toml museum-workshop-app/
cp samples/python/museum-exhibit-studio/requirements.txt museum-workshop-app/
python3 -m venv museum-workshop-app/.venv
museum-workshop-app/.venv/bin/python -m pip install -r museum-workshop-app/requirements.txt
```

Pass condition: pip reports `github-copilot-sdk==1.0.11` installed inside
`museum-workshop-app/.venv`.
:::

:::language go
Copy only module metadata and download the locked SDK 1.0.11 dependency:

```bash
mkdir -p museum-workshop-app
cp samples/go/museum-exhibit-studio/go.mod museum-workshop-app/
cp samples/go/museum-exhibit-studio/go.sum museum-workshop-app/
go -C museum-workshop-app mod download
```

Pass condition: `go mod download` exits successfully and no `.go` file exists yet.
:::

:::language rust
Copy only Cargo metadata, create an empty source directory, and fetch locked dependencies:

```bash
mkdir -p museum-workshop-app/src museum-workshop-app/tests
cp samples/rust/museum-exhibit-studio/Cargo.toml museum-workshop-app/
cp samples/rust/museum-exhibit-studio/Cargo.lock museum-workshop-app/
touch museum-workshop-app/src/lib.rs
cargo fetch --manifest-path museum-workshop-app/Cargo.toml --locked
```

Pass condition: Cargo fetches `github-copilot-sdk` 1.0.11 without modifying `Cargo.lock`. Lesson 1
replaces the empty library target with curator code.
:::

:::language java
Copy only Maven metadata, create empty source trees, and resolve SDK 1.0.11 plus test dependencies:

```bash
mkdir -p museum-workshop-app/src/main/java/workshop museum-workshop-app/src/test/java/workshop
cp samples/java/museum-exhibit-studio/pom.xml museum-workshop-app/
mvn -f museum-workshop-app/pom.xml dependency:go-offline
```

Pass condition: Maven ends with `BUILD SUCCESS`.
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
