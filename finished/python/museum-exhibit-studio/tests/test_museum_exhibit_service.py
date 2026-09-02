from types import SimpleNamespace
import unittest

from curator_prompts import APOLLO_11_FACTS, SYSTEM_MESSAGE
from museum_exhibit_service import (
    GENERATION_TIMEOUT_SECONDS,
    MuseumExhibitService,
    create_session_configuration,
)


def valid_exhibit() -> str:
    narrative = " ".join(f"word{index}" for index in range(1, 111))
    return (
        f"# A Journey\n## Narrative\n{narrative}\n## Visitor questions\n"
        "1. What do you notice?\n"
        "2. What would you ask?\n"
        "3. What will you remember?"
    )


class FakeSession:
    def __init__(self, content: str | None = None, failure: Exception | None = None):
        self.content = content
        self.failure = failure
        self.prompt = ""
        self.timeout = 0.0
        self.disconnected = False

    async def send_and_wait(self, prompt: str, *, timeout: float):
        self.prompt = prompt
        self.timeout = timeout
        if self.failure:
            raise self.failure
        return SimpleNamespace(data=SimpleNamespace(content=self.content))

    async def disconnect(self) -> None:
        self.disconnected = True


class FakeClient:
    def __init__(
        self,
        session: FakeSession,
        create_failure: Exception | None = None,
        start_failure: Exception | None = None,
    ) -> None:
        self.session = session
        self.create_failure = create_failure
        self.start_failure = start_failure
        self.started = False
        self.stopped = False
        self.configuration = {}

    async def start(self) -> None:
        self.started = True
        if self.start_failure:
            raise self.start_failure

    async def create_session(self, **configuration):
        self.configuration = configuration
        if self.create_failure:
            raise self.create_failure
        return self.session

    async def stop(self) -> None:
        self.stopped = True


class MuseumExhibitServiceTests(unittest.IsolatedAsyncioTestCase):
    def test_configuration_owns_system_prompt_and_has_no_tools(self) -> None:
        configuration = create_session_configuration(" test-model ")
        self.assertEqual("museum-exhibit-studio", configuration["client_name"])
        self.assertEqual("test-model", configuration["model"])
        self.assertEqual([], configuration["available_tools"])
        self.assertFalse(configuration["streaming"])
        self.assertEqual(
            {"mode": "replace", "content": SYSTEM_MESSAGE},
            configuration["system_message"],
        )

    async def test_success_returns_content_and_cleans_up(self) -> None:
        session = FakeSession(valid_exhibit())
        client = FakeClient(session)
        result = await MuseumExhibitService(client).generate(list(APOLLO_11_FACTS))
        self.assertTrue(result.validation.valid)
        self.assertTrue(result.validation.narrative.valid)
        self.assertTrue(client.started)
        self.assertTrue(client.stopped)
        self.assertTrue(session.disconnected)
        self.assertEqual(GENERATION_TIMEOUT_SECONDS, session.timeout)
        for fact in APOLLO_11_FACTS:
            self.assertIn(fact, session.prompt)

    async def test_invalid_prompt_never_starts_client(self) -> None:
        session = FakeSession()
        client = FakeClient(session)
        with self.assertRaises(ValueError):
            await MuseumExhibitService(client).generate([])
        self.assertFalse(client.started)

    async def test_empty_output_is_an_error_and_cleans_up(self) -> None:
        session = FakeSession(" ")
        client = FakeClient(session)
        with self.assertRaisesRegex(RuntimeError, "no exhibit content"):
            await MuseumExhibitService(client).generate(list(APOLLO_11_FACTS))
        self.assertTrue(session.disconnected)
        self.assertTrue(client.stopped)

    async def test_send_failure_disconnects_session_and_stops_client(self) -> None:
        session = FakeSession(failure=TimeoutError("Timed out."))
        client = FakeClient(session)
        with self.assertRaises(TimeoutError):
            await MuseumExhibitService(client).generate(list(APOLLO_11_FACTS))
        self.assertTrue(session.disconnected)
        self.assertTrue(client.stopped)

    async def test_create_failure_still_stops_client(self) -> None:
        session = FakeSession()
        client = FakeClient(session, create_failure=RuntimeError("create failed"))
        with self.assertRaisesRegex(RuntimeError, "create failed"):
            await MuseumExhibitService(client).generate(list(APOLLO_11_FACTS))
        self.assertFalse(session.disconnected)
        self.assertTrue(client.stopped)

    async def test_start_failure_still_stops_client(self) -> None:
        session = FakeSession()
        client = FakeClient(session, start_failure=RuntimeError("start failed"))
        with self.assertRaisesRegex(RuntimeError, "start failed"):
            await MuseumExhibitService(client).generate(list(APOLLO_11_FACTS))
        self.assertFalse(session.disconnected)
        self.assertTrue(client.stopped)


if __name__ == "__main__":
    unittest.main()
