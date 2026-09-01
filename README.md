# Copilot SDK Workshops

Choose one of two hands-on GitHub Copilot SDK workshops in .NET, Node.js/TypeScript, Python, Go,
Rust, or Maven Java:

- **Accessibility Reviewer:** build an SDLC developer tool that inspects a web page, consults
  application-owned WCAG guidance, and produces an evidence-based report.
- **Museum Exhibit Studio:** build a non-SDLC curator that transforms approved facts into
  visitor-ready exhibit copy behind deterministic application boundaries.

Across the workshops, you'll:

1. Create a Copilot client and conversation session.
2. Separate durable agent policy from task-specific data.
3. Choose between local tools, MCP tools, and a deliberately tool-free session.
4. Enforce capability, input, timeout, validation, and lifecycle boundaries in application code.
5. Explain what the model can infer and what the application must prove.

Plan on about 90 minutes for Accessibility Reviewer or 105 minutes for Museum Exhibit Studio.
Machine setup happens separately in an untimed preflight for each workshop.

## Start the workshop

Open the GitHub Pages URL produced by the repository's **Deploy to GitHub Pages** workflow. Choose a
workshop outcome, choose a language, then start the selected workshop. The site derives its Pages
base URL at runtime, so there is no hardcoded organization or user Pages hostname.

To preview the site from a clone:

```bash
git clone https://github.com/jamesmontemagno/copilot-sdk-workshop.git
cd copilot-sdk-workshop
python3 -m http.server 8000
```

Open <http://localhost:8000/docs/>. Do not open `step.html` with a `file://` URL; browsers block
the Markdown requests used by the lesson viewer.

## Prerequisites

- [.NET 10 SDK](https://learn.microsoft.com/dotnet/core/install/)
- [Node.js 22 or newer](https://nodejs.org/)
- [Python 3.11 or newer](https://www.python.org/downloads/)
- [Go 1.24 or newer](https://go.dev/dl/)
- [Rust 1.94 or newer](https://rustup.rs/)
- [Java 17 or newer](https://adoptium.net/) and [Maven](https://maven.apache.org/install.html)
- [GitHub Copilot CLI](https://docs.github.com/en/copilot/how-tos/set-up/install-copilot-cli)
- GitHub Copilot subscription or trial
- Microsoft Edge (the workshop default) or Google Chrome

Preflight walks through installation checks, authentication, OS-specific commands, expected
output, and troubleshooting.

## Repository layout

```text
copilot-sdk-workshop/
|-- docs/                         GitHub Pages site and controlled target page
|-- workshop/                     Two complete workshop tracks and optional extensions
|-- start/dotnet/                 .NET learner starter with WCAG data and permission helper
|-- checkpoints/dotnet/           .NET compiling state after each build step
|-- samples/dotnet/
|   |-- hello-copilot-sdk/        Completed local-tool example in every language
|   |-- accessibility-report/     Completed .NET local + MCP reporter
|   `-- museum-exhibit-studio/    Tool-free, grounded museum curator sample
|-- start/nodejs/                 Node.js/TypeScript learner starter
|-- checkpoints/nodejs/           Node.js/TypeScript checkpoint projects
|-- samples/nodejs/               Completed TypeScript examples
|-- start/python/                 Python 3.11+ learner starter
|-- checkpoints/python/           Python checkpoint projects
|-- samples/python/               Completed Python examples
|-- start/go/                     Go 1.24+ learner starter
|-- checkpoints/go/               Go checkpoint projects
|-- samples/go/                   Completed Go examples
|-- start/rust/                   Rust 1.94+ learner starter
|-- checkpoints/rust/             Rust checkpoint projects
|-- samples/rust/                 Completed Rust examples
|-- start/java/                   Maven Java 17+ learner starter
|-- checkpoints/java/             Maven Java checkpoint projects
|-- samples/java/                 Completed Maven Java examples
|-- src/BlazorApp/                Source counterpart of the deployed target
|-- scripts/                      Deterministic content and build validation
`-- .github/workflows/            Validation and Pages deployment
```

## Validate a change

```bash
bash scripts/validate-workshop.sh
```

The command checks lesson structure, internal links, site behavior hooks, and checkpoint coverage.
It then runs browser-independent language-selection tests and restores, builds, or syntax-checks every
starter, every checkpoint, both samples, and the Blazor target without authenticating Copilot, launching
a browser, or sending a prompt.

Pass a language ID to run one smoke-build target:

```bash
bash scripts/validate-workshop.sh nodejs
```

Pull requests run content validation and all six language smoke builds as separate GitHub Actions
jobs, so a failure identifies the affected SDK track.

## Museum Exhibit Studio workshop

Museum Exhibit Studio is available in every workshop language under
`samples/<language>/museum-exhibit-studio`. Each implementation demonstrates a complete custom
system message, a task-specific approved fact list, an empty tool allowlist, and deterministic
output checks in a non-software-engineering agent harness.

The learner-facing track begins at
[`workshop/museum-00-preflight.md`](workshop/museum-00-preflight.md), then continues through seven
required steps ending with Wikipedia MCP.

Rust checks share one Cargo target directory across all workshop projects, avoiding repeated SDK
dependency compilation.

## Deployment

After validation passes, push to `main`. The
[Pages workflow](.github/workflows/deploy.yml) publishes `docs/` plus the Markdown lessons in
`workshop/`. Build and content validation run separately in the validation workflow.

Enable GitHub Pages in repository settings and choose **GitHub Actions** as the source. The
deployment job reports the canonical workshop URL in its environment.

## References

- [GitHub Copilot SDK for .NET](https://github.com/github/copilot-sdk/tree/main/dotnet)
- [GitHub Copilot SDK for Node.js/TypeScript](https://github.com/github/copilot-sdk/tree/main/nodejs)
- [GitHub Copilot SDK for Python](https://github.com/github/copilot-sdk/tree/main/python)
- [GitHub Copilot SDK for Go](https://github.com/github/copilot-sdk/tree/main/go)
- [GitHub Copilot SDK for Rust](https://github.com/github/copilot-sdk/tree/main/rust)
- [GitHub Copilot SDK for Java](https://github.com/github/copilot-sdk/tree/main/java)
- [Copilot SDK cookbook](https://github.com/github/copilot-sdk/tree/main/cookbook)
- [Copilot SDK API and source](https://github.com/github/copilot-sdk)
- [Install the GitHub Copilot CLI](https://docs.github.com/en/copilot/how-tos/set-up/install-copilot-cli)
- [Playwright MCP](https://github.com/microsoft/playwright-mcp)
- [Model Context Protocol](https://modelcontextprotocol.io/)

## License

This workshop is provided as-is for educational purposes.
