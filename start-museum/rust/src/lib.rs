use std::error::Error;
use std::time::Duration;

use async_trait::async_trait;
use github_copilot_sdk::types::{MessageOptions, SessionConfig};
use github_copilot_sdk::{Client, ClientOptions};

pub type RuntimeError = Box<dyn Error + Send + Sync>;

#[async_trait]
pub trait CuratorSession: Send {
    async fn send_and_wait(
        &mut self,
        prompt: String,
        timeout: Duration,
    ) -> Result<Option<String>, RuntimeError>;
    async fn disconnect(&mut self) -> Result<(), RuntimeError>;
}

#[async_trait]
pub trait CuratorClient: Send {
    async fn start(&mut self) -> Result<(), RuntimeError>;
    async fn create_session(
        &mut self,
        configuration: SessionConfig,
    ) -> Result<Box<dyn CuratorSession>, RuntimeError>;
    async fn stop(&mut self) -> Result<(), RuntimeError>;
}

pub struct CopilotCuratorClient {
    client: Option<Client>,
}

impl CopilotCuratorClient {
    pub fn new() -> Self {
        Self { client: None }
    }
}

impl Default for CopilotCuratorClient {
    fn default() -> Self {
        Self::new()
    }
}

struct CopilotCuratorSession(github_copilot_sdk::session::Session);

#[async_trait]
impl CuratorSession for CopilotCuratorSession {
    async fn send_and_wait(
        &mut self,
        prompt: String,
        timeout: Duration,
    ) -> Result<Option<String>, RuntimeError> {
        let event = self
            .0
            .send_and_wait(MessageOptions::new(prompt).with_wait_timeout(timeout))
            .await?;
        Ok(event.and_then(|event| {
            event
                .data
                .get("content")
                .and_then(|content| content.as_str())
                .map(str::to_owned)
        }))
    }

    async fn disconnect(&mut self) -> Result<(), RuntimeError> {
        self.0.disconnect().await?;
        Ok(())
    }
}

#[async_trait]
impl CuratorClient for CopilotCuratorClient {
    async fn start(&mut self) -> Result<(), RuntimeError> {
        self.client = Some(Client::start(ClientOptions::default()).await?);
        Ok(())
    }

    async fn create_session(
        &mut self,
        configuration: SessionConfig,
    ) -> Result<Box<dyn CuratorSession>, RuntimeError> {
        let client = self
            .client
            .as_ref()
            .ok_or_else(|| std::io::Error::other("The curator client is not started."))?;
        Ok(Box::new(CopilotCuratorSession(
            client.create_session(configuration).await?,
        )))
    }

    async fn stop(&mut self) -> Result<(), RuntimeError> {
        if let Some(client) = self.client.take() {
            client.stop().await?;
        }
        Ok(())
    }
}
