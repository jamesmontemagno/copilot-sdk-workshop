from __future__ import annotations

from pathlib import Path
from urllib.parse import urlsplit

from copilot import define_tool
from copilot.rpc import PermissionDecisionApproveOnce, PermissionDecisionReject
from pydantic import BaseModel, Field

from accessibility_rule_catalog import ACCESSIBILITY_RULES

MAX_SNAPSHOT_BYTES = 1_000_000


class LookupParams(BaseModel):
    query: str = Field(description="The accessibility issue or WCAG criterion to look up.")


@define_tool(name="accessibility_rule_lookup", description="Looks up read-only WCAG guidance maintained by this application.", skip_permission=True)
def accessibility_rule_lookup(params: LookupParams) -> dict[str, object]:
    query = params.query.strip().lower()
    rule = next((item for item in ACCESSIBILITY_RULES if item.criterion.lower() in query or item.title.lower() in query or any(keyword in query for keyword in item.keywords)), None)
    if rule is None:
        return {"criterion": "No exact match", "title": "Criterion not found", "when_it_applies": "The issue is not represented in the workshop catalog.", "recommendation": "Verify the evidence and consult the complete WCAG reference."}
    return rule.__dict__


def create_snapshot_reader(working_directory: str):
    output_directory = Path(working_directory, ".playwright-mcp").resolve()
    existing = {path.resolve() for path in output_directory.glob("page-*.yml")} if output_directory.is_dir() else set()

    @define_tool(name="read_latest_accessibility_snapshot", description="Reads the newest Playwright accessibility snapshot created during this run.", skip_permission=True)
    def read_latest_accessibility_snapshot() -> str:
        candidates = [path for path in output_directory.glob("page-*.yml") if path.resolve() not in existing and not path.is_symlink() and path.is_file() and 0 < path.stat().st_size <= MAX_SNAPSHOT_BYTES]
        if not candidates:
            raise FileNotFoundError("No current-run Playwright snapshot is available. Call browser_navigate first.")
        return max(candidates, key=lambda path: path.stat().st_mtime).read_text(encoding="utf-8")

    return read_latest_accessibility_snapshot


def permission_for_target(target: str):
    def handler(request, _invocation):
        if getattr(request, "kind", None) == "mcp" and request.server_name == "playwright" and request.tool_name in {"browser_navigate", "playwright-browser_navigate"} and isinstance(request.args, dict) and isinstance(request.args.get("url"), str) and _same_url(request.args["url"], target):
            return PermissionDecisionApproveOnce()
        return PermissionDecisionReject(feedback="This workshop allows Playwright to navigate only to the exact requested target.")
    return handler


def _same_url(requested: str, allowed: str) -> bool:
    left, right = urlsplit(requested), urlsplit(allowed)
    return (left.scheme.lower(), left.hostname.lower() if left.hostname else "", left.port, left.username, left.password, left.path, left.query, left.fragment) == (right.scheme.lower(), right.hostname.lower() if right.hostname else "", right.port, right.username, right.password, right.path, right.query, right.fragment)


def report_prompt(target: str) -> str:
    return f"""Prepare an evidence-based accessibility review of {target}.
1. Use browser_navigate to open that exact URL.
2. Call read_latest_accessibility_snapshot to inspect its accessibility tree.
3. Identify three to five high-confidence issues supported by the snapshot.
4. Call accessibility_rule_lookup for each issue before recommending a fix.

Return only this structure:
# Accessibility review
## Finding 1: <short name>
- Evidence: <specific element or page structure observed in the browser>
- WCAG criterion: <criterion and title returned by the catalog>
- Recommended remediation: <specific implementation change>
Repeat the finding section as needed.
## Review limits
State that this is a focused review of browser-observable evidence, not a full WCAG conformance audit.
Do not invent evidence, report unsupported statistics, or claim the page is WCAG compliant."""
