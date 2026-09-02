use std::io;
use std::sync::{
    Arc, Mutex,
    atomic::{AtomicBool, Ordering},
};
use std::time::Duration;

use async_trait::async_trait;
use github_copilot_sdk::types::{McpServerConfig, SessionConfig};
use museum_exhibit_studio::*;
use serde_json::json;

struct FixtureMcpServer {
    exposed_tools: Vec<&'static str>,
    calls: Arc<Mutex<Vec<&'static str>>>,
    response: Result<Option<String>, RuntimeError>,
}

struct MockMcpSession {
    server: FixtureMcpServer,
    disconnected: Arc<AtomicBool>,
    prompt: Arc<Mutex<String>>,
    timeout: Arc<Mutex<Duration>>,
}

#[async_trait]
impl CuratorSession for MockMcpSession {
    async fn send_and_wait(
        &mut self,
        prompt: String,
        timeout: Duration,
    ) -> Result<Option<String>, RuntimeError> {
        *self.prompt.lock().unwrap() = prompt;
        *self.timeout.lock().unwrap() = timeout;
        assert_eq!(self.server.exposed_tools, ["search", "readArticle"]);
        self.server
            .calls
            .lock()
            .unwrap()
            .extend(["search", "readArticle"]);
        std::mem::replace(&mut self.server.response, Ok(None))
    }

    async fn disconnect(&mut self) -> Result<(), RuntimeError> {
        self.disconnected.store(true, Ordering::SeqCst);
        Ok(())
    }
}

struct MockClient {
    session: Option<MockMcpSession>,
    configuration: Arc<Mutex<Option<SessionConfig>>>,
    started: Arc<AtomicBool>,
    stopped: Arc<AtomicBool>,
    start_failure: bool,
}

#[async_trait]
impl CuratorClient for MockClient {
    async fn start(&mut self) -> Result<(), RuntimeError> {
        self.started.store(true, Ordering::SeqCst);
        if self.start_failure {
            return Err(Box::new(io::Error::other("fixture startup failed")));
        }
        Ok(())
    }

    async fn create_session(
        &mut self,
        configuration: SessionConfig,
    ) -> Result<Box<dyn CuratorSession>, RuntimeError> {
        *self.configuration.lock().unwrap() = Some(configuration);
        Ok(Box::new(self.session.take().unwrap()))
    }

    async fn stop(&mut self) -> Result<(), RuntimeError> {
        self.stopped.store(true, Ordering::SeqCst);
        Ok(())
    }
}

struct Harness {
    client: MockClient,
    calls: Arc<Mutex<Vec<&'static str>>>,
    prompt: Arc<Mutex<String>>,
    timeout: Arc<Mutex<Duration>>,
    disconnected: Arc<AtomicBool>,
    stopped: Arc<AtomicBool>,
    configuration: Arc<Mutex<Option<SessionConfig>>>,
}

fn harness(response: Result<Option<String>, RuntimeError>) -> Harness {
    let calls = Arc::new(Mutex::new(Vec::new()));
    let prompt = Arc::new(Mutex::new(String::new()));
    let timeout = Arc::new(Mutex::new(Duration::ZERO));
    let disconnected = Arc::new(AtomicBool::new(false));
    let stopped = Arc::new(AtomicBool::new(false));
    let configuration = Arc::new(Mutex::new(None));
    Harness {
        client: MockClient {
            session: Some(MockMcpSession {
                server: FixtureMcpServer {
                    exposed_tools: vec!["search", "readArticle"],
                    calls: calls.clone(),
                    response,
                },
                disconnected: disconnected.clone(),
                prompt: prompt.clone(),
                timeout: timeout.clone(),
            }),
            configuration: configuration.clone(),
            started: Arc::new(AtomicBool::new(false)),
            stopped: stopped.clone(),
            start_failure: false,
        },
        calls,
        prompt,
        timeout,
        disconnected,
        stopped,
        configuration,
    }
}

fn facts() -> Vec<String> {
    APOLLO_11_FACTS.map(str::to_owned).to_vec()
}

