#!/usr/bin/env python3

from __future__ import annotations

from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
WORKSHOP = ROOT / "workshop"
DOCS = ROOT / "docs"
LANGUAGES = ("dotnet", "go", "java", "nodejs", "python", "rust")
SDLC_LESSONS = (
    "00-preflight.md",
    "01-first-session.md",
    "02-streaming.md",
    "03-local-tool.md",
    "04-mcp-safety.md",
    "05-combine-tools.md",
    "06-structured-report.md",
    "07-run-explain.md",
    "08-model-selection.md",
    "09-interactive-html-report.md",
)
MUSEUM_LESSONS = (
    "museum-00-preflight.md",
    "museum-01-first-curator-session.md",
    "museum-02-stream-the-curator.md",
    "museum-03-curator-voice.md",
    "museum-04-approved-facts.md",
    "museum-05-guardrails.md",
    "museum-06-prove-the-structure.md",
    "museum-07-wikipedia-research.md",
    "museum-08-interactive-exhibit-page.md",
)
LESSONS = SDLC_LESSONS + MUSEUM_LESSONS
OFFICIAL_SDK_URLS = {
    "dotnet": "https://github.com/github/copilot-sdk/tree/main/dotnet",
    "nodejs": "https://github.com/github/copilot-sdk/tree/main/nodejs",
    "python": "https://github.com/github/copilot-sdk/tree/main/python",
    "go": "https://github.com/github/copilot-sdk/tree/main/go",
    "rust": "https://github.com/github/copilot-sdk/tree/main/rust",
    "java": "https://github.com/github/copilot-sdk/tree/main/java",
}
MANIFESTS = {
    "dotnet": "*.csproj",
    "nodejs": "package.json",
    "python": "requirements.txt",
    "go": "go.mod",
    "rust": "Cargo.toml",
    "java": "pom.xml",
}
ENTRYPOINTS = {
    "dotnet": "Program.cs",
    "nodejs": "src/index.ts",
    "python": "main.py",
    "go": "main.go",
    "rust": "src/main.rs",
    "java": "src/main/java/workshop/AccessibilityReport.java",
}
LESSON_TRACK_MARKERS = {
    "dotnet": (
        "Program.cs",
        "Helpers/",
        "dotnet run",
        "```csharp",
        "finished/dotnet/",
    ),
    "nodejs": (
        "src/index.ts",
        "src/workshop.ts",
        "npm start",
        "```typescript",
        "finished/nodejs/",
    ),
    "python": (
        "main.py",
        "workshop.py",
        "python main.py",
        "```python",
        "finished/python/",
    ),
    "go": (
        "main.go",
        "go run .",
        "```go",
        "finished/go/",
    ),
    "rust": (
        "src/main.rs",
        "cargo run",
        "```rust",
        "finished/rust/",
    ),
    "java": (
        "src/main/java/",
        "mvn compile",
        "```java",
        "finished/java/",
    ),
}
STEP_3_TRACK_MARKERS = {
    "dotnet": ("AccessibilityRuleCatalog.cs", "CopilotTool.DefineTool", "dotnet run"),
    "nodejs": ("src/workshop.ts", 'defineTool("accessibility_rule_lookup"', "npm start"),
    "python": ("workshop.py", '@define_tool(', "python main.py"),
    "go": ("main.go", "copilot.DefineTool(", "go run ."),
    "rust": ("src/main.rs", 'Tool::new("accessibility_rule_lookup")', "cargo run"),
    "java": ("AccessibilityReport.java", "ToolDefinition.from(", "mvn compile exec:java"),
}
# Every command runs from inside the starter directory the learner already sits in.
# No lesson may reintroduce a copied sibling project.
RUN_COMMAND_MARKERS = {
    "dotnet": "dotnet run",
    "nodejs": "npm start",
    "python": "python main.py",
    "go": "go run .",
    "rust": "cargo run",
    "java": "mvn compile exec:java",
}
STEP_9_RUN_COMMAND_MARKERS = {
    "dotnet": "dotnet run",
    "nodejs": "npm start",
    "python": "python main.py",
    "go": "go run .",
    "rust": "cargo run --",
    "java": "mvn compile exec:java",
}
MUSEUM_COMMAND_MARKERS = {
    "dotnet": (
        "dotnet run",
    ),
    "nodejs": (
        "npm start",
    ),
    "python": (
        ".venv/bin/python main.py",
    ),
    "go": (
        "go run .",
    ),
    "rust": (
        "cargo run",
    ),
    "java": (
        "mvn compile exec:java",
    ),
}
MUSEUM_ENTRYPOINTS = {
    "dotnet": "Program.cs",
    "nodejs": "src/index.ts",
    "python": "main.py",
    "go": "main.go",
    "rust": "src/main.rs",
    "java": "src/main/java/workshop/MuseumExhibitStudio.java",
}
# The learner grows one project in place. Nothing may scaffold or copy a second one.
SECOND_PROJECT_MARKERS = (
    "cp -R start-",
    "Copy-Item -Recurse start-",
    "dotnet new console",
    "cargo new ",
    "go mod init",
    "npm init ",
    "mvn archetype:generate",
)
IN_PLACE_FORBIDDEN_MARKERS = (
    "workshop-app",
    "museum-workshop-app",
)
MUSEUM_FORBIDDEN_LESSON_MARKERS = (
    "museum-07-guides",
    "dotnet test",
    "npm test",
    "go test",
    "cargo test",
    "mvn test",
    "python -m unittest",
    "unittest",
    "mock-wikipedia",
    "tests/",
    "src/test/java",
    "checkpoints/",
    "samples/",
    "ICuratorClient",
    "ICuratorSession",
    "CopilotCuratorClient",
    "createCopilotCuratorClient",
    "MuseumExhibitService",
    "CuratorRuntime",
    "ExhibitValidator",
    "selectApprovedFacts",
    "parseResearchResult",
    "ProposedAddition",
)
PROCEDURE_MARKERS = {
    "01-first-session.md": {
        "dotnet": "SendAndWaitAsync",
        "nodejs": "sendAndWait",
        "python": "create_session",
        "go": "copilot.NewClient",
        "rust": "Client::start",
        "java": "new CopilotClient",
    },
    "02-streaming.md": {
        "dotnet": "ResponseStreamer.SendAndPrintAsync",
        "nodejs": "streamResponse",
        "python": "AssistantMessageDeltaData",
        "go": "session.On",
        "rust": "session.subscribe()",
        "java": "setStreaming(true)",
    },
    "03-local-tool.md": {
        language: markers[1] for language, markers in STEP_3_TRACK_MARKERS.items()
    },
    "04-mcp-safety.md": {
        "dotnet": "McpStdioServerConfig",
        "nodejs": "src/index.ts",
        "python": "main.py",
        "go": "MCPStdioServerConfig",
            "rust": 'tools: Some(vec!["browser_navigate"',
            "java": '.setTools(List.of("browser_navigate"))',
    },
    "05-combine-tools.md": {
        "dotnet": "For each issue, call accessibility_rule_lookup",
        "nodejs": "src/index.ts",
        "python": "main.py",
        "go": "AvailableTools",
        "rust": "config.available_tools",
        "java": "setAvailableTools",
    },
    "06-structured-report.md": {
        "dotnet": "Prompts.CreateReportPrompt",
        "nodejs": 'import "./report.js"',
        "python": "from report import main",
        "go": "reportPrompt(target)",
        "rust": "report_prompt(&target)",
        "java": "reportPrompt(target)",
    },
    "08-model-selection.md": {
        "dotnet": "ModelSelector.SelectAsync",
        "nodejs": "client.listModels()",
        "python": "client.list_models()",
        "go": "client.ListModels",
        "rust": "models().list()",
        "java": "SessionConfig.setModel",
    },
    "09-interactive-html-report.md": {
        "dotnet": "builtin:apply_patch",
        "nodejs": "builtin:apply_patch",
        "python": "builtin:apply_patch",
        "go": "builtin:apply_patch",
        "rust": "builtin:apply_patch",
        "java": "builtin:apply_patch",
    },
    "museum-01-first-curator-session.md": {
        "dotnet": "SendAndWaitAsync",
        "nodejs": "sendAndWait",
        "python": "create_session",
        "go": "copilot.NewClient",
        "rust": "Client::start",
        "java": "new CopilotClient",
    },
    "museum-02-stream-the-curator.md": {
        "dotnet": "CuratorStreamer.StreamExhibitAsync",
        "nodejs": "streamExhibit(",
        "python": "stream_exhibit(",
        "go": "StreamExhibit(",
        "rust": "stream_exhibit(",
        "java": "CuratorStreamer.streamExhibit",
    },
    "museum-03-curator-voice.md": {
        "dotnet": "const string SystemMessage",
        "nodejs": "const systemMessage",
        "python": "SYSTEM_MESSAGE =",
        "go": "const systemMessage",
        "rust": "const SYSTEM_MESSAGE",
        "java": "public static final String SYSTEM_MESSAGE",
    },
    "museum-04-approved-facts.md": {
        "dotnet": "BuildExhibitPrompt",
        "nodejs": "buildExhibitPrompt",
        "python": "build_exhibit_prompt",
        "go": "buildExhibitPrompt",
        "rust": "build_exhibit_prompt",
        "java": "buildExhibitPrompt",
    },
    "museum-05-guardrails.md": {
        "dotnet": "static async Task<string> RunSessionAsync",
        "nodejs": "async function runSession",
        "python": "async def run_session",
        "go": "func runSession(",
        "rust": "async fn run_session",
        "java": "private static String runSession",
    },
    "museum-06-prove-the-structure.md": {
        "dotnet": "CuratorValidation.FormatValidation",
        "nodejs": "formatValidation(validateExhibit(",
        "python": "format_validation(validate_exhibit(",
        "go": "FormatValidation(ValidateExhibit(",
        "rust": "format_validation(&validate_exhibit(",
        "java": "CuratorValidation.formatValidation",
    },
    "museum-07-wikipedia-research.md": {
        "dotnet": "CuratorSafety.WikipediaPermissionHandler()",
        "nodejs": "wikipediaPermissionHandler()",
        "python": "wikipedia_permission_handler()",
        "go": "WikipediaPermissionHandler()",
        "rust": "wikipedia_permission_handler()",
        "java": "CuratorSafety.wikipediaPermissionHandler()",
    },
    "museum-08-interactive-exhibit-page.md": {
        "dotnet": "builtin:apply_patch",
        "nodejs": "builtin:apply_patch",
        "python": "builtin:apply_patch",
        "go": "builtin:apply_patch",
        "rust": "builtin:apply_patch",
        "java": "builtin:apply_patch",
    },
}
UNSCOPED_TRACK_MARKERS = (
    "Program.cs",
    "Helpers/",
    "src/index.ts",
    "src/workshop.ts",
    "main.py",
    "workshop.py",
    "main.go",
    "src/main.rs",
    "src/main/java/",
    "```csharp",
    "```typescript",
    "```python",
    "```go",
    "```rust",
    "```java",
    "PingAsync",
    "SendAndWaitAsync",
    "AssistantMessageDeltaEvent",
    "AssistantMessageEvent",
    "SessionIdleEvent",
    "SessionErrorEvent",
    "ToolExecutionStartEvent",
    "ToolExecutionCompleteEvent",
    "ListModelsAsync",
)
errors: list[str] = []


