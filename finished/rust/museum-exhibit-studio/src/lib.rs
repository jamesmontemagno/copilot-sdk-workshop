use std::error::Error;
use std::fmt;
use std::future::{Future, poll_fn};
use std::io::{self, Write};
use std::path::{Component, Path, PathBuf};
use std::pin::Pin;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::{Arc, Mutex};
use std::task::{Context, Poll, Waker};
use std::thread;
use std::time::Duration;

use async_trait::async_trait;
use github_copilot_sdk::handler::{PermissionHandler, PermissionResult};
use github_copilot_sdk::session::Session;
use github_copilot_sdk::tool::ToolHandler;
use github_copilot_sdk::types::{
    McpServerConfig, McpStdioServerConfig, MessageOptions, PermissionRequestData,
    PermissionRequestKind, RequestId, SessionEvent, SessionId, Tool, ToolInvocation,
};
use github_copilot_sdk::{Error as SdkError, ToolResult};

pub const MAXIMUM_FACT_COUNT: usize = 20;
pub const MAXIMUM_FACT_LENGTH: usize = 500;
pub const GENERATION_TIMEOUT: Duration = Duration::from_secs(120);
pub const RESEARCH_TIMEOUT: Duration = Duration::from_secs(90);
pub const WIKIPEDIA_TOOLS: [&str; 2] = ["wikipedia-search", "wikipedia-readArticle"];
pub const EXHIBIT_FILE_NAME: &str = "exhibit.html";
pub const APPROVED_FACT_LOOKUP_NAME: &str = "approved_fact_lookup";

pub const APOLLO_11_FACTS: [&str; 5] = [
    "Apollo 11 launched July 16, 1969.",
    "It landed on the Moon July 20, 1969.",
    "Neil Armstrong and Buzz Aldrin walked on the Moon.",
    "Michael Collins remained in lunar orbit.",
    "The mission returned to Earth July 24, 1969.",
];

pub const GREAT_BARRIER_REEF_FACTS: [&str; 5] = [
    "The Great Barrier Reef lies off the coast of Queensland, Australia.",
    "It stretches for about 2,300 kilometres.",
    "It is made up of more than 2,900 individual reefs.",
    "It was added to the UNESCO World Heritage List in 1981.",
    "Rising sea temperatures have caused repeated coral bleaching events.",
];

pub const TERRACOTTA_ARMY_FACTS: [&str; 5] = [
    "The Terracotta Army was buried near the tomb of China's first emperor, Qin Shi Huang.",
    "Farmers digging a well discovered the site in 1974.",
    "The pits contain thousands of life-sized clay soldiers.",
    "Each figure was assembled from moulded parts and finished by hand.",
    "The site sits near the modern city of Xi'an in Shaanxi Province.",
];

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct FactSet {
    pub key: &'static str,
    pub label: &'static str,
    pub facts: &'static [&'static str],
}

const FACT_SETS: [FactSet; 3] = [
    FactSet {
        key: "apollo11",
        label: "Apollo 11",
        facts: &APOLLO_11_FACTS,
    },
    FactSet {
        key: "reef",
        label: "Great Barrier Reef",
        facts: &GREAT_BARRIER_REEF_FACTS,
    },
    FactSet {
        key: "terracotta",
        label: "Terracotta Army",
        facts: &TERRACOTTA_ARMY_FACTS,
    },
];

pub fn fact_sets() -> &'static [FactSet] {
    &FACT_SETS
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FactBoundsError(String);

impl fmt::Display for FactBoundsError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str(&self.0)
    }
}

impl Error for FactBoundsError {}

pub fn bound_facts<I, S>(facts: I) -> Result<Vec<String>, FactBoundsError>
where
    I: IntoIterator<Item = S>,
    S: AsRef<str>,
{
    let facts = facts
        .into_iter()
        .map(|fact| fact.as_ref().trim().to_owned())
        .filter(|fact| !fact.is_empty())
        .collect::<Vec<_>>();

    if facts.is_empty() {
        return Err(FactBoundsError(
            "Provide at least one approved fact.".to_owned(),
        ));
    }
    if facts.len() > MAXIMUM_FACT_COUNT {
        return Err(FactBoundsError(format!(
            "Provide no more than {MAXIMUM_FACT_COUNT} approved facts."
        )));
    }
    if facts
        .iter()
        .any(|fact| fact.chars().count() > MAXIMUM_FACT_LENGTH)
    {
        return Err(FactBoundsError(format!(
            "Each approved fact must be {MAXIMUM_FACT_LENGTH} characters or fewer."
        )));
    }

    Ok(facts)
}