fn valid_response() -> String {
    let reviews = APOLLO_11_FACTS
        .iter()
        .map(|fact| {
            json!({
                "fact": fact,
                "status": "supported",
                "evidenceTitle": "Apollo 11",
                "evidenceUrl": "https://en.wikipedia.org/wiki/Apollo_11",
                "explanation": "The fixture article supports this fact."
            })
        })
        .collect::<Vec<_>>();
    json!({
        "reviews": reviews,
        "additions": [{
            "fact": "The mission was crewed.",
            "sourceTitle": "Apollo 11",
            "sourceUrl": "https://en.wikipedia.org/wiki/Apollo_11",
            "approved": true
        }],
        "consultedSources": [{
            "title": "Apollo 11",
            "url": "https://en.wikipedia.org/wiki/Apollo_11"
        }],
        "completed": true,
        "failureMessage": null
    })
    .to_string()
}

fn all_statuses_response() -> String {
    let statuses = [
        ("supported", true),
        ("contradicted", true),
        ("not found", false),
        ("not checked", false),
        ("supported", true),
    ];
    let reviews = APOLLO_11_FACTS
        .iter()
        .zip(statuses)
        .map(|(fact, (status, has_evidence))| {
            json!({
                "fact": fact,
                "status": status,
                "evidenceTitle": has_evidence.then_some("Apollo 11"),
                "evidenceUrl": has_evidence.then_some("https://en.wikipedia.org/wiki/Apollo_11"),
                "explanation": "Fixture review."
            })
        })
        .collect::<Vec<_>>();
    json!({
        "reviews": reviews,
        "additions": [],
        "consultedSources": [{
            "title": "Apollo 11",
            "url": "https://en.wikipedia.org/wiki/Apollo_11"
        }],
        "completed": true,
        "failureMessage": null
    })
    .to_string()
}

#[tokio::test]
async fn mock_mcp_research_is_bounded_and_requires_approval() {
    let mut harness = harness(Ok(Some(valid_response())));
    let original = facts();
    let result = research_wikipedia(&mut harness.client, &original, Some(" test-model ")).await;

    assert!(result.completed);
    assert_eq!(*harness.calls.lock().unwrap(), ["search", "readArticle"]);
    assert_eq!(*harness.timeout.lock().unwrap(), RESEARCH_TIMEOUT);
    assert!(harness.disconnected.load(Ordering::SeqCst));
    assert!(harness.stopped.load(Ordering::SeqCst));
    assert!(
        result
            .reviews
            .iter()
            .all(|review| review.status == FactStatus::Supported)
    );
    assert_eq!(result.additions.len(), 1);
    assert!(!result.additions[0].approved);
    assert_eq!(result.additions[0].source_title, "Apollo 11");
    assert_eq!(
        result.additions[0].source_url,
        "https://en.wikipedia.org/wiki/Apollo_11"
    );

    let prompt = harness.prompt.lock().unwrap();
    assert!(prompt.find("call search first").unwrap() < prompt.find("readArticle").unwrap());
    assert!(prompt.contains("at most 3 results"));
    drop(prompt);

    let configuration = harness.configuration.lock().unwrap();
    let configuration = configuration.as_ref().unwrap();
    assert_eq!(
        configuration.client_name.as_deref(),
        Some("museum-exhibit-studio-research")
    );
    assert_eq!(configuration.model.as_deref(), Some("test-model"));
    assert_eq!(
        configuration.available_tools.as_deref(),
        Some(
            &[
                "wikipedia-search".to_owned(),
                "wikipedia-readArticle".to_owned(),
            ][..]
        )
    );
    let server = configuration
        .mcp_servers
        .as_ref()
        .unwrap()
        .get("wikipedia")
        .unwrap();
    let McpServerConfig::Stdio(server) = server else {
        panic!("Wikipedia must use a stdio MCP server");
    };
    assert_eq!(server.command, "npx");
    assert_eq!(
        server.tools.as_deref(),
        Some(&["search".to_owned(), "readArticle".to_owned()][..])
    );

    assert!(
        create_session_configuration(None)
            .available_tools
            .as_ref()
            .is_some_and(Vec::is_empty)
    );
    assert_eq!(
        approved_facts_with_additions(&original, &result.additions).unwrap(),
        original
    );
    let mut approved = result.additions.clone();
    approved[0].approved = true;
    let combined = approved_facts_with_additions(&original, &approved).unwrap();
    assert_eq!(combined.last().unwrap(), "The mission was crewed.");

    let full = vec!["fact".to_owned(); MAXIMUM_FACT_COUNT];
    assert!(approved_facts_with_additions(&full, &approved).is_err());
}

