use async_trait::async_trait;
use museum_exhibit_studio::*;
use std::sync::{
    Arc,
    atomic::{AtomicBool, Ordering},
};
use std::time::Duration;

struct Session {
    response: Result<Option<String>, RuntimeError>,
    disconnected: Arc<AtomicBool>,
    timeout: Arc<std::sync::Mutex<Duration>>,
}

#[async_trait]
impl CuratorSession for Session {
    async fn send_and_wait(
        &mut self,
        _: String,
        timeout: Duration,
    ) -> Result<Option<String>, RuntimeError> {
        *self.timeout.lock().unwrap() = timeout;
        std::mem::replace(&mut self.response, Ok(None))
    }

    async fn disconnect(&mut self) -> Result<(), RuntimeError> {
        self.disconnected.store(true, Ordering::SeqCst);
        Ok(())
    }
}

struct TestClient {
    session: Option<Session>,
    started: Arc<AtomicBool>,
    stopped: Arc<AtomicBool>,
}

#[async_trait]
impl CuratorClient for TestClient {
    async fn start(&mut self) -> Result<(), RuntimeError> {
        self.started.store(true, Ordering::SeqCst);
        Ok(())
    }

    async fn create_session(
        &mut self,
        _: github_copilot_sdk::types::SessionConfig,
    ) -> Result<Box<dyn CuratorSession>, RuntimeError> {
        Ok(Box::new(self.session.take().unwrap()))
    }

    async fn stop(&mut self) -> Result<(), RuntimeError> {
        self.stopped.store(true, Ordering::SeqCst);
        Ok(())
    }
}

fn client(
    content: Option<String>,
) -> (
    TestClient,
    Arc<AtomicBool>,
    Arc<AtomicBool>,
    Arc<AtomicBool>,
    Arc<std::sync::Mutex<Duration>>,
) {
    let started = Arc::new(AtomicBool::new(false));
    let stopped = Arc::new(AtomicBool::new(false));
    let disconnected = Arc::new(AtomicBool::new(false));
    let timeout = Arc::new(std::sync::Mutex::new(Duration::ZERO));
    (
        TestClient {
            session: Some(Session {
                response: Ok(content),
                disconnected: disconnected.clone(),
                timeout: timeout.clone(),
            }),
            started: started.clone(),
            stopped: stopped.clone(),
        },
        started,
        stopped,
        disconnected,
        timeout,
    )
}

fn valid() -> String {
    let words = (1..=110)
        .map(|i| format!("word{i}"))
        .collect::<Vec<_>>()
        .join(" ");
    format!("# A\n## Narrative\n{words}\n## Visitor questions\n1. One?\n2. Two?\n3. Three?")
}

#[tokio::test]
async fn success_and_empty_clean_up_with_timeout() {
    for output in [Some(valid()), Some(" ".to_owned())] {
        let (mut client, _, stopped, disconnected, timeout) = client(output);
        let facts = APOLLO_11_FACTS.map(str::to_owned);
        let result = generate_exhibit(&mut client, &facts, None).await;
        assert!(stopped.load(Ordering::SeqCst));
        assert!(disconnected.load(Ordering::SeqCst));
        assert_eq!(*timeout.lock().unwrap(), GENERATION_TIMEOUT);
        if let Ok(exhibit) = result {
            assert!(exhibit.validation.narrative.is_valid());
        }
    }
}

#[tokio::test]
async fn invalid_prompt_never_starts() {
    let (mut client, started, _, _, _) = client(Some(valid()));
    assert!(generate_exhibit(&mut client, &[], None).await.is_err());
    assert!(!started.load(Ordering::SeqCst));
}
