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
    "museum-01-curator-role.md",
    "museum-02-tool-free-session.md",
    "museum-03-approved-facts.md",
    "museum-04-deterministic-validation.md",
    "museum-05-lifecycle-tests.md",
    "museum-06-run-review.md",
    "museum-07-wikipedia-grounding.md",
)
LESSONS = SDLC_LESSONS + MUSEUM_LESSONS
CHECKPOINTS = (
    "01-first-session",
    "02-streaming",
    "03-local-tool",
    "04-mcp-safety",
    "05-combine-tools",
    "06-structured-report",
)
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
SOURCE_FILES = {
    "dotnet": "Program.cs",
    "nodejs": "src/workshop.ts",
    "python": "workshop.py",
    "go": "main.go",
    "rust": "src/main.rs",
    "java": "src/main/java/workshop/AccessibilityReport.java",
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
        "workshop-app/Program.cs",
        "workshop-app/Helpers/",
        "dotnet run",
        "```csharp",
        "checkpoints/dotnet/",
        "samples/dotnet/",
    ),
    "nodejs": (
        "workshop-app/src/index.ts",
        "workshop-app/src/workshop.ts",
        "npm --prefix workshop-app",
        "```typescript",
        "checkpoints/nodejs/",
        "samples/nodejs/",
    ),
    "python": (
        "workshop-app/main.py",
        "workshop-app/workshop.py",
        "python workshop-app/main.py",
        "```python",
        "checkpoints/python/",
        "samples/python/",
    ),
    "go": (
        "workshop-app/main.go",
        "go -C workshop-app",
        "```go",
        "checkpoints/go/",
        "samples/go/",
    ),
    "rust": (
        "workshop-app/src/main.rs",
        "cargo run --manifest-path workshop-app/Cargo.toml",
        "```rust",
        "checkpoints/rust/",
        "samples/rust/",
    ),
    "java": (
        "workshop-app/src/main/java/",
        "mvn -f workshop-app/pom.xml",
        "```java",
        "checkpoints/java/",
        "samples/java/",
    ),
}
STEP_3_TRACK_MARKERS = {
    "dotnet": ("AccessibilityRuleCatalog.cs", "CopilotTool.DefineTool", "dotnet run --project workshop-app"),
    "nodejs": ("src/workshop.ts", 'defineTool("accessibility_rule_lookup"', "npm --prefix workshop-app start"),
    "python": ("workshop.py", '@define_tool(', "python workshop-app/main.py"),
    "go": ("main.go", "copilot.DefineTool(", "go -C workshop-app run ."),
    "rust": ("src/main.rs", 'Tool::new("accessibility_rule_lookup")', "cargo run --manifest-path workshop-app/Cargo.toml"),
    "java": ("AccessibilityReport.java", "ToolDefinition.from(", "mvn -f workshop-app/pom.xml compile exec:java"),
}
RUN_COMMAND_MARKERS = {
    "dotnet": "dotnet run --project workshop-app",
    "nodejs": "npm --prefix workshop-app start",
    "python": "python workshop-app/main.py",
    "go": "go -C workshop-app run .",
    "rust": "cargo run --manifest-path workshop-app/Cargo.toml",
    "java": "mvn -f workshop-app/pom.xml compile exec:java",
}
STEP_9_RUN_COMMAND_MARKERS = {
    "dotnet": "cd workshop-app && dotnet run",
    "nodejs": "npm --prefix workshop-app start",
    "python": "cd workshop-app && python main.py",
    "go": "go -C workshop-app run .",
    "rust": "cd workshop-app && cargo run --",
    "java": "cd workshop-app && mvn compile exec:java",
}
MUSEUM_COMMAND_MARKERS = {
    "dotnet": (
        "dotnet build museum-workshop-app",
        "dotnet test museum-workshop-app/",
        "dotnet run --project museum-workshop-app",
    ),
    "nodejs": (
        "npm --prefix museum-workshop-app run build",
        "npm --prefix museum-workshop-app test",
        "npm --prefix museum-workshop-app start",
    ),
    "python": (
        "museum-workshop-app/.venv/bin/python",
        "python3 -m py_compile museum-workshop-app/",
        "python3 -m unittest",
        "python -m unittest",
        "python3 museum-workshop-app/main.py",
    ),
    "go": (
        "go -C museum-workshop-app test",
        "go -C museum-workshop-app run .",
    ),
    "rust": (
        "cargo check --manifest-path museum-workshop-app/Cargo.toml",
        "cargo test --manifest-path museum-workshop-app/Cargo.toml",
        "cargo run --manifest-path museum-workshop-app/Cargo.toml",
    ),
    "java": (
        "mvn -f museum-workshop-app/pom.xml test",
        "mvn -f museum-workshop-app/pom.xml -Dtest=",
        "mvn -f museum-workshop-app/pom.xml compile exec:java",
    ),
}
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
        "nodejs": "workshop-app/src/index.ts",
        "python": "workshop-app/main.py",
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
    "museum-01-curator-role.md": {
        "dotnet": "public const string SystemMessage",
        "nodejs": "export const systemMessage",
        "python": "SYSTEM_MESSAGE =",
        "go": "curatorSystemMessage =",
        "rust": "pub const SYSTEM_MESSAGE",
        "java": "public static final String SYSTEM_MESSAGE",
    },
    "museum-02-tool-free-session.md": {
        "dotnet": "AvailableTools = []",
        "nodejs": "availableTools: []",
        "python": '"available_tools": []',
        "go": "AvailableTools: []string{}",
        "rust": "config.available_tools = Some(Vec::new())",
        "java": ".setAvailableTools(List.of())",
    },
    "museum-03-approved-facts.md": {
        "dotnet": "BuildExhibitPrompt",
        "nodejs": "buildExhibitPrompt",
        "python": "build_exhibit_prompt",
        "go": "buildExhibitPrompt",
        "rust": "build_exhibit_prompt",
        "java": "buildExhibitPrompt",
    },
    "museum-04-deterministic-validation.md": {
        "dotnet": "ExhibitValidator.Validate",
        "nodejs": "validateExhibit",
        "python": "validate_exhibit",
        "go": "validateExhibit",
        "rust": "validate_exhibit",
        "java": "ExhibitValidator.validate",
    },
    "museum-05-lifecycle-tests.md": {
        "dotnet": "GenerateAsync",
        "nodejs": "async generate(",
        "python": "async def generate(",
        "go": "func (service museumExhibitService) Generate(",
        "rust": "pub async fn generate_exhibit(",
        "java": "GeneratedExhibit generate(",
    },
    "museum-06-run-review.md": {
        "dotnet": "new CopilotCuratorClient()",
        "nodejs": "createCopilotCuratorClient()",
        "python": "MuseumExhibitService(CopilotClient())",
        "go": "newCopilotCuratorClient()",
        "rust": "CopilotCuratorClient::new()",
        "java": "new CopilotCuratorClient()",
    },
}
UNSCOPED_TRACK_MARKERS = (
    "workshop-app/Program.cs",
    "workshop-app/Helpers/",
    "workshop-app/src/index.ts",
    "workshop-app/src/workshop.ts",
    "workshop-app/main.py",
    "workshop-app/workshop.py",
    "workshop-app/main.go",
    "workshop-app/src/main.rs",
    "workshop-app/src/main/java/",
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
            if not streaming or label != Path("samples/java/hello-copilot-sdk")
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
    require("CHECKPOINT_STAGE" not in text and "checkpointStage" not in text,
            f"{label} relies on a cosmetic checkpoint label instead of executable behavior")

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
                f"checkpoints/{selected_language}/03-local-tool",
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
        for directory in [ROOT / "start" / language, ROOT / "samples" / language / "hello-copilot-sdk", ROOT / "samples" / language / "accessibility-report"]:
            require(directory.is_dir(), f"Missing {language} project directory {directory.relative_to(ROOT)}")
            require(has_manifest(directory, language), f"Missing {language} manifest in {directory.relative_to(ROOT)}")
            require((directory / entrypoint_path(directory, language)).exists(),
                    f"Missing {language} executable entrypoint in {directory.relative_to(ROOT)}")
        for checkpoint in CHECKPOINTS:
            directory = ROOT / "checkpoints" / language / checkpoint
            require(directory.is_dir(), f"Missing {language} checkpoint {checkpoint}")
            require(has_manifest(directory, language), f"Missing {language} manifest in {directory.relative_to(ROOT)}")
            require((directory / SOURCE_FILES[language]).exists(), f"Missing {language} source in {directory.relative_to(ROOT)}")
            require((directory / ENTRYPOINTS[language]).exists(),
                    f"Missing {language} executable entrypoint in {directory.relative_to(ROOT)}")
    for language in ("nodejs", "go", "rust"):
        for directory in [ROOT / "start" / language, *(ROOT / "samples" / language / sample for sample in ("hello-copilot-sdk", "accessibility-report")), *(ROOT / "checkpoints" / language / checkpoint for checkpoint in CHECKPOINTS)]:
            lock = {"nodejs": "package-lock.json", "go": "go.sum", "rust": "Cargo.lock"}[language]
            require((directory / lock).exists(), f"Missing deterministic {language} lock file in {directory.relative_to(ROOT)}")


def validate_python_dependencies() -> None:
    directories = [
        ROOT / "start" / "python",
        *(ROOT / "samples" / "python" / sample for sample in ("hello-copilot-sdk", "accessibility-report")),
        *(ROOT / "checkpoints" / "python" / checkpoint for checkpoint in CHECKPOINTS),
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
        directories = [
            ROOT / "checkpoints" / language / checkpoint
            for checkpoint in CHECKPOINTS[3:]
        ] + [ROOT / "samples" / language / "accessibility-report"]
        for directory in directories:
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
        *(ROOT / "start" / language for language in LANGUAGES),
        *(ROOT / "samples" / language / "accessibility-report" for language in LANGUAGES),
        *(ROOT / "checkpoints" / language / checkpoint for language in LANGUAGES for checkpoint in CHECKPOINTS),
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


def validate_checkpoint_progression() -> None:
    for language in LANGUAGES:
        executable_hashes: set[str] = set()
        starter = ROOT / "start" / language
        require((starter / ENTRYPOINTS[language]).exists(),
                f"Missing {language} starter executable {ENTRYPOINTS[language]}")
        validate_executable_stage(language, "starter", starter)
        for checkpoint in CHECKPOINTS:
            directory = ROOT / "checkpoints" / language / checkpoint
            text = validate_executable_stage(language, checkpoint, directory)
            executable_hashes.add(text)
            if language == "nodejs":
                package = read(directory / "package.json")
                require('"start": "tsx src/index.ts"' in package, f"{directory.relative_to(ROOT)} start script bypasses its checkpoint entrypoint")
                require("Continue with Step 1" not in text, f"{directory.relative_to(ROOT)} has a placeholder entrypoint")
            if language == "python":
                if checkpoint == "06-structured-report":
                    report = read(directory / "report.py")
                    require("case SessionErrorData(message=message): raise" not in report,
                            f"{directory.relative_to(ROOT)} raises from an event callback instead of completing the wait")
                    require("error: RuntimeError | None = None" in report and "done.set()" in report,
                            f"{directory.relative_to(ROOT)} does not propagate session errors to the awaited flow")
                    require('if __name__ == "__main__":' in report,
                            f"{directory.relative_to(ROOT)} runs interactive code when imported")
                else:
                    require(not (directory / "report.py").exists(),
                            f"{directory.relative_to(ROOT)} includes a misleading completed reporter before Step 6")
            if language == "java":
                pom = read(directory / "pom.xml")
                require("<mainClass>workshop.AccessibilityReport</mainClass>" in pom,
                        f"{directory.relative_to(ROOT)} does not configure mvn exec:java")
        require(
            len(executable_hashes) == len(CHECKPOINTS),
            f"{language} checkpoints have identical executable behavior; each checkpoint must demonstrate its named stage",
        )

    hello_sample_stages = {
        "dotnet": "03-local-tool",
        "nodejs": "03-local-tool",
        "python": "03-local-tool",
        "go": "03-local-tool",
        "rust": "03-local-tool",
        "java": "03-local-tool",
    }
    for language, stage in hello_sample_stages.items():
        directory = ROOT / "samples" / language / "hello-copilot-sdk"
        require(stage == "03-local-tool", f"{directory.relative_to(ROOT)} is not pinned to Step 3 local-tool")
        validate_hello_sample(language, directory)

    for language, stage, directory in (
        ("go", "06-structured-report", ROOT / "samples" / "go" / "accessibility-report"),
        ("rust", "06-structured-report", ROOT / "samples" / "rust" / "accessibility-report"),
        ("java", "06-structured-report", ROOT / "samples" / "java" / "accessibility-report"),
    ):
        text = executable_source(directory, language)
        validate_runtime_flow(language, stage, runtime_source(directory, language, text), directory.relative_to(ROOT))
    for directory in (ROOT / "samples" / "python" / "accessibility-report",):
        validate_runtime_flow(
            "python",
            "06-structured-report",
            read(directory / "report.py"),
            directory.relative_to(ROOT),
        )

    node_report_package = read(ROOT / "samples" / "nodejs" / "accessibility-report" / "package.json")
    require('"start": "tsx src/report.ts"' in node_report_package,
            "Node accessibility-report npm start must execute src/report.ts")
    for directory in [ROOT / "start" / "nodejs", *(ROOT / "checkpoints" / "nodejs" / checkpoint for checkpoint in CHECKPOINTS), ROOT / "samples" / "nodejs" / "accessibility-report"]:
        source = read(directory / "src" / "workshop.ts")
        require("const existingSnapshots = safeSnapshotNames(outputDirectory)" in source,
                f"{directory.relative_to(ROOT)} captures snapshot baseline lazily")
        require("const baseline = await existingSnapshots" in source,
                f"{directory.relative_to(ROOT)} does not await the construction-time snapshot baseline")
    for directory in [ROOT / "start" / "python", *(ROOT / "checkpoints" / "python" / checkpoint for checkpoint in CHECKPOINTS), *(ROOT / "samples" / "python" / sample for sample in ("hello-copilot-sdk", "accessibility-report"))]:
        report_path = directory / "report.py"
        if report_path.exists():
            require('if __name__ == "__main__":' in read(report_path),
                    f"{directory.relative_to(ROOT)} report entrypoint cannot be imported safely")
    for directory in [ROOT / "start" / "java", *(ROOT / "checkpoints" / "java" / checkpoint for checkpoint in CHECKPOINTS), *(ROOT / "samples" / "java" / sample for sample in ("hello-copilot-sdk", "accessibility-report"))]:
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
    for markdown in [ROOT / "README.md", ROOT / "start" / "README.md", ROOT / "checkpoints" / "README.md", *WORKSHOP.glob("*.md")]:
        validate_markdown_links(markdown)
    published = "\n".join(read(path) for path in [ROOT / "README.md", *WORKSHOP.glob("*.md"), *DOCS.rglob("*.html")])
    for forbidden in ("jamesmontemagno.github.io", "codemillmatt.github.io", "](../start/", "](../samples/"):
        require(forbidden not in published, f"Published content contains forbidden pattern: {forbidden}")
    for url in OFFICIAL_SDK_URLS.values():
        require(url in read(ROOT / "README.md"), f"README is missing official SDK link {url}")
    require("https://github.com/github/copilot-sdk/tree/main/cookbook" in read(ROOT / "README.md"), "README is missing the official cookbook link")
    all_markdown = "\n".join(read(path) for path in [ROOT / "README.md", ROOT / "start" / "README.md", ROOT / "checkpoints" / "README.md", *WORKSHOP.glob("*.md")])
    require("go run ./samples/" not in all_markdown and "go run samples/" not in all_markdown,
            "Documentation runs Go modules from the repository root instead of their module directory")
    starters = read(ROOT / "start" / "README.md")
    require("cd workshop-app && go build -mod=readonly ./..." in starters,
            "Starter documentation must build Go modules with the lock enforced")
    checkpoints = read(ROOT / "checkpoints" / "README.md")
    require("go test -mod=readonly ./..." in checkpoints,
            "Checkpoint documentation must test Go modules with the lock enforced")
    require("python -m pip install -r requirements.txt" in starters,
            "Starter documentation must install the pinned Python requirements")
    require("python report.py" not in all_markdown,
            "Documentation must invoke Python checkpoint main.py rather than an unwired report.py")
    for lesson in ("01-first-session.md", "05-combine-tools.md", "06-structured-report.md"):
        require("python workshop-app/main.py" in read(WORKSHOP / lesson),
                f"{lesson} must run the Python checkpoint through main.py")

    lesson_viewer = read(DOCS / "workshop" / "step.html")
    for step_id in (
        "09-interactive-html-report",
        "museum-00-preflight",
        "museum-01-curator-role",
        "museum-02-tool-free-session",
        "museum-03-approved-facts",
        "museum-04-deterministic-validation",
        "museum-05-lifecycle-tests",
        "museum-06-run-review",
        "museum-07-wikipedia-grounding",
    ):
        require(
            f"id: '{step_id}'" in lesson_viewer,
            f"Lesson viewer navigation is missing {step_id}",
        )

    wikipedia_lesson = read(WORKSHOP / "museum-07-wikipedia-grounding.md")
    for required_step in (
        "# Wikipedia MCP",
        "## 1. Choose one Wikipedia MCP server",
        "## 2. Add a separate research contract",
        "## 3. Create the research session",
        "## 4. Implement bounded research",
        "## 5. Add the approval gate",
        "## 6. Test with a mock MCP server",
        '"wikipedia-search"',
        '"wikipedia-readArticle"',
        "The original generation configuration still has an empty tool allowlist.",
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
        "id: 'museum-07-wikipedia-grounding'" in lesson_viewer
        and "title: 'Wikipedia MCP',\n                navTitle: 'Wikipedia MCP'" in lesson_viewer
        and "kind: 'core',\n                number: 7,\n                time: '30 min'" in lesson_viewer,
        "Wikipedia MCP must be registered as required 30-minute museum step 7",
    )
    landing_page = read(DOCS / "index.html")
    require(
        "Non-SDLC tool · 105 minutes" in landing_page
        and "105 minutes for Museum Exhibit Studio" in read(ROOT / "README.md"),
        "Museum workshop duration must include all 105 timed minutes",
    )

    museum_preflight = read(WORKSHOP / "museum-00-preflight.md")
    for clean_clone_step in (
        "git clone https://github.com/jamesmontemagno/copilot-sdk-workshop.git",
        'test "$(git rev-parse --show-toplevel)" = "$PWD"',
        'test -z "$(git status --short)"',
        "test ! -e museum-workshop-app",
    ):
        require(
            clean_clone_step in museum_preflight,
            f"Museum preflight is missing clean-clone guidance: {clean_clone_step}",
        )
    require(
        "rm -rf museum-workshop-app" not in museum_preflight,
        "Museum preflight must fail safely instead of deleting an existing learner project",
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
validate_python_dependencies()
validate_security_invariants()
validate_playwright_output_configuration()
validate_checkpoint_progression()
validate_site_behavior()
validate_documentation()
validate_workflows()

if errors:
    print("Workshop validation failed:")
    for error in errors:
        print(f"- {error}")
    sys.exit(1)

print(
    f"Workshop content validation passed: {len(LANGUAGES)} languages, "
    f"{len(SDLC_LESSONS)} SDLC lessons, {len(MUSEUM_LESSONS)} museum lessons, "
    f"{len(CHECKPOINTS)} checkpoints per language, "
    "and local site assets."
)