#[tokio::test]
async fn empty_malformed_and_timeout_results_fail_without_inventing_evidence() {
    let original = facts();
    let responses = [
        Ok(None),
        Ok(Some("{not json}".to_owned())),
        Ok(Some("x".repeat(MAXIMUM_RESEARCH_RESPONSE_BYTES + 1))),
        Err(Box::new(io::Error::new(io::ErrorKind::TimedOut, "fixture timeout")) as RuntimeError),
    ];
    for response in responses {
        let mut harness = harness(response);
        let result = research_wikipedia(&mut harness.client, &original, None).await;
        assert!(!result.completed);
        assert!(result.additions.is_empty());
        assert!(result.consulted_sources.is_empty());
        assert!(result.reviews.iter().all(|review| {
            review.status == FactStatus::NotChecked
                && review.evidence_title.is_none()
                && review.evidence_url.is_none()
        }));
        assert!(harness.disconnected.load(Ordering::SeqCst));
        assert!(harness.stopped.load(Ordering::SeqCst));
    }
}

#[tokio::test]
async fn startup_failure_returns_not_checked_reviews() {
    let original = facts();
    let mut harness = harness(Ok(Some(valid_response())));
    harness.client.start_failure = true;
    let result = research_wikipedia(&mut harness.client, &original, None).await;
    assert!(!result.completed);
    assert_eq!(result.reviews.len(), original.len());
    assert!(
        result
            .reviews
            .iter()
            .all(|review| review.status == FactStatus::NotChecked)
    );
    assert!(
        result
            .failure_message
            .as_deref()
            .is_some_and(|message| message.contains("fixture startup failed"))
    );
    assert!(harness.stopped.load(Ordering::SeqCst));
}

#[tokio::test]
async fn invalid_fact_budget_never_starts_research() {
    let mut harness = harness(Ok(Some(valid_response())));
    let too_many = vec!["fact".to_owned(); MAXIMUM_FACT_COUNT + 1];
    let result = research_wikipedia(&mut harness.client, &too_many, None).await;
    assert!(!result.completed);
    assert!(!harness.client.started.load(Ordering::SeqCst));
    assert!(
        result
            .failure_message
            .as_deref()
            .is_some_and(|message| message.contains("no more than 20"))
    );
}

#[tokio::test]
async fn malformed_provenance_is_rejected() {
    let original = facts();
    let malformed = valid_response().replace(
        "https://en.wikipedia.org/wiki/Apollo_11",
        "https://example.com/Apollo_11",
    );
    let mut harness = harness(Ok(Some(malformed)));
    let result = research_wikipedia(&mut harness.client, &original, None).await;
    assert!(!result.completed);
    assert!(result.additions.is_empty());
    assert!(result.consulted_sources.is_empty());
}

#[tokio::test]
async fn too_many_additions_are_rejected() {
    let original = facts();
    let mut response: serde_json::Value = serde_json::from_str(&valid_response()).unwrap();
    let addition = response["additions"][0].clone();
    response["additions"] = json!([
        addition.clone(),
        addition.clone(),
        addition.clone(),
        addition
    ]);
    let mut harness = harness(Ok(Some(response.to_string())));
    let result = research_wikipedia(&mut harness.client, &original, None).await;
    assert!(!result.completed);
    assert!(result.additions.is_empty());
}

#[tokio::test]
async fn every_documented_review_status_is_preserved() {
    let original = facts();
    let mut harness = harness(Ok(Some(all_statuses_response())));
    let result = research_wikipedia(&mut harness.client, &original, None).await;
    assert!(result.completed);
    assert_eq!(
        result
            .reviews
            .iter()
            .map(|review| review.status)
            .collect::<Vec<_>>(),
        vec![
            FactStatus::Supported,
            FactStatus::Contradicted,
            FactStatus::NotFound,
            FactStatus::NotChecked,
            FactStatus::Supported,
        ]
    );
}
