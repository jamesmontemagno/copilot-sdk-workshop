# Preflight: prepare your machine

> **Untimed preparation**  
> Complete this page before starting the 90-minute workshop.

## What you'll have ready

By the end of preflight, you'll have the repository cloned, the Copilot CLI authenticated, the
starter project built, and Playwright MCP downloaded and ready.

:::language dotnet
## What you need

| Requirement | Why the workshop needs it | Verify |
|---|---|---|
| [.NET 10 SDK](https://learn.microsoft.com/dotnet/core/install/) | Builds and runs the C# console application | `dotnet --version` |
| [Node.js 22 or newer](https://nodejs.org/) | Runs the Playwright MCP server | `node --version` |
| [GitHub Copilot CLI](https://docs.github.com/en/copilot/how-tos/set-up/install-copilot-cli) | Provides the Copilot runtime used by the SDK | `copilot --version` |
| [GitHub Copilot access](https://github.com/features/copilot) | Authorizes Copilot requests | `copilot login` |
| Microsoft Edge (default) or Google Chrome | Lets Playwright inspect the target page | Open the browser once before the workshop |

Your commands should return output in this shape:

```text
$ dotnet --version
10.0.x
$ node --version
v22.x.x
$ copilot --version
GitHub Copilot CLI ...
```
:::

:::language nodejs
## What you need

| Requirement | Why the workshop needs it | Verify |
|---|---|---|
| [Node.js 22.12 or newer](https://nodejs.org/) | Runs the TypeScript workshop app and Playwright MCP | `node --version` |
| [npm](https://docs.npmjs.com/downloading-and-installing-node-js-and-npm) | Installs `@github/copilot-sdk` and build tools | `npm --version` |
| [GitHub Copilot CLI](https://docs.github.com/en/copilot/how-tos/set-up/install-copilot-cli) | Provides the Copilot runtime used by the SDK | `copilot --version` |
| [GitHub Copilot access](https://github.com/features/copilot) | Authorizes Copilot requests | `copilot login` |
| Microsoft Edge (default) or Google Chrome | Lets Playwright inspect the target page | Open the browser once before the workshop |

Your commands should return output in this shape:

```text
$ node --version
v22.12.x
$ npm --version
10.x.x
$ copilot --version
GitHub Copilot CLI ...
```

See the official
[Node.js SDK installation guide](https://github.com/github/copilot-sdk/tree/main/nodejs).
:::

:::language python
## What you need

| Requirement | Why the workshop needs it | Verify |
|---|---|---|
| [Python 3.11 or newer](https://www.python.org/downloads/) | Runs the async workshop application | `python --version` |
| [pip](https://pip.pypa.io/en/stable/installation/) | Installs the pinned `github-copilot-sdk` wheel | `python -m pip --version` |
| [Node.js 22 or newer](https://nodejs.org/) | Runs the Playwright MCP server | `node --version` |
| [GitHub Copilot CLI](https://docs.github.com/en/copilot/how-tos/set-up/install-copilot-cli) | Optional local runtime override via `COPILOT_CLI_PATH` | `copilot --version` |
| [GitHub Copilot access](https://github.com/features/copilot) | Authorizes Copilot requests | `copilot login` |
| Microsoft Edge (default) or Google Chrome | Lets Playwright inspect the target page | Open the browser once before the workshop |

Your commands should return output in this shape:

```text
$ python --version
Python 3.11.x
$ node --version
v22.x.x
$ copilot --version
GitHub Copilot CLI ...
```

The Python SDK can download a pinned runtime on first use. See the official
[Python SDK installation guide](https://github.com/github/copilot-sdk/tree/main/python).
:::

:::language go
## What you need

| Requirement | Why the workshop needs it | Verify |
|---|---|---|
| [Go 1.24 or newer](https://go.dev/dl/) | Builds and runs the Go workshop module | `go version` |
| [Node.js 22 or newer](https://nodejs.org/) | Runs the Playwright MCP server | `node --version` |
| [GitHub Copilot CLI](https://docs.github.com/en/copilot/how-tos/set-up/install-copilot-cli) | Required on `PATH` (or `COPILOT_CLI_PATH`) for the SDK | `copilot --version` |
| [GitHub Copilot access](https://github.com/features/copilot) | Authorizes Copilot requests | `copilot login` |
| Microsoft Edge (default) or Google Chrome | Lets Playwright inspect the target page | Open the browser once before the workshop |

Your commands should return output in this shape:

```text
$ go version
go version go1.24.x ...
$ node --version
v22.x.x
$ copilot --version
GitHub Copilot CLI ...
```

See the official
[Go SDK installation guide](https://github.com/github/copilot-sdk/tree/main/go).
:::

:::language rust
## What you need

| Requirement | Why the workshop needs it | Verify |
|---|---|---|
| [Rust 1.94 or newer](https://rustup.rs/) | Builds the async Rust workshop crate | `rustc --version` |
| [Cargo](https://doc.rust-lang.org/cargo/getting-started/installation.html) | Resolves locked dependencies and runs the app | `cargo --version` |
| [Node.js 22 or newer](https://nodejs.org/) | Runs the Playwright MCP server | `node --version` |
| [GitHub Copilot CLI](https://docs.github.com/en/copilot/how-tos/set-up/install-copilot-cli) | Runtime used when not relying solely on a bundled binary | `copilot --version` |
| [GitHub Copilot access](https://github.com/features/copilot) | Authorizes Copilot requests | `copilot login` |
| Microsoft Edge (default) or Google Chrome | Lets Playwright inspect the target page | Open the browser once before the workshop |

Your commands should return output in this shape:

```text
$ rustc --version
rustc 1.94.x
$ cargo --version
cargo 1.94.x
$ node --version
v22.x.x
$ copilot --version
GitHub Copilot CLI ...
```

See the official
[Rust SDK installation guide](https://github.com/github/copilot-sdk/tree/main/rust).
:::

:::language java
## What you need

| Requirement | Why the workshop needs it | Verify |
|---|---|---|
| [Java 17 or newer](https://adoptium.net/) (JDK) | Compiles and runs the Maven workshop app | `java -version` |
| [Apache Maven 3.9+](https://maven.apache.org/install.html) | Builds the project and launches `exec:java` | `mvn -version` |
| [Node.js 22 or newer](https://nodejs.org/) | Runs the Playwright MCP server | `node --version` |
| [GitHub Copilot CLI](https://docs.github.com/en/copilot/how-tos/set-up/install-copilot-cli) | Required on `PATH` for the Java SDK runtime | `copilot --version` |
| [GitHub Copilot access](https://github.com/features/copilot) | Authorizes Copilot requests | `copilot login` |
| Microsoft Edge (default) or Google Chrome | Lets Playwright inspect the target page | Open the browser once before the workshop |

Your commands should return output in this shape:

```text
$ java -version
openjdk version "17.x.x" ...
$ mvn -version
Apache Maven 3.9.x
$ node --version
v22.x.x
$ copilot --version
GitHub Copilot CLI ...
```

Use Maven for this track. Do not substitute JBang or Gradle. See the official
[Java SDK installation guide](https://github.com/github/copilot-sdk/tree/main/java).
:::

## 1. Clone the repository

```bash
git clone https://github.com/jamesmontemagno/copilot-sdk-workshop.git
cd copilot-sdk-workshop
code .
```

If `code` is not on your path, use your editor's **Open Folder** command instead.

## 2. Authenticate Copilot

Install the CLI with the method from the
[official setup guide](https://docs.github.com/en/copilot/how-tos/set-up/install-copilot-cli), then run:

```bash
copilot login
```

Finish the browser flow so later SDK calls can reach GitHub Copilot.

## 3. Warm up Playwright MCP

Run this once to download the pinned package and print its options without starting a server:

```bash
npx -y @playwright/mcp@0.0.78 --help
```

The package version is pinned so everyone sees the same tool names and behavior. The code uses
Microsoft Edge with `--browser=msedge`. If you prepared Google Chrome instead, use
`--browser=chrome` when the argument appears in Step 4.

:::language dotnet
## 4. Copy and build the starter

If `dotnet build` cannot find the Copilot CLI later, set its path for the current terminal:

<div class="workshop-tabs" data-tabs>
  <div role="tablist" aria-label="Set the Copilot CLI path">
    <button type="button" role="tab" aria-selected="true" data-tab="cli-windows">Windows</button>
    <button type="button" role="tab" aria-selected="false" data-tab="cli-unix">macOS or Linux</button>
  </div>
  <div role="tabpanel" data-panel="cli-windows">
    <pre><code class="language-powershell">$env:COPILOT_CLI_BINARY_PATH = (Get-Command copilot).Source</code></pre>
  </div>
  <div role="tabpanel" data-panel="cli-unix" hidden>
    <pre><code class="language-bash">export COPILOT_CLI_BINARY_PATH="$(command -v copilot)"</code></pre>
  </div>
</div>

Copy the starter and build it:

<div class="workshop-tabs" data-tabs>
  <div role="tablist" aria-label="Copy the workshop starter">
    <button type="button" role="tab" aria-selected="true" data-tab="copy-windows">Windows</button>
    <button type="button" role="tab" aria-selected="false" data-tab="copy-unix">macOS or Linux</button>
  </div>
  <div role="tabpanel" data-panel="copy-windows">
    <pre><code class="language-powershell">Copy-Item -Recurse start-accessibility/dotnet workshop-app
dotnet build workshop-app</code></pre>
  </div>
  <div role="tabpanel" data-panel="copy-unix" hidden>
    <pre><code class="language-bash">cp -R start-accessibility/dotnet workshop-app
dotnet build workshop-app</code></pre>
  </div>
</div>

A successful build ends with:

```text
Build succeeded.
    0 Warning(s)
    0 Error(s)
```

Open the controlled target page once to make sure you can reach it:

```text
{{TARGET_APP_URL}}
```

<details>
<summary>Troubleshooting preflight</summary>

| Symptom | Fix |
|---|---|
| `copilot` is not recognized | Restart the terminal after installation, or set `COPILOT_CLI_BINARY_PATH` with the command above. |
| Copilot asks you to authenticate | Run `copilot login`, finish the browser flow, then retry. |
| NuGet restore cannot reach the package source | Check proxy or package-source settings, then run `dotnet restore workshop-app`. |
| `npx` is not recognized | Install Node.js 22 or newer and restart the terminal. |
| The browser cannot start later | Install Edge or Chrome, or follow the [Playwright MCP browser configuration](https://github.com/microsoft/playwright-mcp#configuration). |

</details>

> **Start Step 1 when:** `dotnet build workshop-app` succeeds, `copilot login` is complete, and the
> target page opens.
:::

:::language nodejs
## 4. Copy and build the starter

If the SDK cannot find the Copilot CLI later, point it at your install for the current terminal:

<div class="workshop-tabs" data-tabs>
  <div role="tablist" aria-label="Set the Copilot CLI path">
    <button type="button" role="tab" aria-selected="true" data-tab="cli-windows">Windows</button>
    <button type="button" role="tab" aria-selected="false" data-tab="cli-unix">macOS or Linux</button>
  </div>
  <div role="tabpanel" data-panel="cli-windows">
    <pre><code class="language-powershell">$env:COPILOT_CLI_PATH = (Get-Command copilot).Source</code></pre>
  </div>
  <div role="tabpanel" data-panel="cli-unix" hidden>
    <pre><code class="language-bash">export COPILOT_CLI_PATH="$(command -v copilot)"</code></pre>
  </div>
</div>

Copy the starter, install dependencies, and type-check:

<div class="workshop-tabs" data-tabs>
  <div role="tablist" aria-label="Copy the workshop starter">
    <button type="button" role="tab" aria-selected="true" data-tab="copy-windows">Windows</button>
    <button type="button" role="tab" aria-selected="false" data-tab="copy-unix">macOS or Linux</button>
  </div>
  <div role="tabpanel" data-panel="copy-windows">
    <pre><code class="language-powershell">Copy-Item -Recurse start-accessibility/nodejs workshop-app
npm --prefix workshop-app install
npm --prefix workshop-app run build</code></pre>
  </div>
  <div role="tabpanel" data-panel="copy-unix" hidden>
    <pre><code class="language-bash">cp -R start-accessibility/nodejs workshop-app
npm --prefix workshop-app install
npm --prefix workshop-app run build</code></pre>
  </div>
</div>

A successful type-check ends with no TypeScript errors (empty output from `tsc --noEmit`). The
`package.json` start script is `tsx src/index.ts`.

Open the controlled target page once to make sure you can reach it:

```text
{{TARGET_APP_URL}}
```

<details>
<summary>Troubleshooting preflight</summary>

| Symptom | Fix |
|---|---|
| `node` or `npm` is not recognized | Install Node.js 22.12 or newer and restart the terminal. |
| Engine warning about Node version | Upgrade to Node.js 22.12+; the starter declares `"node": ">=22.12.0"`. |
| `npm install` fails on the lockfile | Stay in the copied `workshop-app` directory and keep `package-lock.json`; do not delete it. |
| `copilot` is not recognized | Restart the terminal after installation, or set `COPILOT_CLI_PATH` with the command above. |
| Copilot asks you to authenticate | Run `copilot login`, finish the browser flow, then retry. |
| `npx` cannot download Playwright MCP | Check network access, then rerun the warm-up command from section 3. |
| The browser cannot start later | Install Edge or Chrome, or follow the [Playwright MCP browser configuration](https://github.com/microsoft/playwright-mcp#configuration). |

</details>

> **Start Step 1 when:** `npm --prefix workshop-app run build` succeeds, `copilot login` is complete,
> and the target page opens.
:::

:::language python
## 4. Copy and build the starter

Optional: force the SDK to use your installed CLI instead of downloading a runtime:

<div class="workshop-tabs" data-tabs>
  <div role="tablist" aria-label="Set the Copilot CLI path">
    <button type="button" role="tab" aria-selected="true" data-tab="cli-windows">Windows</button>
    <button type="button" role="tab" aria-selected="false" data-tab="cli-unix">macOS or Linux</button>
  </div>
  <div role="tabpanel" data-panel="cli-windows">
    <pre><code class="language-powershell">$env:COPILOT_CLI_PATH = (Get-Command copilot).Source</code></pre>
  </div>
  <div role="tabpanel" data-panel="cli-unix" hidden>
    <pre><code class="language-bash">export COPILOT_CLI_PATH="$(command -v copilot)"</code></pre>
  </div>
</div>

Copy the starter, create a virtual environment, install pinned requirements, and compile-check:

<div class="workshop-tabs" data-tabs>
  <div role="tablist" aria-label="Copy the workshop starter">
    <button type="button" role="tab" aria-selected="true" data-tab="copy-windows">Windows</button>
    <button type="button" role="tab" aria-selected="false" data-tab="copy-unix">macOS or Linux</button>
  </div>
  <div role="tabpanel" data-panel="copy-windows">
    <pre><code class="language-powershell">Copy-Item -Recurse start-accessibility/python workshop-app
python -m venv workshop-app/.venv
workshop-app\.venv\Scripts\Activate.ps1
python -m pip install -r workshop-app/requirements.txt
python -m py_compile workshop-app/main.py workshop-app/workshop.py workshop-app/report.py workshop-app/accessibility_rule_catalog.py</code></pre>
  </div>
  <div role="tabpanel" data-panel="copy-unix" hidden>
    <pre><code class="language-bash">cp -R start-accessibility/python workshop-app
python3 -m venv workshop-app/.venv
source workshop-app/.venv/bin/activate
python -m pip install -r workshop-app/requirements.txt
python -m py_compile workshop-app/main.py workshop-app/workshop.py workshop-app/report.py workshop-app/accessibility_rule_catalog.py</code></pre>
  </div>
</div>

A successful install prints the resolved packages, including `github-copilot-sdk==...`. A successful
compile check prints no output. Keep the virtual environment activated for later steps.

Optionally pre-download the runtime now so the first Step 1 run is faster:

```bash
python -m copilot download-runtime
```

Open the controlled target page once to make sure you can reach it:

```text
{{TARGET_APP_URL}}
```

<details>
<summary>Troubleshooting preflight</summary>

| Symptom | Fix |
|---|---|
| `python` points at Python 2 or is missing | Use Python 3.11+ (`python3` on macOS/Linux) and recreate the venv. |
| `pip install` cannot reach PyPI | Check proxy settings, then rerun `python -m pip install -r workshop-app/requirements.txt`. |
| Wrong package versions | Install only from the pinned `requirements.txt`; do not loosen `==` pins. |
| Runtime download fails later | Run `python -m copilot download-runtime`, or set `COPILOT_CLI_PATH` to a working CLI. |
| Copilot asks you to authenticate | Run `copilot login`, finish the browser flow, then retry. |
| `npx` is not recognized | Install Node.js 22 or newer and restart the terminal. |
| The browser cannot start later | Install Edge or Chrome, or follow the [Playwright MCP browser configuration](https://github.com/microsoft/playwright-mcp#configuration). |

</details>

> **Start Step 1 when:** the pinned requirements install, `py_compile` succeeds, `copilot login` is
> complete, and the target page opens.
:::

:::language go
## 4. Copy and build the starter

The Go SDK expects the Copilot CLI on `PATH`, or via `COPILOT_CLI_PATH`:

<div class="workshop-tabs" data-tabs>
  <div role="tablist" aria-label="Set the Copilot CLI path">
    <button type="button" role="tab" aria-selected="true" data-tab="cli-windows">Windows</button>
    <button type="button" role="tab" aria-selected="false" data-tab="cli-unix">macOS or Linux</button>
  </div>
  <div role="tabpanel" data-panel="cli-windows">
    <pre><code class="language-powershell">$env:COPILOT_CLI_PATH = (Get-Command copilot).Source</code></pre>
  </div>
  <div role="tabpanel" data-panel="cli-unix" hidden>
    <pre><code class="language-bash">export COPILOT_CLI_PATH="$(command -v copilot)"</code></pre>
  </div>
</div>

Copy the starter and build with the lock enforced:

<div class="workshop-tabs" data-tabs>
  <div role="tablist" aria-label="Copy the workshop starter">
    <button type="button" role="tab" aria-selected="true" data-tab="copy-windows">Windows</button>
    <button type="button" role="tab" aria-selected="false" data-tab="copy-unix">macOS or Linux</button>
  </div>
  <div role="tabpanel" data-panel="copy-windows">
    <pre><code class="language-powershell">Copy-Item -Recurse start-accessibility/go workshop-app
go -C workshop-app build -mod=readonly ./...</code></pre>
  </div>
  <div role="tabpanel" data-panel="copy-unix" hidden>
    <pre><code class="language-bash">cp -R start-accessibility/go workshop-app
go -C workshop-app build -mod=readonly ./...</code></pre>
  </div>
</div>

A successful build prints no errors and produces a binary in `workshop-app`. Keep `go.sum` intact so
module resolution stays deterministic.

Open the controlled target page once to make sure you can reach it:

```text
{{TARGET_APP_URL}}
```

<details>
<summary>Troubleshooting preflight</summary>

| Symptom | Fix |
|---|---|
| `go: go.mod requires go >= 1.24` | Install Go 1.24 or newer and reopen the terminal. |
| `missing go.sum entry` | Restore the committed `go.sum`; build with `-mod=readonly` instead of rewriting the lock. |
| Module download blocked | Configure `GOPROXY`/proxy access, then retry the build from `workshop-app`. |
| `copilot` is not recognized | Install the CLI, restart the terminal, or set `COPILOT_CLI_PATH`. |
| Copilot asks you to authenticate | Run `copilot login`, finish the browser flow, then retry. |
| `npx` is not recognized | Install Node.js 22 or newer and restart the terminal. |
| The browser cannot start later | Install Edge or Chrome, or follow the [Playwright MCP browser configuration](https://github.com/microsoft/playwright-mcp#configuration). |

</details>

> **Start Step 1 when:** `go -C workshop-app build -mod=readonly ./...` succeeds, `copilot login` is
> complete, and the target page opens.

Compare with
[`finished/go/hello-copilot-sdk`](https://github.com/jamesmontemagno/copilot-sdk-workshop/tree/main/finished/go/hello-copilot-sdk)
if you want a later reference point after Step 1.
:::

:::language rust
## 4. Copy and build the starter

If runtime startup cannot resolve the CLI later, set `COPILOT_CLI_PATH`:

<div class="workshop-tabs" data-tabs>
  <div role="tablist" aria-label="Set the Copilot CLI path">
    <button type="button" role="tab" aria-selected="true" data-tab="cli-windows">Windows</button>
    <button type="button" role="tab" aria-selected="false" data-tab="cli-unix">macOS or Linux</button>
  </div>
  <div role="tabpanel" data-panel="cli-windows">
    <pre><code class="language-powershell">$env:COPILOT_CLI_PATH = (Get-Command copilot).Source</code></pre>
  </div>
  <div role="tabpanel" data-panel="cli-unix" hidden>
    <pre><code class="language-bash">export COPILOT_CLI_PATH="$(command -v copilot)"</code></pre>
  </div>
</div>

Copy the starter and check it against the lockfile:

<div class="workshop-tabs" data-tabs>
  <div role="tablist" aria-label="Copy the workshop starter">
    <button type="button" role="tab" aria-selected="true" data-tab="copy-windows">Windows</button>
    <button type="button" role="tab" aria-selected="false" data-tab="copy-unix">macOS or Linux</button>
  </div>
  <div role="tabpanel" data-panel="copy-windows">
    <pre><code class="language-powershell">Copy-Item -Recurse start-accessibility/rust workshop-app
cargo check --manifest-path workshop-app/Cargo.toml --locked</code></pre>
  </div>
  <div role="tabpanel" data-panel="copy-unix" hidden>
    <pre><code class="language-bash">cp -R start-accessibility/rust workshop-app
cargo check --manifest-path workshop-app/Cargo.toml --locked</code></pre>
  </div>
</div>

A successful check ends with a `Finished` line and no errors. Keep `Cargo.lock` committed so the
crate graph stays pinned.

Open the controlled target page once to make sure you can reach it:

```text
{{TARGET_APP_URL}}
```

<details>
<summary>Troubleshooting preflight</summary>

| Symptom | Fix |
|---|---|
| `rustc 1.xx is too old` | Install Rust 1.94+ with `rustup update` and reopen the terminal. |
| Lockfile mismatch with `--locked` | Keep the starter `Cargo.lock`; do not run unconstrained `cargo update`. |
| Crate download blocked | Check network/proxy access to crates.io, then retry `cargo check`. |
| Runtime cannot start later | Install and authenticate `copilot`, or set `COPILOT_CLI_PATH`. |
| Copilot asks you to authenticate | Run `copilot login`, finish the browser flow, then retry. |
| `npx` is not recognized | Install Node.js 22 or newer and restart the terminal. |
| The browser cannot start later | Install Edge or Chrome, or follow the [Playwright MCP browser configuration](https://github.com/microsoft/playwright-mcp#configuration). |

</details>

> **Start Step 1 when:** `cargo check --manifest-path workshop-app/Cargo.toml --locked` succeeds,
> `copilot login` is complete, and the target page opens.

Compare with
[`finished/rust/hello-copilot-sdk`](https://github.com/jamesmontemagno/copilot-sdk-workshop/tree/main/finished/rust/hello-copilot-sdk)
if you want a later reference point after Step 1.
:::

:::language java
## 4. Copy and build the starter

The Java SDK expects the Copilot CLI on `PATH` when the application starts. Confirm it before
building:

```bash
copilot --version
```

Copy the starter and compile with Maven:

<div class="workshop-tabs" data-tabs>
  <div role="tablist" aria-label="Copy the workshop starter">
    <button type="button" role="tab" aria-selected="true" data-tab="copy-windows">Windows</button>
    <button type="button" role="tab" aria-selected="false" data-tab="copy-unix">macOS or Linux</button>
  </div>
  <div role="tabpanel" data-panel="copy-windows">
    <pre><code class="language-powershell">Copy-Item -Recurse start-accessibility/java workshop-app
mvn -f workshop-app/pom.xml compile</code></pre>
  </div>
  <div role="tabpanel" data-panel="copy-unix" hidden>
    <pre><code class="language-bash">cp -R start-accessibility/java workshop-app
mvn -f workshop-app/pom.xml compile</code></pre>
  </div>
</div>

A successful compile ends with:

```text
[INFO] BUILD SUCCESS
```

The `pom.xml` already configures `exec-maven-plugin` with
`mainClass` `workshop.AccessibilityReport`. Stay on Maven for this track.

Open the controlled target page once to make sure you can reach it:

```text
{{TARGET_APP_URL}}
```

<details>
<summary>Troubleshooting preflight</summary>

| Symptom | Fix |
|---|---|
| `java` or `mvn` is not recognized | Install JDK 17+ and Maven, then restart the terminal. |
| Compiler release errors | Confirm `java -version` reports 17 or newer; the POM sets `maven.compiler.release` to 17. |
| Dependency download fails | Check Maven Central / proxy settings, then rerun `mvn -f workshop-app/pom.xml compile`. |
| Tempted to switch tools | Do not replace Maven with JBang or Gradle for this workshop. |
| `copilot` is not recognized | Install the CLI, restart the terminal, and verify `copilot --version`. |
| Copilot asks you to authenticate | Run `copilot login`, finish the browser flow, then retry. |
| `npx` is not recognized | Install Node.js 22 or newer and restart the terminal. |
| The browser cannot start later | Install Edge or Chrome, or follow the [Playwright MCP browser configuration](https://github.com/microsoft/playwright-mcp#configuration). |

</details>

> **Start Step 1 when:** `mvn -f workshop-app/pom.xml compile` prints `BUILD SUCCESS`,
> `copilot login` is complete, and the target page opens.

Compare with
[`finished/java/hello-copilot-sdk`](https://github.com/jamesmontemagno/copilot-sdk-workshop/tree/main/finished/java/hello-copilot-sdk)
if you want a later reference point after Step 1.
:::

Continue to [Step 1: Create your first Copilot session](01-first-session.md).
