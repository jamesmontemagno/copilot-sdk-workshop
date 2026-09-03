---
on:
  workflow_dispatch:
  schedule: daily

permissions:
  contents: read
  issues: read
  pull-requests: read
  copilot-requests: write

engine: copilot
network: defaults

safe-outputs:
  create-issue:
    max: 1
    title-prefix: "[daily workshop validation] "
    deduplicate-by-title: true
  report-failure-as-issue: true
---

# Daily workshop validation

First check for commits during the preceding 26 hours:

```bash
git log --since="26 hours ago" --format="%H %s"
```

If there are no commits, stop without running validation or creating output. Otherwise, review the
changed workshop, site, and track files, then run:

```bash
bash scripts/validate-workshop.sh
```

That command validates the shared six-language registry, strict directives and lesson coverage,
local assets and language propagation tests, both starter tracks, all finished projects, and the
Blazor target. Museum projects are restored and compiled without running application test harnesses.
It uses deterministic noninteractive commands only.
Do not authenticate, send Copilot prompts, launch a browser, or report a failure caused only by
credentials, browser runtime, external services, or an organization package proxy.

If every applicable check passes, stop without creating an issue. If a reproducible repository
defect remains, search existing issues and create at most one factual issue with the command or
static rule, expected and actual result, commit SHA, affected language(s), and likely files.
