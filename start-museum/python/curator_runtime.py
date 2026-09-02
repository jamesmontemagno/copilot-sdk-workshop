from __future__ import annotations

from typing import Any, Protocol

from copilot import CopilotClient


class CuratorSession(Protocol):
    async def send_and_wait(
        self, prompt: str, *, timeout: float | None = None
    ) -> Any: ...

    async def disconnect(self) -> None: ...


class CuratorClient(Protocol):
    async def start(self) -> None: ...

    async def create_session(self, **configuration: Any) -> CuratorSession: ...

    async def stop(self) -> None: ...


def create_copilot_curator_client() -> CuratorClient:
    return CopilotClient()