struct ApprovedFactLookup {
    facts: Vec<String>,
}

#[async_trait]
impl ToolHandler for ApprovedFactLookup {
    async fn call(&self, _invocation: ToolInvocation) -> Result<ToolResult, SdkError> {
        Ok(ToolResult::Text(
            serde_json::to_string(&self.facts).expect("approved facts serialize"),
        ))
    }
}

/// The application owns the approved facts. This tool is the only way the curator can read them.
pub fn approved_fact_lookup<I, S>(facts: I) -> Result<Tool, FactBoundsError>
where
    I: IntoIterator<Item = S>,
    S: AsRef<str>,
{
    let facts = bound_facts(facts)?;
    Ok(Tool::new(APPROVED_FACT_LOOKUP_NAME)
        .with_description(
            "Returns the complete list of educator-approved facts this application holds for the current exhibit.",
        )
        .with_parameters(
            serde_json::json!({"type": "object", "properties": {}, "additionalProperties": false}),
        )
        .with_skip_permission(true)
        .with_handler(Arc::new(ApprovedFactLookup { facts })))
}

pub type RuntimeError = Box<dyn Error + Send + Sync>;

#[derive(Debug)]
struct StudioError(String);

impl StudioError {
    fn new(message: impl Into<String>) -> Self {
        Self(message.into())
    }
}

impl fmt::Display for StudioError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str(&self.0)
    }
}

impl Error for StudioError {}

struct Deadline {
    expired: Arc<AtomicBool>,
    waker: Arc<Mutex<Option<Waker>>>,
}

impl Deadline {
    fn new(duration: Duration) -> Self {
        let expired = Arc::new(AtomicBool::new(false));
        let waker = Arc::new(Mutex::new(None::<Waker>));
        let thread_expired = Arc::clone(&expired);
        let thread_waker = Arc::clone(&waker);
        thread::spawn(move || {
            thread::sleep(duration);
            thread_expired.store(true, Ordering::SeqCst);
            if let Ok(mut waker) = thread_waker.lock() {
                if let Some(waker) = waker.take() {
                    waker.wake();
                }
            }
        });
        Self { expired, waker }
    }
}

impl Future for Deadline {
    type Output = ();

    fn poll(self: Pin<&mut Self>, cx: &mut Context<'_>) -> Poll<Self::Output> {
        if self.expired.load(Ordering::SeqCst) {
            return Poll::Ready(());
        }
        if let Ok(mut waker) = self.waker.lock() {
            *waker = Some(cx.waker().clone());
        }
        if self.expired.load(Ordering::SeqCst) {
            Poll::Ready(())
        } else {
            Poll::Pending
        }
    }
}

enum StreamOutcome {
    Sent(Result<(), RuntimeError>),
    Event(Result<SessionEvent, RuntimeError>),
    Timeout,
}