def require(condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


class LocalAssetParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.references: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attribute = "href" if tag in {"a", "link"} else "src" if tag in {"script", "img"} else None
        if attribute:
            value = dict(attrs).get(attribute)
            if value:
                self.references.append(value)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def has_manifest(directory: Path, language: str) -> bool:
    manifest = MANIFESTS[language]
    return bool(list(directory.glob(manifest))) if "*" in manifest else (directory / manifest).exists()


def entrypoint_path(directory: Path, language: str) -> Path:
    if language == "java" and directory.name == "hello-copilot-sdk":
        return Path("src/main/java/workshop/AccessibilityGuidance.java")
    if language == "java" and directory.name == "museum-exhibit-studio":
        return Path("src/main/java/workshop/MuseumExhibitStudio.java")
    if language == "java" and directory.parent.name == "start-museum":
        return Path("src/main/java/workshop/MuseumExhibitStudio.java")
    return Path(ENTRYPOINTS[language])


def project_source(directory: Path) -> str:
    source_suffixes = {
        ".cs", ".ts", ".py", ".go", ".rs", ".java"
    }
    return "\n".join(
        read(path) for path in directory.rglob("*")
        if path.is_file()
        and path.suffix in source_suffixes
        and not set(path.relative_to(directory).parts).intersection(
            {"node_modules", "bin", "obj", "target", "__pycache__"}
        )
    )


def executable_source(directory: Path, language: str) -> str:
    """Read the launched entrypoint and any directly launched report module, not dormant helpers."""
    entrypoint = directory / entrypoint_path(directory, language)
    text = read(entrypoint)
    if language == "nodejs" and re.search(r'import\s+["\']\./report\.js["\']', text):
        text += "\n" + read(directory / "src" / "report.ts") + "\n" + read(directory / "src" / "workshop.ts")
    if language == "python" and re.search(r"from\s+report\s+import\s+main", text):
        text += "\n" + read(directory / "report.py") + "\n" + read(directory / "workshop.py")
    if language == "dotnet" and "Prompts.CreateReportPrompt" in text:
        text += "\n" + read(directory / "Helpers" / "Prompts.cs")
    return text


def contains_any(text: str, markers: tuple[str, ...]) -> bool:
    folded = text.casefold()
    return any(marker.casefold() in folded for marker in markers)


LANGUAGE_APIS = {
    "dotnet": {
        "client": ("new CopilotClient",),
        "session": ("CreateSessionAsync",),
        "send": ("SendAndWaitAsync", "ResponseStreamer.SendAndPrintAsync"),
        "stream": ("Streaming = true",),
        "tool": ("CreateLookupTool",),
    },
    "nodejs": {
        "client": ("new CopilotClient",),
        "session": ("createSession",),
        "send": ("sendAndWait", "streamResponse"),
        "stream": ("streaming: true",),
        "tool": ("accessibilityRuleLookup", "tools: ["),
    },
    "python": {
        "client": ("CopilotClient",),
        "session": ("create_session",),
        "send": ("session.send",),
        "stream": ("streaming=True",),
        "tool": ("accessibility_rule_lookup", "tools=["),
    },
    "go": {
        "client": ("copilot.NewClient",),
        "session": ("CreateSession",),
        "send": ("SendAndWait",),
        "stream": ("Streaming: copilot.Bool(true)",),
        "tool": ('DefineTool("accessibility_rule_lookup"',),
    },
    "rust": {
        "client": ("Client::start",),
        "session": ("create_session",),
        "send": ("send_and_wait", "$session.send("),
        "stream": ("config.streaming = Some(true)",),
        "tool": ('Tool::new("accessibility_rule_lookup")',),
    },
    "java": {
        "client": ("new CopilotClient",),
        "session": ("createSession",),
        "send": ("sendAndWait",),
        "stream": ("setStreaming(true)",),
        "tool": ('ToolDefinition.from(', '"accessibility_rule_lookup"'),
    },
}


def contains_all(text: str, markers: tuple[str, ...]) -> bool:
    folded = text.casefold()
    return all(marker.casefold() in folded for marker in markers)


def runtime_source(directory: Path, language: str, text: str) -> str:
    """Include the directly imported Node response helper for runtime-flow validation."""
    if language == "nodejs":
        if re.search(r'from\s+["\']\./local-tool\.js["\']', text):
            return text + "\n" + read(directory / "src" / "local-tool.ts")
        if re.search(r'from\s+["\']\./workshop\.js["\']', text):
            return text + "\n" + read(directory / "src" / "workshop.ts")
    if language == "dotnet" and "ResponseStreamer.SendAndPrintAsync" in text:
        return text + "\n" + read(directory / "Helpers" / "ResponseStreamer.cs")
    return text


def validate_runtime_flow(language: str, stage: str, text: str, label: Path) -> None:
    """Require a visible response and a completion/error path, not just a send call."""
    streaming = stage != "01-first-session"

    if language == "dotnet":
        markers = (
            ("SendAndWaitAsync", 'Console.WriteLine($"\\nCopilot: {response.Data.Content}")', "await")
            if not streaming
            else ("await ResponseStreamer.SendAndPrintAsync", "AssistantMessageDeltaEvent",
                  "AssistantMessageEvent", "SessionIdleEvent", "SessionErrorEvent", "receivedDelta")
        )
        require(contains_all(text, markers),
                f"{label} does not print a completed Copilot response")
    elif language == "nodejs":
        markers = (
            ("const response = await session.sendAndWait", "console.log(response")
            if not streaming
            else ("await streamResponse(", "session.on(", "process.stdout.write", "session.error", "session.idle")
        )
        require(contains_all(text, markers),
                f"{label} does not print and complete the Copilot response")
    elif language == "python":
        markers = (
            ("AssistantMessageData", "print(content)", "SessionErrorData", "SessionIdleData",
             "await done.wait()", "if error is not None", "done.set()")
            if not streaming
            else ("AssistantMessageDeltaData", "AssistantMessageData", "received_delta = False",
                 "received_delta = True", "not received_delta", "print(delta", "print(content)",
                 "SessionErrorData", "SessionIdleData",
                  "await done.wait()", "if error is not None", "done.set()")
        )
        require(contains_all(text, markers),
               f"{label} does not print streamed output or a final-message fallback before propagating session errors")
        if stage == "05-combine-tools":
            tool_event_markers = (
                "ToolExecutionStartData",
                "[tool:start]",
                "ToolExecutionCompleteData",
                "[tool:done]",
            )
            require(
                contains_all(text, tool_event_markers),
                f"{label} does not print local and MCP tool lifecycle events",
            )
    elif language == "go":
        if streaming:
            event_output = contains_all(text, ("session.On(", "AssistantMessageDeltaData", "AssistantMessageData", "receivedDelta", "fmt.Print"))
            blocking_output = contains_all(text, ("AssistantMessageData", "fmt.Println(message.Content)"))
            require(event_output or blocking_output,
                    f"{label} does not print streamed or final assistant output")
        else:
            require(contains_all(text, ("AssistantMessageData", "fmt.Println(message.Content)")),
                    f"{label} does not print the final assistant response")
        require(contains_all(text, ("SendAndWait",)) and
                ("return err" in text or "if err != nil" in text),
                f"{label} does not wait for or propagate the send result")
    elif language == "rust":
        markers = (
            ("send_and_wait", 'message.data.get("content")', "println!")
            if not streaming
            else ("$session.send(", "session.subscribe", "assistant.message_delta", "assistant.message",
                  "session.error", "session.idle", "tokio::select!", "print!")
        )
        require(contains_all(text, markers),
                f"{label} does not subscribe, print, and await completion or errors")
    elif language == "java":
        markers = (
            ("sendAndWait", "response == null", "response.getData().content()", ".get()")
            if not streaming or label != Path("finished/java/hello-copilot-sdk")
            else ("AssistantMessageDeltaEvent", "AssistantMessageEvent", "receivedDelta",
                  "System.out.print", "sendAndWait", ".get()")
        )
        require(contains_all(text, markers),
                f"{label} does not print streamed output or a final-message fallback before awaiting completion")


LATER_CAPABILITIES = {
    "stream": ("streaming", "Streaming", "setStreaming"),
    "local": ("accessibility_rule_lookup",),
    "mcp": ("mcpServers", "mcp_servers", "MCPServers", "McpStdioServerConfig", "McpServerConfig"),
    "browser": ("browser_navigate", "playwright-browser_navigate"),
    "snapshot": ("read_latest_accessibility_snapshot",),
    "permission": ("permissionForTarget", "permission_for_target", "OnPermissionRequest", "with_permission_handler", "setOnPermissionRequest"),
    "report": ("Review limits", "review limits", "reportPrompt", "report_prompt"),
}

DEFAULT_PERMISSION_HANDLERS = {
    "dotnet": "OnPermissionRequest = PermissionHandler.ApproveAll",
    "nodejs": "onPermissionRequest: approveAll",
    "python": "on_permission_request=PermissionHandler.approve_all",
    "go": "OnPermissionRequest: copilot.PermissionHandler.ApproveAll",
    "rust": "with_permission_handler(permission::approve_all())",
    "java": "setOnPermissionRequest(PermissionHandler.APPROVE_ALL)",
}

PLAYWRIGHT_MCP_PACKAGE = "@playwright/mcp@0.0.78"
PLAYWRIGHT_OUTPUT_DIRECTORY = re.compile(
    r'--output-dir(?:(?!--[a-z]).){0,80}["\']\.playwright-mcp["\']',
    re.DOTALL,
)
PLAYWRIGHT_OUTPUT_MODE = re.compile(
    r'--output-mode(?:(?!--[a-z]).){0,80}["\']file["\']',
    re.DOTALL,
)


def validate_executable_stage(language: str, stage: str, directory: Path) -> str:
    text = executable_source(directory, language)
    apis = LANGUAGE_APIS[language]
    label = directory.relative_to(ROOT)
    if stage == "starter":
        for capability in ("client", "session", "stream", "local", "mcp", "browser", "snapshot", "permission", "report"):
            markers = apis.get(capability, ()) + LATER_CAPABILITIES.get(capability, ())
            require(not contains_any(text, markers),
                    f"{label} starter wires {capability} instead of remaining a scaffold")
        return text

    for capability in ("client", "session", "send"):
        require(contains_any(text, apis[capability]),
                f"{label} executable entrypoint does not create, use, and send through a Copilot session")

    required_capabilities = {
        "01-first-session": (),
        "02-streaming": ("stream",),
        "03-local-tool": ("stream", "local"),
        "04-mcp-safety": ("stream", "local", "mcp", "browser", "snapshot", "permission"),
        "05-combine-tools": ("stream", "local", "mcp", "browser", "snapshot", "permission"),
        "06-structured-report": ("stream", "local", "mcp", "browser", "snapshot", "permission", "report"),
    }[stage]
    for capability in required_capabilities:
        markers = apis.get(capability, ()) + LATER_CAPABILITIES.get(capability, ())
        require(contains_any(text, markers),
                f"{label} executable entrypoint does not wire {capability} for {stage}")

    if stage == "01-first-session" or (
            language == "java" and stage in {"02-streaming", "03-local-tool"}):
        require(DEFAULT_PERMISSION_HANDLERS[language] in text,
                f"{label} does not configure the required baseline permission handler")

    validate_runtime_flow(language, stage, runtime_source(directory, language, text), label)
    if stage == "04-mcp-safety":
        require("evidence-backed" not in text and "Review limits" not in text,
                f"{label} combines report behavior before Step 5 or Step 6")
    if stage == "05-combine-tools":
        combined_marker = {
            "dotnet": "For each issue, call accessibility_rule_lookup",
            "nodejs": "evidence-backed",
            "python": "evidence-backed",
            "go": "evidence-backed",
            "rust": "evidence-backed",
            "java": "evidence-backed",
        }[language]
        require(combined_marker in text and "Review limits" not in text,
                f"{label} does not combine browser evidence with local guidance before Step 6")
    if stage == "06-structured-report":
        require("Review limits" in text,
                f"{label} executable entrypoint does not request the structured report limits")

    forbidden_capabilities = {
        "01-first-session": ("stream", "local", "mcp", "browser", "snapshot", "report"),
        "02-streaming": ("local", "mcp", "browser", "snapshot", "report"),
        "03-local-tool": ("mcp", "browser", "snapshot", "report"),
    }.get(stage, ())
    for capability in forbidden_capabilities:
        markers = apis.get(capability, ()) + LATER_CAPABILITIES.get(capability, ())
        require(not contains_any(text, markers),
                f"{label} executable entrypoint wires later-stage {capability} capability")

    if language == "nodejs" and stage in {"04-mcp-safety", "05-combine-tools"}:
        require('["http:", "https:"].includes(target.protocol)' in text,
                f"{label} accepts a non-HTTP(S) URL")
    return text


def validate_hello_manifest_entrypoint(language: str, directory: Path) -> None:
    """Ensure the sample's launch manifest reaches the entrypoint being inspected."""
    label = directory.relative_to(ROOT)
    entrypoint = directory / entrypoint_path(directory, language)
    require(has_manifest(directory, language), f"{label} is missing its {language} manifest")
    require(entrypoint.exists(), f"{label} manifest cannot reach {entrypoint_path(directory, language)}")

    manifest = read(next(directory.glob(MANIFESTS[language]))) if "*" in MANIFESTS[language] else read(directory / MANIFESTS[language])
    if language == "dotnet":
        require("<OutputType>Exe</OutputType>" in manifest,
                f"{label} project manifest does not define an executable")
    elif language == "nodejs":
        package = json.loads(manifest)
        require(package.get("scripts", {}).get("start") == "tsx src/index.ts",
                f"{label} package start script does not launch src/index.ts")
    elif language == "python":
        require("github-copilot-sdk==" in manifest
                and "[project]" in read(directory / "pyproject.toml")
                and 'if __name__ == "__main__":' in read(entrypoint),
                f"{label} Python manifest and main.py do not define a runnable entrypoint")
    elif language == "go":
        require("module " in manifest and "package main" in read(entrypoint) and "func main()" in read(entrypoint),
                f"{label} Go manifest does not reach package main")
    elif language == "rust":
        require("[package]" in manifest and "async fn main()" in read(entrypoint),
                f"{label} Cargo manifest does not reach src/main.rs")
    elif language == "java":
        require("<mainClass>workshop.AccessibilityGuidance</mainClass>" in manifest
                and "public static void main" in read(entrypoint),
                f"{label} Maven manifest does not launch AccessibilityGuidance")


def validate_hello_sample(language: str, directory: Path) -> None:
    stage = "03-local-tool"
    validate_hello_manifest_entrypoint(language, directory)
    text = validate_executable_stage(language, stage, directory)
    source = project_source(directory)
    label = directory.relative_to(ROOT)

    forbidden_capabilities = ("mcp", "browser", "snapshot", "permission", "report")
    if language == "java":
        forbidden_capabilities = tuple(
            capability for capability in forbidden_capabilities if capability != "permission")
    for capability in forbidden_capabilities:
        markers = LANGUAGE_APIS[language].get(capability, ()) + LATER_CAPABILITIES[capability]
        require(not contains_any(source, markers),
                f"{label} includes later-stage {capability} behavior")

    tool_config = {
        "dotnet": ("Tools = [AccessibilityRuleCatalog.CreateLookupTool()]", 'AvailableTools = ["accessibility_rule_lookup"]'),
        "nodejs": ("tools: [accessibilityRuleLookup]", 'availableTools: ["accessibility_rule_lookup"]'),
        "python": ("tools=[accessibility_rule_lookup]", 'available_tools=["accessibility_rule_lookup"]'),
        "go": ("Tools:          []copilot.Tool{lookup}", 'AvailableTools: []string{"accessibility_rule_lookup"}'),
        "rust": ("config.tools = Some(vec![lookup])", 'config.available_tools = Some(vec!["accessibility_rule_lookup".to_owned()])'),
        "java": (".setTools(List.of(lookup))", '.setAvailableTools(List.of("accessibility_rule_lookup"))'),
    }[language]
    require(contains_all(text, tool_config),
            f"{label} does not register only accessibility_rule_lookup")

    question_markers = {
        "dotnet": ("Console.ReadLine()", "Accessibility question:", "Use accessibility_rule_lookup to answer this question:"),
        "nodejs": ("readQuestion", "Accessibility question:", "Use accessibility_rule_lookup to answer this question:"),
        "python": ("read_question", "Accessibility question:", "Use accessibility_rule_lookup to answer this question:"),
        "go": ("readQuestion", "Accessibility question:", "Use accessibility_rule_lookup to answer this question:"),
        "rust": ("read_question", "Accessibility question:", "Use accessibility_rule_lookup to answer this question:"),
        "java": ("readQuestion", "Accessibility question:", "Use accessibility_rule_lookup to answer this question:"),
    }[language]
    require(contains_all(text, question_markers),
            f"{label} does not accept an accessibility question and direct the lookup tool")


def validate_html_assets(html_file: Path) -> None:
    parser = LocalAssetParser()
    parser.feed(read(html_file))
    for reference in parser.references:
        parsed = urlsplit(reference)
        if parsed.scheme or reference.startswith(("#", "?", "//", "data:")):
            continue
        target = (html_file.parent / parsed.path).resolve()
        if parsed.path.endswith("/"):
            target /= "index.html"
        require(target.exists(), f"{html_file.relative_to(ROOT)} links to missing local asset {reference}")


def validate_markdown_links(markdown_file: Path) -> None:
    for target_text in re.findall(r"!?\[[^\]]*\]\(([^)]+)\)", read(markdown_file)):
        target_value = target_text.split(maxsplit=1)[0].strip("<>")
        prefixes = (
            "https://github.com/jamesmontemagno/copilot-sdk-workshop/tree/main/",
            "https://github.com/jamesmontemagno/copilot-sdk-workshop/blob/main/",
        )
        prefix = next((candidate for candidate in prefixes if target_value.startswith(candidate)), None)
        if prefix:
            require(
                (ROOT / target_value.removeprefix(prefix)).exists(),
                f"{markdown_file.relative_to(ROOT)} links to missing repository path {target_value}",
            )
            continue
        parsed = urlsplit(target_value)
        if parsed.scheme or target_value.startswith(("#", "mailto:")):
            continue
        require(
            (markdown_file.parent / parsed.path).resolve().exists(),
            f"{markdown_file.relative_to(ROOT)} links to missing file {target_value}",
        )


def validate_language_directives(markdown_file: Path) -> None:
    active_language: str | None = None
    blocks: set[str] = set()
    for line_number, line in enumerate(read(markdown_file).splitlines(), start=1):
        opening = re.fullmatch(r":::language ([a-z0-9]+)", line)
        if opening:
            require(active_language is None, f"{markdown_file.relative_to(ROOT)}:{line_number} nests a language directive")
            active_language = opening.group(1)
            require(active_language in LANGUAGES, f"{markdown_file.relative_to(ROOT)}:{line_number} uses unknown language {active_language}")
            blocks.add(active_language)
        elif line == ":::":
            require(active_language is not None, f"{markdown_file.relative_to(ROOT)}:{line_number} closes no language directive")
            active_language = None
        elif line.startswith(":::"):
            require(False, f"{markdown_file.relative_to(ROOT)}:{line_number} has invalid language directive syntax")
    require(active_language is None, f"{markdown_file.relative_to(ROOT)} has an unclosed language directive")
    require(blocks == set(LANGUAGES), f"{markdown_file.relative_to(ROOT)} must contain exactly one or more blocks for all six languages")


def validate_shared_language_content(markdown_file: Path) -> None:
    active_language: str | None = None
    for line_number, line in enumerate(read(markdown_file).splitlines(), start=1):
        opening = re.fullmatch(r":::language ([a-z0-9]+)", line)
        if opening:
            active_language = opening.group(1)
        elif line == ":::":
            active_language = None
        elif active_language is None:
            require(
                not line.startswith("### "),
                f"{markdown_file.relative_to(ROOT)}:{line_number} exposes a "
                "language-specific procedure heading outside a language block",
            )
            for marker in UNSCOPED_TRACK_MARKERS:
                require(
                    marker.casefold() not in line.casefold(),
                    f"{markdown_file.relative_to(ROOT)}:{line_number} exposes "
                    f"language-specific content outside a language block: {marker}",
                )


def render_language_markdown(markdown_file: Path, selected_language: str) -> str:
    rendered: list[str] = []
    active_language: str | None = None
    for line in read(markdown_file).splitlines():
        opening = re.fullmatch(r":::language ([a-z0-9]+)", line)
        if opening:
            active_language = opening.group(1)
        elif line == ":::":
            active_language = None
        elif active_language is None or active_language == selected_language:
            rendered.append(line)
    return "\n".join(rendered)


def markdown_section(markdown: str, heading: str) -> str:
    lines = markdown.splitlines()
    try:
        start = lines.index(heading)
    except ValueError:
        return ""
    end = next(
        (index for index in range(start + 1, len(lines)) if lines[index].startswith("## ")),
        len(lines),
    )
    return "\n".join(lines[start:end])


def validate_rendered_language_content(markdown_file: Path) -> None:
    for selected_language in LANGUAGES:
        rendered = render_language_markdown(markdown_file, selected_language)
        rendered_folded = rendered.casefold()
        for other_language, markers in LESSON_TRACK_MARKERS.items():
            if other_language == selected_language:
                continue
            for marker in markers:
                require(
                    marker.casefold() not in rendered_folded,
                    f"{markdown_file.relative_to(ROOT)} shows {other_language} content "
                    f"for the {selected_language} track: {marker}",
                )

        if markdown_file.name == "03-local-tool.md":
            for marker in (
                *STEP_3_TRACK_MARKERS[selected_language],
                "## Run it",
                "Troubleshooting this run",
            ):
                require(
                    marker.casefold() in rendered_folded,
                    f"{markdown_file.relative_to(ROOT)} is missing {selected_language} "
                    f"Step 3 guidance: {marker}",
                )

        if markdown_file.name not in {"00-preflight.md", "museum-00-preflight.md"}:
            run_section = markdown_section(rendered, "## Run it")
            if markdown_file.name == "09-interactive-html-report.md":
                run_markers = STEP_9_RUN_COMMAND_MARKERS
            elif markdown_file.name.startswith("museum-"):
                run_markers = MUSEUM_COMMAND_MARKERS
            else:
                run_markers = RUN_COMMAND_MARKERS
            run_marker = run_markers[selected_language]
            require(
                contains_any(run_section, run_marker)
                if isinstance(run_marker, tuple)
                else run_marker.casefold() in run_section.casefold(),
                f"{markdown_file.relative_to(ROOT)} has no {selected_language} "
                f"run command in its Run it section: {run_marker}",
            )

        if markdown_file.name in PROCEDURE_MARKERS:
            procedure_marker = PROCEDURE_MARKERS[markdown_file.name][selected_language]
            run_position = rendered.find("## Run it")
            procedure_position = rendered.casefold().find(procedure_marker.casefold())
            require(
                0 <= procedure_position < run_position,
                f"{markdown_file.relative_to(ROOT)} does not show the {selected_language} "
                f"procedure before Run it: {procedure_marker}",
            )

        if markdown_file.name == "05-combine-tools.md" and selected_language == "java":
            for marker in ("private record Rule", "Rule.RULES", "\"1.1.1\"", "\"4.1.2\""):
                require(
                    marker.casefold() in rendered_folded,
                    f"{markdown_file.relative_to(ROOT)} does not teach the Java expanded rule catalog: {marker}",
                )
        if markdown_file.name == "05-combine-tools.md" and selected_language == "python":
            for marker in (
                "ToolExecutionStartData",
                "[tool:start]",
                "ToolExecutionCompleteData",
                "[tool:done]",
            ):
                require(
                    marker.casefold() in rendered_folded,
                    f"{markdown_file.relative_to(ROOT)} does not teach Python tool lifecycle events: {marker}",
                )

        if markdown_file.name == "09-interactive-html-report.md":
            for marker in (
                "accessibility-report.html",
                "builtin:apply_patch",
                "exact target navigation",
                "accessible text filter",
            ):
                require(
                    marker.casefold() in rendered_folded,
                    f"{markdown_file.relative_to(ROOT)} is missing {selected_language} "
                    f"interactive HTML report guidance: {marker}",
                )

        if markdown_file.name == "08-model-selection.md":
            require(
                "Enter the workshop target URL, then choose a model" in rendered,
                f"{markdown_file.relative_to(ROOT)} does not preserve target URL input before model selection",
            )


def validate_language_registry() -> None:
    registry = read(DOCS / "language-registry.js")
    ids = re.findall(r"\bid: '([a-z0-9]+)'", registry)
    require(ids == list(LANGUAGES), "docs/language-registry.js must be the ordered six-language registry")
    for language, url in OFFICIAL_SDK_URLS.items():
        require(url in registry, f"Language registry has no official {language} SDK link")
    require("Object.freeze" in registry and "getLanguage" in registry, "Language registry must expose immutable language lookup")


def validate_layout() -> None:
    for language in LANGUAGES:
        directories = [
            ROOT / "start-accessibility" / language,
            ROOT / "start-museum" / language,
            *(ROOT / "finished" / language / project for project in (
                "hello-copilot-sdk",
                "accessibility-report",
                "museum-exhibit-studio",
            )),
        ]
        for directory in directories:
            require(directory.is_dir(), f"Missing {language} project directory {directory.relative_to(ROOT)}")
            require(has_manifest(directory, language), f"Missing {language} manifest in {directory.relative_to(ROOT)}")
            require((directory / entrypoint_path(directory, language)).exists(),
                    f"Missing {language} executable entrypoint in {directory.relative_to(ROOT)}")
    for language in ("nodejs", "go", "rust"):
        for directory in [
            ROOT / "start-accessibility" / language,
            ROOT / "start-museum" / language,
            *(ROOT / "finished" / language / project for project in (
                "hello-copilot-sdk",
                "accessibility-report",
                "museum-exhibit-studio",
            )),
        ]:
            lock = {"nodejs": "package-lock.json", "go": "go.sum", "rust": "Cargo.lock"}[language]
            require((directory / lock).exists(), f"Missing deterministic {language} lock file in {directory.relative_to(ROOT)}")
    require(
        (ROOT / "start-museum" / "dotnet" / "packages.lock.json").exists(),
        "Missing deterministic .NET package lock in start-museum/dotnet",
    )


MUSEUM_HELPER_PATTERNS = {
    "dotnet": ("Helpers/Curator*.cs",),
    "nodejs": ("src/curator.ts",),
    "python": ("curator.py",),
    "go": ("curator.go",),
    "rust": ("src/lib.rs",),
    "java": ("src/main/java/workshop/Curator*.java",),
}
MUSEUM_HELPER_SYMBOLS = (
    "apollo11facts",
    "greatbarrierreeffacts",
    "terracottaarmyfacts",
    "factsets",
    "maximumfactcount",
    "maximumfactlength",
    "boundfacts",
    "approvedfactlookup",
    "streamexhibit",
    "validateexhibit",
    "formatvalidation",
    "wikipediaserver",
    "wikipediapermission",
    "extractsources",
    "exhibitwrite",
    "askyesno",
    "readfacts",
)
MUSEUM_HELPER_LESSON_REFERENCES = {
    "dotnet": re.compile(r"Helpers/Curator[A-Za-z]+\.cs"),
    "nodejs": re.compile(r"src/curator\.ts"),
    "python": re.compile(r"(?<![\w/])curator\.py"),
    "go": re.compile(r"(?<![\w/])curator\.go"),
    "rust": re.compile(r"src/lib\.rs"),
    "java": re.compile(r"(?<![\w/])Curator[A-Za-z]+\.java"),
}
MUSEUM_ABSTRACTION_MARKERS = (
    "icuratorclient",
    "icuratorsession",
    "curatorclient",
    "curatorsession",
    "curatorruntime",
    "copilotcuratorclient",
)
MUSEUM_RETIRED_RESEARCH_MARKERS = (
    "proposedaddition",
    "selectapprovedfacts",
    "parseresearchresult",
    "researchmodels",
    "factreview",
    "incompleteresearch",
)
MUSEUM_STARTER_SOLUTION_MARKERS = (
    "systemmessage",
    "buildexhibitprompt",
    "buildresearchprompt",
    "availabletools",
    "createsession",
    "copilotclient",
    "mcpservers",
)
MUSEUM_ONE_TOOL_ALLOWLIST = {
    "dotnet": (r"availabletools=\[curatorfacts\.approvedfactlookupname\]",),
    "nodejs": (r"availabletools:\[approvedfactlookupname\]",),
    "python": (r"[\"']?availabletools[\"']?[=:]\[approvedfactlookupname\]",),
    "go": (r"availabletools:\[\]string\{approvedfactlookupname\}",),
    "rust": (r"availabletools=some\(vec!\[approvedfactlookupname\.toowned\(\)\]\)",),
    "java": (r"setavailabletools\(list\.of\(curatorfacts\.approvedfactlookupname\)\)",),
}
MUSEUM_TOOL_REGISTRATION = {
    "dotnet": (r"tools=\[curatorfacts\.createapprovedfactlookup\(",),
    "nodejs": (r"tools:\[createapprovedfactlookup\(",),
    "python": (r"[\"']?tools[\"']?[=:]\[createapprovedfactlookup\(",),
    "go": (r"tools:\[\]copilot\.tool\{lookup\}",),
    "rust": (r"tools=some\(vec!\[approvedfactlookup\(",),
    "java": (r"settools\(list\.of\(curatorfacts\.approvedfactlookup\(",),
}
# A session created without a permission handler does not deny requests: the runtime emits them as
# events and leaves them pending for manual resolution, so the run stalls. Repository validation
# never authenticates the Copilot CLI or sends a prompt, so nothing else here can catch that.
MUSEUM_SESSION_CONFIGURATION_LESSONS = (
    "museum-01-first-curator-session.md",
    "museum-02-stream-the-curator.md",
    "museum-03-curator-voice.md",
    "museum-04-approved-facts.md",
    "museum-05-guardrails.md",
    "museum-07-wikipedia-research.md",
    "museum-08-interactive-exhibit-page.md",
)
MUSEUM_ANY_PERMISSION_HANDLER = {
    "dotnet": r"onpermissionrequest=",
    "nodejs": r"onpermissionrequest:",
    "python": r"[\"']?onpermissionrequest[\"']?[=:]",
    "go": r"onpermissionrequest:",
    "rust": r"withpermissionhandler\(",
    "java": r"setonpermissionrequest\(",
}
MUSEUM_APPROVE_ALL_PERMISSION_HANDLER = {
    "dotnet": r"onpermissionrequest=permissionhandler\.approveall",
    "nodejs": r"onpermissionrequest:approveall",
    "python": r"[\"']?onpermissionrequest[\"']?[=:]permissionhandler\.approveall",
    "go": r"onpermissionrequest:copilot\.permissionhandler\.approveall",
    "rust": r"withpermissionhandler\(permission::approveall\(\)\)",
    "java": r"setonpermissionrequest\(permissionhandler\.approveall\)",
}
MUSEUM_SESSION_CREATION = {
    "dotnet": r"createsessionasync\(",
    "nodejs": r"createsession\(",
    "python": r"createsession\(",
    "go": r"createsession\(",
    "rust": r"createsession\(",
    "java": r"createsession\(",
}
# Every pre-built Rust helper reports failure as the crate's `RuntimeError` alias. A lesson that
# declares `Result<_, Box<dyn std::error::Error>>` instead stops compiling the moment it uses `?` on
# a helper call: `dyn Error + Send + Sync` is unsized, so it does not implement `Error`, and
# `Box<dyn Error>` therefore has no `From<Box<dyn Error + Send + Sync>>` impl. Assert the declared
# error type rather than any prose, because the type is what the compiler rejects.
MUSEUM_RUST_ERROR_ALIAS = "RuntimeError"
MUSEUM_RUST_ERROR_ALIAS_DEFINITION = (
    f"pub type {MUSEUM_RUST_ERROR_ALIAS} = Box<dyn Error + Send + Sync>;"
)
MUSEUM_RUST_ENTRYPOINT = re.compile(
    r"\bfn\s+(?P<name>main|run)\b\s*\([^)]*\)\s*(?:->\s*(?P<returns>[^{\n]+?)\s*)?\{"
)
MUSEUM_RUST_CRATE_IMPORT = re.compile(
    r"use museum_exhibit_studio::(?:\{(?P<names>[^}]*)\}|(?P<name>[A-Za-z0-9_]+))\s*;", re.S
)


def museum_symbols(text: str) -> str:
    """Fold case and drop underscores so one marker matches every language's naming style."""
    return text.casefold().replace("_", "")


def museum_tokens(text: str) -> str:
    """Fold case and drop underscores and whitespace so configuration markers match any layout."""
    return re.sub(r"\s+", "", museum_symbols(text))


def strip_line_comments(text: str) -> str:
    """Drop whole-line // and # comments so scaffold guidance is not read as seeded code."""
    return "\n".join(
        line for line in text.splitlines()
        if not re.match(r"\s*(//|#)", line)
    )


def museum_helper_source(directory: Path, language: str) -> str:
    paths = sorted(
        path
        for pattern in MUSEUM_HELPER_PATTERNS[language]
        for path in directory.glob(pattern)
    )
    require(
        bool(paths),
        f"{directory.relative_to(ROOT)} has no pre-built curator helper module "
        f"({', '.join(MUSEUM_HELPER_PATTERNS[language])})",
    )
    return "\n".join(read(path) for path in paths)


def validate_museum_projects() -> None:
    ignored_directories = {
        ".venv",
        "__pycache__",
        "bin",
        "dist",
        "node_modules",
        "obj",
        "target",
    }

    def tracked_project_files(directory: Path):
        return (
            path
            for path in directory.rglob("*")
            if path.is_file()
            and not ignored_directories.intersection(
                part.casefold() for part in path.relative_to(directory).parts[:-1]
            )
        )

    for language in LANGUAGES:
        starter = ROOT / "start-museum" / language
        starter_symbols = museum_symbols(project_source(starter))
        entrypoint = read(starter / entrypoint_path(starter, language))
        # Placement comments tell the learner where each step's code goes. They name SDK members
        # on purpose, so only real code is checked for seeded solutions.
        entrypoint_symbols = museum_symbols(strip_line_comments(entrypoint))
        require(
            "Museum Exhibit Studio starter" in entrypoint,
            f"{starter.relative_to(ROOT)} does not identify itself when run",
        )
        for step_reference in ("Step 1", "Step 4", "Step 5", "Step 8"):
            require(
                step_reference in entrypoint,
                f"{starter.relative_to(ROOT)} entrypoint does not tell the learner where "
                f"{step_reference} code goes",
            )
        helper_symbols = museum_symbols(museum_helper_source(starter, language))
        for symbol in MUSEUM_HELPER_SYMBOLS:
            require(
                symbol in helper_symbols,
                f"{starter.relative_to(ROOT)} helper module is missing {symbol}",
            )
        require(
            "approved_fact_lookup" in museum_helper_source(starter, language),
            f"{starter.relative_to(ROOT)} helper module does not ship the pre-built "
            "approved_fact_lookup tool",
        )
        for marker in MUSEUM_STARTER_SOLUTION_MARKERS:
            require(
                marker not in entrypoint_symbols,
                f"{starter.relative_to(ROOT)} entrypoint seeds lesson solution code: {marker}",
            )
        for marker in MUSEUM_ABSTRACTION_MARKERS:
            require(
                marker not in starter_symbols,
                f"{starter.relative_to(ROOT)} still wraps the SDK in an abstraction: {marker}",
            )
        require(
            not any(
                path.is_file()
                and (
                    "test" in {part.casefold() for part in path.relative_to(starter).parts[:-1]}
                    or path.name.casefold().endswith(("_test.go", ".test.ts", "test.java"))
                )
                for path in tracked_project_files(starter)
            ),
            f"{starter.relative_to(ROOT)} contains a test artifact",
        )

        finished = ROOT / "finished" / language / "museum-exhibit-studio"
        finished_source = project_source(finished)
        finished_symbols = museum_symbols(finished_source)
        finished_tokens = museum_tokens(finished_source)
        finished_helper_symbols = museum_symbols(museum_helper_source(finished, language))
        for symbol in MUSEUM_HELPER_SYMBOLS:
            require(
                symbol in finished_helper_symbols,
                f"{finished.relative_to(ROOT)} helper module is missing {symbol}",
            )
        require(
            museum_helper_source(starter, language) == museum_helper_source(finished, language),
            f"{starter.relative_to(ROOT)} and {finished.relative_to(ROOT)} ship different "
            "curator helper modules; a learner must end up with the starter's helpers unchanged",
        )
        for marker in MUSEUM_ABSTRACTION_MARKERS:
            require(
                marker not in finished_symbols,
                f"{finished.relative_to(ROOT)} still wraps the SDK in an abstraction: {marker}",
            )
        for marker in MUSEUM_RETIRED_RESEARCH_MARKERS:
            require(
                marker not in finished_symbols,
                f"{finished.relative_to(ROOT)} keeps the retired research contract: {marker}",
            )
        require(
            any(
                re.search(pattern, finished_tokens)
                for pattern in MUSEUM_ONE_TOOL_ALLOWLIST[language]
            ),
            f"{finished.relative_to(ROOT)} does not restrict exhibit generation to the "
            "single approved_fact_lookup allowlist entry",
        )
        require(
            any(
                re.search(pattern, finished_tokens)
                for pattern in MUSEUM_TOOL_REGISTRATION[language]
            ),
            f"{finished.relative_to(ROOT)} does not register the approved_fact_lookup "
            "implementation on the generation session",
        )
        require(
            "approved_fact_lookup" in finished_source,
            f"{finished.relative_to(ROOT)} never names the approved_fact_lookup tool",
        )
        for marker in ("wikipedia-mcp@1.0.3", "builtin:apply_patch", "exhibit.html"):
            require(
                marker in finished_source,
                f"{finished.relative_to(ROOT)} is missing required behavior: {marker}",
            )
        require(
            "#[cfg(test)]" not in finished_source,
            f"{finished.relative_to(ROOT)} contains inline Rust tests",
        )
        require(
            not any(
                path.is_file()
                and (
                    "test" in {part.casefold() for part in path.relative_to(finished).parts[:-1]}
                    or path.name.casefold().endswith(("_test.go", ".test.ts", "test.java"))
                    or path.name.casefold().startswith("test_")
                    or "mock-wikipedia" in path.name.casefold()
                )
                for path in tracked_project_files(finished)
            ),
            f"{finished.relative_to(ROOT)} contains a museum test artifact",
        )

    node_package = json.loads(read(ROOT / "finished" / "nodejs" / "museum-exhibit-studio" / "package.json"))
    require("test" not in node_package.get("scripts", {}), "Finished Node museum package still defines tests")
    java_pom = read(ROOT / "finished" / "java" / "museum-exhibit-studio" / "pom.xml")
    require(
        "junit" not in java_pom.casefold() and "surefire" not in java_pom.casefold(),
        "Finished Java museum manifest still includes test-only configuration",
    )


def validate_python_dependencies() -> None:
    directories = [
        ROOT / "start-accessibility" / "python",
        ROOT / "start-museum" / "python",
        *(ROOT / "finished" / "python" / project for project in (
            "hello-copilot-sdk",
            "accessibility-report",
            "museum-exhibit-studio",
        )),
    ]
    for directory in directories:
        requirements = [
            line.strip() for line in read(directory / "requirements.txt").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]
        require(requirements, f"{directory.relative_to(ROOT)} has no pinned Python dependencies")
        for requirement in requirements:
            require("==" in requirement and not requirement.startswith(("-", "git+", "http:")),
                    f"{directory.relative_to(ROOT)} has an unpinned Python dependency: {requirement}")
        require(any(requirement.startswith("github-copilot-sdk==") for requirement in requirements),
                f"{directory.relative_to(ROOT)} does not pin github-copilot-sdk")


def validate_security_invariants() -> None:
    required_tools = ("accessibility_rule_lookup", "read_latest_accessibility_snapshot", "playwright-browser_navigate")
    for language in LANGUAGES:
        directory = ROOT / "finished" / language / "accessibility-report"
        for directory in (directory,):
            source = project_source(directory)
            for tool in required_tools:
                require(tool in source, f"{directory.relative_to(ROOT)} is missing canonical tool {tool}")
            require("browser_snapshot" not in source, f"{directory.relative_to(ROOT)} exposes browser_snapshot")
            require("browser_navigate" in source, f"{directory.relative_to(ROOT)} does not expose browser_navigate")
            require("read_latest_accessibility_snapshot" in source, f"{directory.relative_to(ROOT)} has no scoped snapshot reader")
            require(re.search(r"snapshot.*bytes", source, re.IGNORECASE) is not None,
                    f"{directory.relative_to(ROOT)} snapshot reader lacks a bounded no-path reader")
            exact_url_markers = {
                "dotnet": "UriComponents.PathAndQuery | UriComponents.Fragment",
                "nodejs": "function sameUrl",
                "python": "def _same_url",
                "go": "func sameURL",
                "rust": "fn same_url",
                "java": "boolean sameUrl",
            }
            require(exact_url_markers[language] in source, f"{directory.relative_to(ROOT)} does not compare target URL components exactly")
            if language == "rust":
                require(
                    'match extra.get("permissionRequest")' in source
                    and "Some(request) => request.as_object()" in source
                    and "None => extra.as_object()" in source,
                    f"{directory.relative_to(ROOT)} does not normalize the Rust SDK permission payload",
                )
            if language == "java":
                strict_marker = '&& isExactNavigation(request.getExtensionData(), target)'
                fallback_marker = 'if (options.allowLocalDemoMcp() && "mcp".equals(request.getKind()))'
                reject_marker = "PermissionRequestResult.reject"
                require(
                    all(marker in source for marker in (
                        'LOCAL_DEMO_MCP_FLAG = "--allow-local-demo-mcp"',
                        "parseRunOptions(args)",
                        strict_marker,
                        fallback_marker,
                        "PermissionRequestResult.approveOnce()",
                        reject_marker,
                    )),
                    f"{directory.relative_to(ROOT)} does not implement the explicit Java local-demo MCP fallback",
                )
                require(
                    source.index(strict_marker) < source.index(fallback_marker) < source.index(reject_marker),
                    f"{directory.relative_to(ROOT)} does not preserve exact-target rejection before its Java fallback",
                )
                require(
                    "APPROVE_ALL" not in source,
                    f"{directory.relative_to(ROOT)} must not use unqualified Java permission approval",
                )
    rust_permission_markers = (
        'match extra.get("permissionRequest")',
        "Some(request) => request.as_object()",
        "None => extra.as_object()",
    )
    for lesson in ("04-mcp-safety.md", "05-combine-tools.md"):
        rendered = render_language_markdown(WORKSHOP / lesson, "rust")
        require(
            all(marker in rendered for marker in rust_permission_markers),
            f"workshop/{lesson} does not preserve Rust permission payload normalization",
        )
    report_lesson = render_language_markdown(WORKSHOP / "09-interactive-html-report.md", "rust")
    require(
        "permission_payload(&request.extra)" in report_lesson,
        "workshop/09-interactive-html-report.md does not use normalized Rust write permission data",
    )
    for lesson in (
        "04-mcp-safety.md",
        "05-combine-tools.md",
        "06-structured-report.md",
        "07-run-explain.md",
        "08-model-selection.md",
    ):
        rendered = render_language_markdown(WORKSHOP / lesson, "java")
        require(
            all(marker in rendered for marker in (
                "--allow-local-demo-mcp",
                "https://github.com/github/copilot-sdk/issues/2273",
                "exact",
                "mcp",
            )),
            f"workshop/{lesson} does not document the Java local-demo MCP fallback boundary",
        )
    java_report_lesson = render_language_markdown(WORKSHOP / "09-interactive-html-report.md", "java")
    require(
        all(marker in java_report_lesson for marker in (
            "--allow-local-demo-mcp",
            "--allow-local-demo-write",
            "options.allowLocalDemoWrite()",
            '"write".equals(request.getKind())',
            "builtin:apply_patch",
            "cannot enforce the output path",
            "https://github.com/github/copilot-sdk/issues/2273",
        )),
        "workshop/09-interactive-html-report.md does not constrain the Java local-demo write fallback",
    )


def validate_playwright_file_output(text: str, label: Path) -> None:
    configurations = text.split(PLAYWRIGHT_MCP_PACKAGE)[1:]
    for index, configuration in enumerate(configurations, start=1):
        configuration = configuration.split(PLAYWRIGHT_MCP_PACKAGE, maxsplit=1)[0]
        require(
            PLAYWRIGHT_OUTPUT_DIRECTORY.search(configuration) is not None,
            f"{label} Playwright MCP configuration {index} must pair --output-dir with .playwright-mcp",
        )
        require(
            PLAYWRIGHT_OUTPUT_MODE.search(configuration) is not None,
            f"{label} Playwright MCP configuration {index} must pair --output-mode with file",
        )


def validate_playwright_output_configuration() -> None:
    directories = [
        *(ROOT / "start-accessibility" / language for language in LANGUAGES),
        *(ROOT / "finished" / language / "accessibility-report" for language in LANGUAGES),
    ]
    for directory in directories:
        validate_playwright_file_output(project_source(directory), directory.relative_to(ROOT))

    for lesson in ("04-mcp-safety.md", "05-combine-tools.md", "06-structured-report.md", "08-model-selection.md"):
        lesson_path = WORKSHOP / lesson
        for language in LANGUAGES:
            validate_playwright_file_output(
                render_language_markdown(lesson_path, language),
                Path(f"workshop/{lesson} ({language})"),
            )


def validate_project_behavior() -> None:
    for language in LANGUAGES:
        starter = ROOT / "start-accessibility" / language
        require((starter / ENTRYPOINTS[language]).exists(),
                f"Missing {language} starter executable {ENTRYPOINTS[language]}")
        validate_executable_stage(language, "starter", starter)

    for language in LANGUAGES:
        directory = ROOT / "finished" / language / "hello-copilot-sdk"
        validate_hello_sample(language, directory)

    for language, stage, directory in (
        ("go", "06-structured-report", ROOT / "finished" / "go" / "accessibility-report"),
        ("rust", "06-structured-report", ROOT / "finished" / "rust" / "accessibility-report"),
        ("java", "06-structured-report", ROOT / "finished" / "java" / "accessibility-report"),
    ):
        text = executable_source(directory, language)
        validate_runtime_flow(language, stage, runtime_source(directory, language, text), directory.relative_to(ROOT))
    for directory in (ROOT / "finished" / "python" / "accessibility-report",):
        validate_runtime_flow(
            "python",
            "06-structured-report",
            read(directory / "report.py"),
            directory.relative_to(ROOT),
        )

    node_report_package = read(ROOT / "finished" / "nodejs" / "accessibility-report" / "package.json")
    require('"start": "tsx src/report.ts"' in node_report_package,
            "Node accessibility-report npm start must execute src/report.ts")
    for directory in [ROOT / "start-accessibility" / "nodejs", ROOT / "finished" / "nodejs" / "accessibility-report"]:
        source = read(directory / "src" / "workshop.ts")
        require("const existingSnapshots = safeSnapshotNames(outputDirectory)" in source,
                f"{directory.relative_to(ROOT)} captures snapshot baseline lazily")
        require("const baseline = await existingSnapshots" in source,
                f"{directory.relative_to(ROOT)} does not await the construction-time snapshot baseline")
    for directory in [ROOT / "start-accessibility" / "python", *(ROOT / "finished" / "python" / project for project in ("hello-copilot-sdk", "accessibility-report"))]:
        report_path = directory / "report.py"
        if report_path.exists():
            require('if __name__ == "__main__":' in read(report_path),
                    f"{directory.relative_to(ROOT)} report entrypoint cannot be imported safely")
    for directory in [ROOT / "start-accessibility" / "java", *(ROOT / "finished" / "java" / project for project in ("hello-copilot-sdk", "accessibility-report"))]:
        main_class = "AccessibilityGuidance" if directory.name == "hello-copilot-sdk" else "AccessibilityReport"
        require(f"<mainClass>workshop.{main_class}</mainClass>" in read(directory / "pom.xml"),
                f"{directory.relative_to(ROOT)} does not configure the Maven executable entrypoint")


def validate_site_behavior() -> None:
    index = read(DOCS / "index.html")
    step = read(DOCS / "workshop" / "step.html")
    navigation = read(DOCS / "language-navigation.js")
    require(index.count('class="primary-action"') == 1, "Homepage must have exactly one primary action")
    require(index.count('name="workshop"') == 2, "Homepage must offer exactly two workshop choices")
    require('value="sdlc"' in index and 'value="museum"' in index,
            "Homepage must offer SDLC and museum workshop choices")
    require(index.count('name="language"') == len(LANGUAGES),
            "Homepage must offer exactly six language choices")
    require('name="language" value="dotnet" required' in index and "checked" not in index,
            "Homepage must require a language without choosing a default")
    require('id="languagePicker"' in index and "homepage.js" in index, "Homepage is missing language selection behavior")
    require("language-navigation.js" in index and "language-navigation.js" in step, "Homepage and lessons must share language navigation")
    require("resolveLanguage" in navigation and "lessonUrl" in navigation and "firstLessonUrl" in navigation, "Language navigation must preserve URL propagation")
    require("localStorage" in read(DOCS / "homepage.js") and "localStorage" in step, "Homepage and lessons must persist language selection")
    require("Choose a workshop language" in step and "if (!language)" in step, "Lessons must not load without a valid language")
    require("preprocessLanguageDirectives" in step, "Lesson viewer must filter language directives")
    require("workshopTracks" in step and "activeWorkshopId" in step,
            "Lesson viewer must scope navigation to the active workshop")
    require("museum-00-preflight" in navigation,
            "Language navigation must route the museum workshop to its own preflight")
    for hook in ("event.key === 'Escape'", "trapNavigationFocus", "toggleAttribute('inert'", "initializeTabs", 'id="lessonStatus"', 'id="progressTrack"'):
        require(hook in step, f"Lesson viewer is missing behavior hook: {hook}")
    for html_file in (DOCS / "index.html", DOCS / "workshop" / "step.html", DOCS / "target-app" / "index.html"):
        validate_html_assets(html_file)


def validate_documentation() -> None:
    for markdown in [
        ROOT / "README.md",
        ROOT / "start-accessibility" / "README.md",
        ROOT / "start-museum" / "README.md",
        *WORKSHOP.glob("*.md"),
    ]:
        validate_markdown_links(markdown)
    published = "\n".join(read(path) for path in [ROOT / "README.md", *WORKSHOP.glob("*.md"), *DOCS.rglob("*.html")])
    for forbidden in ("jamesmontemagno.github.io", "codemillmatt.github.io", "](../start-accessibility/", "](../finished/"):
        require(forbidden not in published, f"Published content contains forbidden pattern: {forbidden}")
    for url in OFFICIAL_SDK_URLS.values():
        require(url in read(ROOT / "README.md"), f"README is missing official SDK link {url}")
    require("https://github.com/github/copilot-sdk/tree/main/cookbook" in read(ROOT / "README.md"), "README is missing the official cookbook link")
    all_markdown = "\n".join(read(path) for path in [
        ROOT / "README.md",
        ROOT / "start-accessibility" / "README.md",
        ROOT / "start-museum" / "README.md",
        *WORKSHOP.glob("*.md"),
    ])
    require("go run ./finished/" not in all_markdown and "go run finished/" not in all_markdown,
            "Documentation runs Go modules from the repository root instead of their module directory")
    starters = read(ROOT / "start-accessibility" / "README.md")
    require("cd start-accessibility/go && go build -mod=readonly ./..." in starters,
            "Starter documentation must build Go modules in place with the lock enforced")
    require("python -m pip install -r requirements.txt" in starters,
            "Starter documentation must install the pinned Python requirements")
    require("python report.py" not in all_markdown,
            "Documentation must invoke Python main.py rather than an unwired report.py")
    for lesson in ("01-first-session.md", "05-combine-tools.md", "06-structured-report.md"):
        require("python main.py" in read(WORKSHOP / lesson),
                f"{lesson} must run the Python project through main.py")

    # Learners clone the repository and work in place inside start-accessibility/<language> or
    # start-museum/<language>. No copied sibling project may reappear anywhere.
    for lesson in LESSONS:
        lesson_text = read(WORKSHOP / lesson)
        for forbidden in IN_PLACE_FORBIDDEN_MARKERS:
            require(
                forbidden not in lesson_text,
                f"workshop/{lesson} still references the retired copied project: {forbidden}",
            )
        for forbidden in SECOND_PROJECT_MARKERS:
            require(
                forbidden not in lesson_text,
                f"workshop/{lesson} scaffolds or copies a second project instead of "
                f"working in place: {forbidden}",
            )
    for documentation in (
        ROOT / "README.md",
        ROOT / "start-accessibility" / "README.md",
        ROOT / "start-museum" / "README.md",
    ):
        documentation_text = read(documentation)
        for forbidden in (*IN_PLACE_FORBIDDEN_MARKERS, *SECOND_PROJECT_MARKERS):
            require(
                forbidden not in documentation_text,
                f"{documentation.relative_to(ROOT)} still describes the retired copy flow: "
                f"{forbidden}",
            )

    accessibility_preflight = read(WORKSHOP / "00-preflight.md")
    require(
        "git clone https://github.com/jamesmontemagno/copilot-sdk-workshop.git"
        in accessibility_preflight,
        "Accessibility preflight must start from a clone of the repository",
    )
    for language in LANGUAGES:
        require(
            f"cd start-accessibility/{language}" in accessibility_preflight,
            f"Accessibility preflight must change into the {language} starter directory",
        )
    require(
        "git checkout -- ." in accessibility_preflight,
        "Accessibility preflight must explain how to restore a clean starter",
    )
    require(
        "git status" in accessibility_preflight,
        "Accessibility preflight must tell learners their in-place edits appear in git status",
    )

    lesson_viewer = read(DOCS / "workshop" / "step.html")
    for step_id in (
        "09-interactive-html-report",
        "museum-00-preflight",
        "museum-01-first-curator-session",
        "museum-02-stream-the-curator",
        "museum-03-curator-voice",
        "museum-04-approved-facts",
        "museum-05-guardrails",
        "museum-06-prove-the-structure",
        "museum-07-wikipedia-research",
        "museum-08-interactive-exhibit-page",
    ):
        require(
            f"id: '{step_id}'" in lesson_viewer,
            f"Lesson viewer navigation is missing {step_id}",
        )
    for retired_step_id in (
        "museum-01-curator-role",
        "museum-02-tool-free-session",
        "museum-05-lifecycle-tests",
        "museum-06-run-review",
        "museum-07-wikipedia-grounding",
    ):
        require(
            f"id: '{retired_step_id}'" not in lesson_viewer,
            f"Lesson viewer still registers the retired museum step {retired_step_id}",
        )
        require(
            f"'{retired_step_id}':" in lesson_viewer,
            f"Lesson viewer must keep a legacy redirect for {retired_step_id}",
        )
    require(
        "'museum-03-approved-facts': 'museum-04-approved-facts'" in lesson_viewer
        and "'museum-04-deterministic-validation': 'museum-06-prove-the-structure'" in lesson_viewer
        and "'museum-05-lifecycle-tests': 'museum-05-guardrails'" in lesson_viewer
        and "'museum-07-wikipedia-grounding': 'museum-07-wikipedia-research'" in lesson_viewer,
        "Legacy museum step URLs must map onto the redesigned lessons",
    )

    wikipedia_lesson = read(WORKSHOP / "museum-07-wikipedia-research.md")
    for required_step in (
        "# Step 7: Research with Wikipedia MCP",
        "## Two sessions, two capability profiles",
        "## Add the research session",
        "wikipedia-search",
        "wikipedia-readArticle",
        "deny-by-default",
        "Research notes are never merged into the approved facts.",
        "The session that writes the exhibit keeps its one-tool allowlist.",
        "Consulted Wikipedia sources:",
    ):
        require(
            required_step in wikipedia_lesson,
            f"Wikipedia MCP lesson is missing required implementation guidance: {required_step}",
        )
    require(
        "# Optional: Wikipedia MCP" not in wikipedia_lesson,
        "Wikipedia MCP must be a required museum workshop step",
    )
    require(
        "id: 'museum-07-wikipedia-research'" in lesson_viewer
        and "title: 'Research with Wikipedia MCP',\n                navTitle: 'Wikipedia research'" in lesson_viewer
        and "kind: 'core',\n                number: 7,\n                time: '20 min'" in lesson_viewer,
        "Wikipedia MCP must be registered as required 20-minute museum step 7",
    )

    html_lesson = read(WORKSHOP / "museum-08-interactive-exhibit-page.md")
    for required_step in (
        "builtin:apply_patch",
        "exhibit.html",
        "accessible text filter",
        "keyboard focus",
    ):
        require(
            required_step in html_lesson,
            f"Optional exhibit page lesson is missing required guidance: {required_step}",
        )
    require(
        "id: 'museum-08-interactive-exhibit-page'" in lesson_viewer
        and "kind: 'optional',\n                number: 8,\n                time: '15 min'" in lesson_viewer,
        "The interactive exhibit page must be registered as optional 15-minute museum step 8",
    )

    landing_page = read(DOCS / "index.html")
    require(
        "Non-SDLC tool · 90 minutes" in landing_page
        and "90 minutes for Museum Exhibit Studio" in read(ROOT / "README.md"),
        "Museum workshop duration must match the seven timed core steps",
    )

    museum_lessons = {name: read(WORKSHOP / name) for name in MUSEUM_LESSONS}
    combined_museum = "\n".join(museum_lessons.values())
    for forbidden in MUSEUM_FORBIDDEN_LESSON_MARKERS:
        require(
            forbidden.casefold() not in combined_museum.casefold(),
            f"Museum lessons still reference retired workshop content: {forbidden}",
        )
    require(
        not re.search(r"(?<![-\w])start/", combined_museum),
        "Museum lessons must copy starters from start-museum/, not a bare start/ path",
    )
    require(
        not (WORKSHOP / "museum-07-guides").exists(),
        "workshop/museum-07-guides must be deleted; lessons now carry the per-language code",
    )
    for name, text in museum_lessons.items():
        if name == "museum-00-preflight.md":
            continue
        for language in LANGUAGES:
            rendered = render_language_markdown(WORKSHOP / name, language)
            require(
                MUSEUM_ENTRYPOINTS[language] in rendered,
                f"{name} ({language}) must grow the single in-place museum project through "
                f"{MUSEUM_ENTRYPOINTS[language]}",
            )
            # Learners call a large pre-built helper module in every step. Each lesson has to
            # point at the file that holds it, in that reader's own language, so the "look
            # inside" notes cannot quietly disappear.
            require(
                MUSEUM_HELPER_LESSON_REFERENCES[language].search(rendered) is not None,
                f"{name} ({language}) must tell the learner which pre-built curator helper file "
                f"to open (expected a reference matching "
                f"{MUSEUM_HELPER_LESSON_REFERENCES[language].pattern})",
            )

    # The museum curator reaches its approved facts through one application-owned local tool.
    # Nothing in the track may claim the session is tool-free or that its allowlist is empty.
    for retired_framing in (
        "tool-free",
        "tool free",
        "empty tool allowlist",
        "empty allowlist",
    ):
        require(
            retired_framing not in combined_museum.casefold(),
            f"Museum lessons still describe the curator as {retired_framing!r}; the curator now "
            "reaches its approved facts through the approved_fact_lookup tool",
        )

    facts_lesson = museum_lessons["museum-04-approved-facts.md"]
    require(
        "Call approved_fact_lookup first." in facts_lesson
        or "Call `approved_fact_lookup` first." in facts_lesson,
        "museum-04-approved-facts.md must instruct the curator to call approved_fact_lookup first",
    )
    require(
        "[tool:start] approved_fact_lookup" in facts_lesson,
        "museum-04-approved-facts.md must show the approved_fact_lookup tool event in its run output",
    )
    for language in LANGUAGES:
        for lesson_name, lesson_label in (
            ("museum-04-approved-facts.md", "register"),
            ("museum-05-guardrails.md", "keep"),
        ):
            rendered = museum_tokens(render_language_markdown(WORKSHOP / lesson_name, language))
            require(
                any(
                    re.search(pattern, rendered)
                    for pattern in MUSEUM_TOOL_REGISTRATION[language]
                ),
                f"workshop/{lesson_name} ({language}) must {lesson_label} the approved_fact_lookup "
                "implementation in the session tool list",
            )
            require(
                any(
                    re.search(pattern, rendered)
                    for pattern in MUSEUM_ONE_TOOL_ALLOWLIST[language]
                ),
                f"workshop/{lesson_name} ({language}) must {lesson_label} approved_fact_lookup as "
                "the single entry in the session tool allowlist",
            )

    museum_preflight = read(WORKSHOP / "museum-00-preflight.md")
    for clone_step in (
        "git clone https://github.com/jamesmontemagno/copilot-sdk-workshop.git",
        'test "$(git rev-parse --show-toplevel)" = "$PWD"',
    ):
        require(
            clone_step in museum_preflight,
            f"Museum preflight is missing clone guidance: {clone_step}",
        )
    require(
        "rm -rf " not in museum_preflight,
        "Museum preflight must fail safely instead of deleting learner work",
    )
    for language in LANGUAGES:
        require(
            f"cd start-museum/{language}" in museum_preflight,
            f"Museum preflight must change into the {language} starter directory",
        )
    require(
        "git checkout -- ." in museum_preflight,
        "Museum preflight must explain how to restore a clean starter",
    )
    require(
        "git status" in museum_preflight,
        "Museum preflight must tell learners their in-place edits appear in git status",
    )
    require(
        "cp finished/" not in museum_preflight
        and "mkdir -p tests" not in museum_preflight,
        "Museum preflight must not reconstruct projects or create test directories",
    )
    require(
        "Museum Exhibit Studio starter" in museum_preflight,
        "Museum preflight must state the starter identity output learners should see",
    )


def validate_editor_open_guidance() -> None:
    # Both tracks hand the learner exactly one starter directory and expect them to live in it for
    # the whole workshop. Every per-language render has to name that folder and mention `code .`
    # next to it, so the "open this folder in your editor" step cannot quietly vanish from one
    # block. Opening an editor is a convenience, so this asserts the inline mention rather than a
    # fenced command the learner is expected to run.
    fence = "`code .`"
    for lesson_name, starter_root in (
        ("00-preflight.md", "start-accessibility"),
        ("museum-00-preflight.md", "start-museum"),
    ):
        for language in LANGUAGES:
            rendered = render_language_markdown(WORKSHOP / lesson_name, language)
            starter_directory = f"{starter_root}/{language}"
            change_directory = rendered.find(f"cd {starter_directory}")
            require(
                change_directory >= 0,
                f"workshop/{lesson_name} ({language}) must change into {starter_directory}",
            )
            if change_directory < 0:
                continue
            guidance = rendered[change_directory:]
            fence_position = guidance.find(fence)
            require(
                fence_position >= 0,
                f"workshop/{lesson_name} ({language}) must show `code .` after changing into "
                f"{starter_directory} so the learner opens that folder in an editor",
            )
            if fence_position < 0:
                continue
            neighborhood = guidance[
                max(0, fence_position - 400) : fence_position + len(fence) + 400
            ]
            require(
                starter_directory in neighborhood,
                f"workshop/{lesson_name} ({language}) must name {starter_directory} as the folder "
                "its `code .` command opens",
            )
            require(
                "editor" in neighborhood.casefold(),
                f"workshop/{lesson_name} ({language}) must tell the learner to open "
                f"{starter_directory} in an editor, not only run `code .`",
            )
    for starter_readme in (
        ROOT / "start-accessibility" / "README.md",
        ROOT / "start-museum" / "README.md",
    ):
        readme_text = read(starter_readme)
        require(
            "code ." in readme_text and "editor" in readme_text.casefold(),
            f"{starter_readme.relative_to(ROOT)} must tell learners to open the starter directory "
            "in an editor",
        )


def validate_museum_permission_handlers() -> None:
    # Every museum session configuration has to answer permission requests. Without a handler the
    # runtime leaves each request pending instead of denying it, so a learner's Step 1 run stalls
    # and never prints an exhibit. Assert the per-language SDK member rather than any prose.
    for lesson_name in MUSEUM_SESSION_CONFIGURATION_LESSONS:
        for language in LANGUAGES:
            rendered = museum_tokens(render_language_markdown(WORKSHOP / lesson_name, language))
            require(
                re.search(MUSEUM_ANY_PERMISSION_HANDLER[language], rendered) is not None,
                f"workshop/{lesson_name} ({language}) builds a session without a permission "
                "handler; the runtime leaves permission requests pending and the run stalls",
            )

    # Any other museum lesson that starts creating sessions has to join the list above rather than
    # quietly shipping a handler-less session.
    for lesson_name in MUSEUM_LESSONS:
        if lesson_name in MUSEUM_SESSION_CONFIGURATION_LESSONS or lesson_name.endswith(
            "00-preflight.md"
        ):
            continue
        for language in LANGUAGES:
            rendered = museum_tokens(render_language_markdown(WORKSHOP / lesson_name, language))
            require(
                re.search(MUSEUM_SESSION_CREATION[language], rendered) is None,
                f"workshop/{lesson_name} ({language}) creates a session but is not listed in "
                "MUSEUM_SESSION_CONFIGURATION_LESSONS, so its permission handler is unchecked",
            )

    # The finished apps run the same generation session the lessons build, so they need the same
    # approve-all handler. The scoped research and HTML handlers are checked elsewhere.
    for language in LANGUAGES:
        finished = ROOT / "finished" / language / "museum-exhibit-studio"
        entrypoint = museum_tokens(read(finished / MUSEUM_ENTRYPOINTS[language]))
        require(
            re.search(MUSEUM_APPROVE_ALL_PERMISSION_HANDLER[language], entrypoint) is not None,
            f"{finished.relative_to(ROOT)} does not set the approve-all permission handler on the "
            "exhibit generation session, so the finished app stalls on the first request",
        )


def rust_lesson_code_blocks(markdown_file: Path) -> list[str]:
    """Return the Rust fenced blocks a learner is told to type in one lesson."""
    rendered = render_language_markdown(markdown_file, "rust")
    return re.findall(r"^```rust\n(.*?)^```$", rendered, re.S | re.M)


def rust_result_error_type(returns: str) -> str | None:
    """Return the error half of a `Result<_, E>` return type, or None for anything else."""
    if not returns.startswith("Result<") or not returns.endswith(">"):
        return None
    inner = returns[len("Result<") : -1]
    depth = 0
    for index, character in enumerate(inner):
        if character == "<":
            depth += 1
        elif character == ">":
            depth -= 1
        elif character == "," and depth == 0:
            return inner[index + 1 :].strip()
    return None


def validate_museum_rust_error_types() -> None:
    # The museum lessons build on one pre-built helper crate, and every helper that can fail returns
    # its `RuntimeError` alias. Repository validation compiles the starter and the finished app but
    # never the code the lessons dictate, so a lesson is free to declare an error type no helper call
    # can convert into. Assert the declared type in each lesson signature against the alias the
    # helper actually exports.
    helper = read(ROOT / "start-museum" / "rust" / "src" / "lib.rs")
    require(
        MUSEUM_RUST_ERROR_ALIAS_DEFINITION in helper,
        "start-museum/rust/src/lib.rs must export "
        f"`{MUSEUM_RUST_ERROR_ALIAS_DEFINITION}` as the error type every helper returns",
    )
    for lesson_name in MUSEUM_LESSONS:
        blocks = rust_lesson_code_blocks(WORKSHOP / lesson_name)
        lesson_source = "\n".join(blocks)
        imported = {
            name.strip()
            for match in MUSEUM_RUST_CRATE_IMPORT.finditer(lesson_source)
            for name in ((match.group("names") or match.group("name") or "").split(","))
            if name.strip()
        }
        shows_crate_import = bool(imported)
        for block in blocks:
            for match in MUSEUM_RUST_ENTRYPOINT.finditer(block):
                returns = (match.group("returns") or "").strip()
                if not returns:
                    continue
                entrypoint = f"`fn {match.group('name')}`"
                require(
                    rust_result_error_type(returns) == MUSEUM_RUST_ERROR_ALIAS,
                    f"workshop/{lesson_name} (rust) declares {entrypoint} returning `{returns}`; "
                    f"the pre-built helpers return {MUSEUM_RUST_ERROR_ALIAS} "
                    "(Box<dyn Error + Send + Sync>), which no other boxed error type can absorb "
                    f"through `?`, so the error type must be {MUSEUM_RUST_ERROR_ALIAS}",
                )
                require(
                    not shows_crate_import or MUSEUM_RUST_ERROR_ALIAS in imported,
                    f"workshop/{lesson_name} (rust) uses {MUSEUM_RUST_ERROR_ALIAS} in {entrypoint} "
                    "but its museum_exhibit_studio import does not bring the name into scope",
                )


def validate_learn_more_sections() -> None:
    # Every lesson ends with a "Learn more" section so a learner can go deeper into the official
    # SDK documentation for that step. Assert the section and at least one link in every
    # per-language render, so the links cannot quietly end up inside a single language block and
    # leave the other five tracks with a heading and nothing under it. This checks structure only;
    # link targets are checked by validate_markdown_links.
    documentation_link = re.compile(r"\[[^\]]+\]\(https?://[^)]+\)")
    for lesson_name in LESSONS:
        lesson_path = WORKSHOP / lesson_name
        if not lesson_path.exists():
            continue
        require(
            "## Learn more" in read(lesson_path),
            f"workshop/{lesson_name} is missing its required '## Learn more' section",
        )
        for language in LANGUAGES:
            section = markdown_section(
                render_language_markdown(lesson_path, language), "## Learn more"
            )
            require(
                documentation_link.search(section) is not None,
                f"workshop/{lesson_name} ({language}) has no documentation link in its "
                "'## Learn more' section",
            )


SYSTEM_MESSAGE_MODE_EXPLAINER_LESSONS = ("01-first-session.md", "museum-03-curator-voice.md")
SYSTEM_MESSAGE_MODES = ("`append`", "`replace`", "`customize`")
PERMISSION_DECISION_EXPLAINER_LESSONS = ("04-mcp-safety.md", "museum-07-wikipedia-research.md")
PERMISSION_DECISION_KINDS = (
    "`approve-once`",
    "`reject`",
    "`user-not-available`",
    "`no-result`",
)


def validate_configuration_explainers() -> None:
    # Two things a learner never sees in the code are still decisions the application made: the
    # system message mode the session runs under, and which decision a permission handler returns.
    # Each track explains both exactly once, and those paragraphs are prose with no compiled
    # counterpart, so nothing else would notice them disappearing. Assert the mode and decision
    # names rather than any sentence, and assert them per rendered language so an explainer cannot
    # end up inside one language block and leave the other five tracks without it.
    for lesson_name in SYSTEM_MESSAGE_MODE_EXPLAINER_LESSONS:
        for language in LANGUAGES:
            rendered = render_language_markdown(WORKSHOP / lesson_name, language)
            for mode in SYSTEM_MESSAGE_MODES:
                require(
                    mode in rendered,
                    f"workshop/{lesson_name} ({language}) must name the {mode} system message "
                    "mode; the lesson explains which of the three modes the session runs under",
                )

    for lesson_name in PERMISSION_DECISION_EXPLAINER_LESSONS:
        for language in LANGUAGES:
            rendered = render_language_markdown(WORKSHOP / lesson_name, language)
            for kind in PERMISSION_DECISION_KINDS:
                require(
                    kind in rendered,
                    f"workshop/{lesson_name} ({language}) must name the {kind} permission "
                    "decision; this is where the learner first writes a real decision instead of "
                    "a blanket approve-all handler",
                )


def validate_workflows() -> None:
    required_setup = (
        ("actions/setup-dotnet@v6", "dotnet-version: 10.0.x"),
        ("actions/setup-node@v7", "node-version: 22"),
        ("actions/setup-python@v7", 'python-version: "3.11"'),
        ("actions/setup-go@v7", 'go-version: "1.24.x"'),
        ("dtolnay/rust-toolchain@stable", 'toolchain: "1.94.0"'),
        ("actions/setup-java@v6", 'java-version: "17"'),
        ("mvn --version", "bash scripts/validate-workshop.sh"),
    )
    validation_workflow = read(ROOT / ".github" / "workflows" / "validate.yml")
    for expected in required_setup:
        for value in expected:
            require(value in validation_workflow, f"validate.yml is missing required validation setup: {value}")

    deployment_workflow = read(ROOT / ".github" / "workflows" / "deploy.yml")
    for forbidden in (
        "actions/setup-dotnet",
        "actions/setup-node",
        "actions/setup-python",
        "actions/setup-go",
        "rust-toolchain",
        "actions/setup-java",
        "validate-workshop.sh",
    ):
        require(
            forbidden not in deployment_workflow,
            f"deploy.yml should publish the prevalidated site without running {forbidden}",
        )
    for required in (
        "Prepare deployment",
        "actions/configure-pages@v6",
        "actions/upload-pages-artifact@v5",
        "actions/deploy-pages@v5",
    ):
        require(required in deployment_workflow, f"deploy.yml is missing deployment step: {required}")


validate_language_registry()
for lesson in LESSONS:
    lesson_path = WORKSHOP / lesson
    require(lesson_path.exists(), f"Missing lesson {lesson}")
    if lesson_path.exists():
        validate_language_directives(lesson_path)
        validate_shared_language_content(lesson_path)
        validate_rendered_language_content(lesson_path)
        for section in ("## Run it", "## Check your understanding"):
            if lesson not in {"00-preflight.md", "museum-00-preflight.md"}:
                require(section in read(lesson_path), f"{lesson} is missing required section: {section}")
validate_layout()
validate_museum_projects()
validate_python_dependencies()
validate_security_invariants()
validate_playwright_output_configuration()
validate_project_behavior()
validate_site_behavior()
validate_documentation()
validate_editor_open_guidance()
validate_museum_permission_handlers()
validate_museum_rust_error_types()
validate_learn_more_sections()
validate_configuration_explainers()
validate_workflows()

if errors:
    print("Workshop validation failed:")
    for error in errors:
        print(f"- {error}")
    sys.exit(1)

print(
    f"Workshop content validation passed: {len(LANGUAGES)} languages, "
    f"{len(SDLC_LESSONS)} SDLC lessons, {len(MUSEUM_LESSONS)} museum lessons, "
    "all repository projects, and local site assets."
)
