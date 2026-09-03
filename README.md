# Copilot SDK Workshops

Choose one of two hands-on GitHub Copilot SDK workshops in .NET, Node.js/TypeScript, Python, Go,
Rust, or Maven Java:

- **Accessibility Reviewer:** build an SDLC developer tool that inspects a web page, consults
  application-owned WCAG guidance, and produces an evidence-based report.
- **Museum Exhibit Studio:** build a non-SDLC curator that transforms educator-approved facts into
  visitor-ready exhibit copy behind deterministic application boundaries.

Across the workshops, you'll:

1. Create a Copilot client and conversation session.
2. Separate durable agent policy from task-specific data.
3. Choose between local tools, MCP tools, and a tightly scoped single-tool allowlist.
4. Enforce capability, input, timeout, validation, and lifecycle boundaries in application code.
5. Explain what the model can infer and what the application must prove.

Plan on about 90 minutes for Accessibility Reviewer or 90 minutes for Museum Exhibit Studio.
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
|-- start-accessibility/          Accessibility Reviewer starters in all six languages
|-- start-museum/                 Museum Exhibit Studio starters in all six languages
|-- finished/dotnet/
|   |-- hello-copilot-sdk/        Completed local-tool example in every language
|   |-- accessibility-report/     Completed .NET local + MCP reporter
|   `-- museum-exhibit-studio/    Grounded museum curator sample, one application-owned tool
|-- finished/nodejs/              Completed TypeScript projects
|-- finished/python/              Completed Python projects
|-- finished/go/                  Completed Go projects
|-- finished/rust/                Completed Rust projects
|-- finished/java/                Completed Maven Java projects
|-- src/BlazorApp/                Source counterpart of the deployed target
|-- scripts/                      Deterministic content and build validation
`-- .github/workflows/            Validation and Pages deployment
```

## Validate a change

```bash
bash scripts/validate-workshop.sh
```

The command checks lesson structure, internal links, site behavior hooks, and project coverage.
It then runs browser-independent language-selection tests and restores, builds, or syntax-checks every
accessibility and museum starter, every finished project, and the Blazor target without authenticating
Copilot, launching a browser, or sending a prompt. The museum projects ship no tests, mocks, or
fixtures, so their targets only restore and build.

Pass a language ID to run one smoke-build target:

```bash
bash scripts/validate-workshop.sh nodejs
```

Pull requests run content validation and all six language smoke builds as separate GitHub Actions
jobs, so a failure identifies the affected SDK track.

## Museum Exhibit Studio workshop

Museum Exhibit Studio starters live under `start-museum/<language>`, with completed references under
`finished/<language>/museum-exhibit-studio`. Each starter ships one pre-built curator helper module
that learners never edit: approved fact sets and their bounds, a streaming printer, deterministic
exhibit validation, the scoped Wikipedia MCP server with its deny-by-default permission handler, the
single-file `exhibit.html` write permission, and small terminal prompts.

Learners work directly in `start-museum/<language>` and grow that one project across the
lessons, running it at every step. They write only the session setup, the curator and research
system messages, the prompt builders, one session runner that owns the lifecycle and guardrails, and
`main`. The finished sample is what a learner ends up with, not a separate reference architecture.

The learner-facing track begins at
[`workshop/museum-00-preflight.md`](workshop/museum-00-preflight.md), then runs through seven core
steps — first session, streaming, curator voice, approved facts, guardrails, structural checks, and
Wikipedia MCP research — plus an optional interactive `exhibit.html` capstone.

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