pub async fn stream_exhibit(
    session: &Session,
    prompt: impl Into<String>,
    timeout: Duration,
) -> Result<String, RuntimeError> {
    let mut events = session.subscribe();
    let mut send = Box::pin(session.send(MessageOptions::new(prompt.into())));
    let mut receive = Box::pin(events.recv());
    let mut deadline = Box::pin(Deadline::new(timeout));
    let mut sent = false;
    let mut idle = false;
    let mut received_delta = false;
    let mut content = String::new();

    while !sent || !idle {
        let outcome = poll_fn(|cx| {
            if !sent {
                if let Poll::Ready(result) = Future::poll(send.as_mut(), cx) {
                    return Poll::Ready(StreamOutcome::Sent(
                        result
                            .map(|_| ())
                            .map_err(|error| Box::new(error) as RuntimeError),
                    ));
                }
            }
            if let Poll::Ready(result) = Future::poll(receive.as_mut(), cx) {
                return Poll::Ready(StreamOutcome::Event(
                    result.map_err(|error| Box::new(error) as RuntimeError),
                ));
            }
            if let Poll::Ready(()) = Future::poll(deadline.as_mut(), cx) {
                return Poll::Ready(StreamOutcome::Timeout);
            }
            Poll::Pending
        })
        .await;

        match outcome {
            StreamOutcome::Sent(result) => {
                result?;
                sent = true;
            }
            StreamOutcome::Event(result) => {
                drop(receive);
                let event = result?;
                match event.event_type.as_str() {
                    "assistant.message_delta" => {
                        if let Some(delta) = event
                            .data
                            .get("deltaContent")
                            .and_then(|value| value.as_str())
                        {
                            received_delta = true;
                            content.push_str(delta);
                            print!("{delta}");
                            io::stdout().flush()?;
                        }
                    }
                    "assistant.message" if !received_delta => {
                        if let Some(message) =
                            event.data.get("content").and_then(|value| value.as_str())
                        {
                            content.push_str(message);
                            print!("{message}");
                            io::stdout().flush()?;
                        }
                    }
                    "tool.execution_start" => {
                        let tool_name = event
                            .data
                            .get("toolName")
                            .and_then(|value| value.as_str())
                            .unwrap_or("unknown");
                        println!("\n[tool:start] {tool_name}");
                    }
                    "tool.execution_complete" => {
                        let success = event
                            .data
                            .get("success")
                            .and_then(|value| value.as_bool())
                            .unwrap_or(false);
                        println!("[tool:done] success={success}");
                    }
                    "session.error" => {
                        let message = event
                            .data
                            .get("message")
                            .and_then(|value| value.as_str())
                            .unwrap_or("Copilot session failed");
                        return Err(Box::new(StudioError::new(message.to_owned())));
                    }
                    "session.idle" => {
                        println!();
                        idle = true;
                    }
                    _ => {}
                }
                receive = Box::pin(events.recv());
            }
            StreamOutcome::Timeout => {
                return Err(Box::new(io::Error::new(
                    io::ErrorKind::TimedOut,
                    "timeout while waiting for the curator",
                )));
            }
        }
    }

    Ok(content)
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct TitleValidation {
    pub title_count: usize,
    pub present: bool,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct NarrativeValidation {
    pub present: bool,
    pub word_count: usize,
    pub within_limit: bool,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct VisitorQuestionsValidation {
    pub present: bool,
    pub question_count: usize,
    pub exactly_three: bool,
    pub all_items_are_questions: bool,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct VocabularyValidation {
    pub prohibited_terms: Vec<&'static str>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ExhibitValidation {
    pub title: TitleValidation,
    pub narrative: NarrativeValidation,
    pub visitor_questions: VisitorQuestionsValidation,
    pub vocabulary: VocabularyValidation,
    pub errors: Vec<String>,
    pub valid: bool,
}

const PROHIBITED_VOCABULARY: [&str; 5] = [
    "software",
    "codebase",
    "repository",
    "terminal",
    "GitHub Copilot",
];

pub fn validate_exhibit(content: &str) -> ExhibitValidation {
    let normalized = content.replace("\r\n", "\n").replace('\r', "\n");
    let lines = normalized.lines().collect::<Vec<_>>();
    let title_count = lines
        .iter()
        .filter(|line| {
            line.strip_prefix("# ")
                .is_some_and(|title| !title.is_empty() && !title.starts_with('#'))
        })
        .count();
    let narrative_index = find_heading(&lines, "## Narrative");
    let questions_index = find_heading(&lines, "## Visitor questions");
    let narrative_text = match (narrative_index, questions_index) {
        (Some(start), Some(end)) if end > start => lines[start + 1..end].join(" "),
        _ => String::new(),
    };
    let narrative_word_count = count_words(&narrative_text);
    let questions = questions_index
        .map(|index| {
            lines[index + 1..]
                .iter()
                .filter_map(|line| numbered_item(line))
                .collect::<Vec<_>>()
        })
        .unwrap_or_default();
    let lower_content = normalized.to_lowercase();
    let prohibited_terms = PROHIBITED_VOCABULARY
        .iter()
        .copied()
        .filter(|term| lower_content.contains(&term.to_lowercase()))
        .collect::<Vec<_>>();

    let title = TitleValidation {
        title_count,
        present: title_count == 1,
    };
    let narrative = NarrativeValidation {
        present: narrative_index.is_some(),
        word_count: narrative_word_count,
        within_limit: (100..=140).contains(&narrative_word_count),
    };
    let visitor_questions = VisitorQuestionsValidation {
        present: questions_index.is_some(),
        question_count: questions.len(),
        exactly_three: questions.len() == 3,
        all_items_are_questions: !questions.is_empty()
            && questions.iter().all(|question| question.ends_with('?')),
    };
    let vocabulary = VocabularyValidation { prohibited_terms };
    let mut errors = Vec::new();

    if !title.present {
        errors.push("The exhibit must contain exactly one level-one title.".to_owned());
    }
    if !narrative.present {
        errors.push("The exhibit must contain a Narrative section.".to_owned());
    }
    if !narrative.within_limit {
        errors.push(format!(
            "The narrative must contain 100-140 words; found {narrative_word_count}."
        ));
    }
    if !visitor_questions.present {
        errors.push("The exhibit must contain a Visitor questions section.".to_owned());
    }
    if !visitor_questions.exactly_three {
        errors.push(format!(
            "The exhibit must contain exactly three numbered questions; found {}.",
            questions.len()
        ));
    }
    if !visitor_questions.all_items_are_questions {
        errors.push("Every numbered visitor item must end with a question mark.".to_owned());
    }
    if !vocabulary.prohibited_terms.is_empty() {
        errors.push(format!(
            "The exhibit contains prohibited vocabulary: {}.",
            vocabulary.prohibited_terms.join(", ")
        ));
    }

    let valid = errors.is_empty();
    ExhibitValidation {
        title,
        narrative,
        visitor_questions,
        vocabulary,
        errors,
        valid,
    }
}

pub fn format_validation(validation: &ExhibitValidation) -> String {
    let mut lines = Vec::new();
    lines.push(
        if validation.valid {
            "Structural checks passed."
        } else {
            "Structural checks found issues:"
        }
        .to_owned(),
    );
    lines.push(format!(
        "- One level-one title: {}",
        validation.title.present
    ));
    lines.push(format!(
        "- Narrative section: {}",
        validation.narrative.present
    ));
    lines.push(format!(
        "- Narrative length: {} words (within 100-140: {})",
        validation.narrative.word_count, validation.narrative.within_limit
    ));
    lines.push(format!(
        "- Visitor questions section: {}",
        validation.visitor_questions.present
    ));
    lines.push(format!(
        "- Numbered questions: {} (exactly three: {})",
        validation.visitor_questions.question_count, validation.visitor_questions.exactly_three
    ));
    lines.push(format!(
        "- Every item is a question: {}",
        validation.visitor_questions.all_items_are_questions
    ));
    if validation.vocabulary.prohibited_terms.is_empty() {
        lines.push("- Prohibited vocabulary: none".to_owned());
    } else {
        lines.push(format!(
            "- Prohibited vocabulary: {}",
            validation.vocabulary.prohibited_terms.join(", ")
        ));
    }
    for error in &validation.errors {
        lines.push(format!("  - {error}"));
    }
    lines.push(String::new());
    lines.push(
        "Structural checks do not prove factual grounding. Unsupported claims require human review or a separate evaluator."
            .to_owned(),
    );
    lines.join("\n")
}

fn find_heading(lines: &[&str], heading: &str) -> Option<usize> {
    lines
        .iter()
        .position(|line| line.trim().eq_ignore_ascii_case(heading))
}

fn numbered_item(line: &str) -> Option<&str> {
    let trimmed = line.trim_start();
    let digit_count = trimmed.chars().take_while(char::is_ascii_digit).count();
    if digit_count == 0 {
        return None;
    }
    let remainder = &trimmed[digit_count..];
    let remainder = remainder.strip_prefix('.')?;
    if !remainder.starts_with(char::is_whitespace) {
        return None;
    }
    let item = remainder.trim();
    (!item.is_empty()).then_some(item)
}

fn count_words(text: &str) -> usize {
    let chars = text.chars().collect::<Vec<_>>();
    let mut index = 0;
    let mut count = 0;
    while index < chars.len() {
        if chars[index].is_alphanumeric() {
            count += 1;
            index += 1;
            while index < chars.len() {
                if chars[index].is_alphanumeric() {
                    index += 1;
                } else if matches!(chars[index], '\'' | '’' | '-')
                    && index + 1 < chars.len()
                    && chars[index + 1].is_alphanumeric()
                {
                    index += 2;
                } else {
                    break;
                }
            }
        } else {
            index += 1;
        }
    }
    count
}

pub fn wikipedia_server() -> McpServerConfig {
    // Return the stdio server config object; callers place it in SessionConfig::mcp_servers under "wikipedia".
    McpServerConfig::Stdio(McpStdioServerConfig {
        command: "npx".to_owned(),
        args: vec!["-y".to_owned(), "wikipedia-mcp@1.0.3".to_owned()],
        working_directory: Some(
            std::env::current_dir()
                .map(|directory| directory.display().to_string())
                .unwrap_or_else(|_| ".".to_owned()),
        ),
        tools: Some(vec!["search".to_owned(), "readArticle".to_owned()]),
        ..Default::default()
    })
}

pub struct WikipediaPermissions;

pub fn wikipedia_permission_handler() -> WikipediaPermissions {
    WikipediaPermissions
}

#[derive(Debug, Default)]
struct PermissionPayload {
    kind: Option<String>,
    server_name: Option<String>,
    tool_name: Option<String>,
    file_name: Option<String>,
}

fn permission_payload(request: &PermissionRequestData) -> PermissionPayload {
    let payload = match request.extra.get("permissionRequest") {
        Some(request) => request.as_object(),
        None => request.extra.as_object(),
    };
    PermissionPayload {
        kind: payload
            .and_then(|payload| payload.get("kind"))
            .and_then(|value| value.as_str())
            .map(str::to_owned),
        server_name: payload
            .and_then(|payload| payload.get("serverName"))
            .and_then(|value| value.as_str())
            .map(str::to_owned),
        tool_name: payload
            .and_then(|payload| payload.get("toolName"))
            .and_then(|value| value.as_str())
            .map(str::to_owned),
        file_name: payload
            .and_then(|payload| payload.get("fileName"))
            .and_then(|value| value.as_str())
            .map(str::to_owned),
    }
}

#[async_trait]
impl PermissionHandler for WikipediaPermissions {
    async fn handle(
        &self,
        _session_id: SessionId,
        _request_id: RequestId,
        request: PermissionRequestData,
    ) -> PermissionResult {
        let payload = permission_payload(&request);
        let kind_allowed = request.kind == Some(PermissionRequestKind::Mcp)
            || payload.kind.as_deref() == Some("mcp");
        let tool_allowed = matches!(
            payload.tool_name.as_deref(),
            Some("search" | "readArticle" | "wikipedia-search" | "wikipedia-readArticle")
        );
        if kind_allowed && payload.server_name.as_deref() == Some("wikipedia") && tool_allowed {
            PermissionResult::approve_once()
        } else {
            PermissionResult::reject(Some(
                "This session allows only the scoped Wikipedia search and article tools."
                    .to_owned(),
            ))
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Source {
    pub title: String,
    pub url: String,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ExtractedSources {
    pub body: String,
    pub sources: Vec<Source>,
}

pub fn extract_sources(content: &str) -> ExtractedSources {
    let normalized = content.replace("\r\n", "\n").replace('\r', "\n");
    let lines = normalized.lines().collect::<Vec<_>>();
    let Some(sources_index) = lines
        .iter()
        .rposition(|line| line.trim().eq_ignore_ascii_case("## Sources"))
    else {
        return ExtractedSources {
            body: normalized.trim_end().to_owned(),
            sources: Vec::new(),
        };
    };

    let body = lines[..sources_index].join("\n").trim_end().to_owned();
    let sources = lines[sources_index + 1..]
        .iter()
        .filter_map(|line| parse_source_line(line))
        .collect();
    ExtractedSources { body, sources }
}

fn parse_source_line(line: &str) -> Option<Source> {
    let bullet = line.trim().strip_prefix("- ")?.trim();
    let split = bullet.find(": http")?;
    let title = bullet[..split].trim();
    let url = bullet[split + 2..].trim();
    if title.is_empty() || url.is_empty() {
        return None;
    }
    Some(Source {
        title: title.to_owned(),
        url: url.to_owned(),
    })
}

pub struct ExhibitWritePermissions {
    working_directory: PathBuf,
    exhibit_path: PathBuf,
}

pub fn exhibit_write_permission(working_directory: impl Into<PathBuf>) -> ExhibitWritePermissions {
    let directory = absolute_normalized_path(working_directory.into());
    let exhibit_path = normalize_path(directory.join(EXHIBIT_FILE_NAME));
    ExhibitWritePermissions {
        working_directory: directory,
        exhibit_path,
    }
}

#[async_trait]
impl PermissionHandler for ExhibitWritePermissions {
    async fn handle(
        &self,
        _session_id: SessionId,
        _request_id: RequestId,
        request: PermissionRequestData,
    ) -> PermissionResult {
        let payload = permission_payload(&request);
        let kind_allowed = request.kind == Some(PermissionRequestKind::Write)
            || payload.kind.as_deref() == Some("write");
        let file_allowed = payload.file_name.as_deref().is_some_and(|file_name| {
            let candidate = Path::new(file_name);
            let candidate = if candidate.is_absolute() {
                candidate.to_path_buf()
            } else {
                self.working_directory.join(candidate)
            };
            normalize_path(candidate) == self.exhibit_path
        });
        if kind_allowed && file_allowed {
            PermissionResult::approve_once()
        } else {
            PermissionResult::reject(Some(
                "This session allows writing only exhibit.html in the application working directory."
                    .to_owned(),
            ))
        }
    }
}

fn absolute_normalized_path(path: PathBuf) -> PathBuf {
    let absolute = if path.is_absolute() {
        path
    } else {
        std::env::current_dir()
            .map(|directory| directory.join(&path))
            .unwrap_or(path)
    };
    normalize_path(absolute)
}

fn normalize_path(path: PathBuf) -> PathBuf {
    let mut normalized = PathBuf::new();
    for component in path.components() {
        match component {
            Component::CurDir => {}
            Component::ParentDir => {
                if !normalized.pop() {
                    normalized.push("..");
                }
            }
            Component::Normal(part) => normalized.push(part),
            Component::RootDir => normalized.push(component.as_os_str()),
            Component::Prefix(prefix) => normalized.push(prefix.as_os_str()),
        }
    }
    normalized
}

pub fn ask_yes_no(question: &str, default_yes: bool) -> io::Result<bool> {
    let suffix = if default_yes { " [Y/n]: " } else { " [y/N]: " };
    print!("{question}{suffix}");
    io::stdout().flush()?;
    let mut answer = String::new();
    io::stdin().read_line(&mut answer)?;
    let answer = answer.trim();
    if answer.is_empty() {
        return Ok(default_yes);
    }
    Ok(match answer.to_lowercase().as_str() {
        "y" | "yes" => true,
        "n" | "no" => false,
        _ => default_yes,
    })
}

pub fn ask_line(question: &str) -> io::Result<String> {
    print!("{question}");
    io::stdout().flush()?;
    let mut answer = String::new();
    io::stdin().read_line(&mut answer)?;
    Ok(answer.trim().to_owned())
}

pub fn read_facts() -> io::Result<Vec<String>> {
    println!("Enter one approved fact per line. Submit a blank line when finished:");
    let mut facts = Vec::new();
    loop {
        let mut fact = String::new();
        io::stdin().read_line(&mut fact)?;
        let fact = fact.trim();
        if fact.is_empty() {
            return Ok(facts);
        }
        facts.push(fact.to_owned());
    }
}
