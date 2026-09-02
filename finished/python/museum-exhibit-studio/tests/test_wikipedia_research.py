import json
from contextlib import redirect_stdout
from io import StringIO
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from copilot.rpc import PermissionDecisionApproveOnce, PermissionDecisionReject
from copilot.session_events import (
    ToolExecutionCompleteData,
    ToolExecutionCompleteResult,
    ToolExecutionStartData,
)

from curator_prompts import APOLLO_11_FACTS, build_exhibit_prompt
import main as application
from main import review_research
from museum_exhibit_service import (
    MAXIMUM_RESEARCH_RESPONSE_LENGTH,
    RESEARCH_STATUSES,
    RESEARCH_TIMEOUT_SECONDS,
    MuseumExhibitService,
    create_research_session_configuration,
    create_session_configuration,
    wikipedia_permission_handler,
)


def research_json() -> str:
    article_url = "https://en.wikipedia.org/wiki/Apollo_11"
    return json.dumps(
        {
            "reviews": [
                {
                    "fact": fact,
                    "status": "supported",
                    "evidenceTitle": "Apollo 11",
                    "evidenceUrl": article_url,
                    "explanation": "The article supports this supplied fact.",
                }
                for fact in APOLLO_11_FACTS
            ],
            "additions": [
                {
                    "fact": "Apollo 11 carried three crew members.",
                    "sourceTitle": "Apollo 11",
                    "sourceUrl": article_url,
                    "approved": False,
                }
            ],
            "consultedSources": [{"title": "Apollo 11", "url": article_url}],
            "completed": True,
            "failureMessage": None,
        }
    )


def unretrieved_research_json() -> str:
    payload = json.loads(research_json())
    url = "https://en.wikipedia.org/wiki/Invented_Article"
    for review in payload["reviews"]:
        review["evidenceTitle"] = "Invented Article"
        review["evidenceUrl"] = url
    payload["additions"][0]["sourceTitle"] = "Invented Article"
    payload["additions"][0]["sourceUrl"] = url
    payload["consultedSources"] = [{"title": "Invented Article", "url": url}]
    return json.dumps(payload)


def mismatched_source_json() -> str:
    payload = json.loads(research_json())
    url = "https://en.wikipedia.org/wiki/Neil_Armstrong"
    for review in payload["reviews"]:
        review["evidenceUrl"] = url
    payload["additions"][0]["sourceUrl"] = url
    payload["consultedSources"] = [{"title": "Apollo 11", "url": url}]
    return json.dumps(payload)


class MockWikipediaMcpSession:
    def __init__(self, content: str | None = None, failure: Exception | None = None):
        self.content = content
        self.failure = failure
        self.timeout = 0.0
        self.prompt = ""
        self.disconnected = False
        self.tool_calls = ["search", "readArticle"]
        self.failed_tools: set[str] = set()
        self.article_arguments: object = {"title": "Apollo 11"}
        self.article_result = "Apollo 11 article content"
        self.event_handler = None

    async def send_and_wait(self, prompt: str, *, timeout: float):
        self.prompt = prompt
        self.timeout = timeout
        if self.failure:
            raise self.failure
        for index, tool_name in enumerate(self.tool_calls):
            if self.event_handler is not None:
                tool_call_id = str(index)
                arguments = (
                    {"query": "Apollo 11", "limit": 3}
                    if tool_name == "search"
                    else self.article_arguments
                )
                self.event_handler(
                    SimpleNamespace(
                        data=ToolExecutionStartData(
                            tool_call_id=tool_call_id,
                            tool_name=f"wikipedia-{tool_name}",
                            arguments=arguments,
                            mcp_server_name="wikipedia",
                            mcp_tool_name=tool_name,
                        )
                    )
                )
                self.event_handler(
                    SimpleNamespace(
                        data=ToolExecutionCompleteData(
                            success=tool_name not in self.failed_tools,
                            tool_call_id=tool_call_id,
                            result=ToolExecutionCompleteResult(
                                content=(
                                    "Apollo 11 search results"
                                    if tool_name == "search"
                                    else self.article_result
                                )
                            ),
                        )
                    )
                )
        return SimpleNamespace(data=SimpleNamespace(content=self.content))

    def on(self, handler):
        self.event_handler = handler
        return lambda: setattr(self, "event_handler", None)

    async def disconnect(self) -> None:
        self.disconnected = True


class MockWikipediaMcpClient:
    def __init__(
        self,
        session: MockWikipediaMcpSession,
        start_failure: Exception | None = None,
    ) -> None:
        self.session = session
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
        return self.session

    async def stop(self) -> None:
        self.stopped = True


class WikipediaResearchTests(unittest.IsolatedAsyncioTestCase):
    def test_research_configuration_exposes_only_read_tools(self) -> None:
        configuration = create_research_session_configuration(" test-model ")
        self.assertEqual(
            ["wikipedia-search", "wikipedia-readArticle"],
            configuration["available_tools"],
        )
        self.assertEqual(
            ["search", "readArticle"],
            configuration["mcp_servers"]["wikipedia"]["tools"],
        )
        self.assertEqual([], create_session_configuration()["available_tools"])

    def test_permission_handler_denies_everything_else(self) -> None:
        for tool_name in (
            "search",
            "readArticle",
            "wikipedia-search",
            "wikipedia-readArticle",
        ):
            decision = wikipedia_permission_handler(
                SimpleNamespace(
                    kind="mcp", server_name="wikipedia", tool_name=tool_name
                ),
                None,
            )
            self.assertIsInstance(decision, PermissionDecisionApproveOnce)
        rejected = wikipedia_permission_handler(
            SimpleNamespace(kind="mcp", server_name="other", tool_name="search"),
            None,
        )
        self.assertIsInstance(rejected, PermissionDecisionReject)

    async def test_research_keeps_reviews_and_additions_separate(self) -> None:
        session = MockWikipediaMcpSession(research_json())
        client = MockWikipediaMcpClient(session)
        result = await MuseumExhibitService(client).research(list(APOLLO_11_FACTS))

        self.assertTrue(result.completed)
        self.assertEqual(APOLLO_11_FACTS, tuple(review.fact for review in result.reviews))
        self.assertTrue(
            all(review.status in RESEARCH_STATUSES for review in result.reviews)
        )
        self.assertEqual(("search", "readArticle"), tuple(session.tool_calls))
        self.assertEqual(RESEARCH_TIMEOUT_SECONDS, session.timeout)
        self.assertIn("call search first", session.prompt)
        self.assertIs(
            wikipedia_permission_handler,
            client.configuration["on_permission_request"],
        )
        self.assertEqual("Apollo 11", result.additions[0].source_title)
        self.assertEqual(
            "https://en.wikipedia.org/wiki/Apollo_11",
            result.additions[0].source_url,
        )
        self.assertFalse(result.additions[0].approved)
        self.assertTrue(session.disconnected)
        self.assertTrue(client.stopped)

    async def test_numeric_page_id_retrieval_uses_completed_article_content(self) -> None:
        session = MockWikipediaMcpSession(research_json())
        session.article_arguments = {"pageId": 736}
        result = await MuseumExhibitService(
            MockWikipediaMcpClient(session)
        ).research(list(APOLLO_11_FACTS))
        self.assertTrue(result.completed)

    async def test_unapproved_addition_does_not_enter_generation_prompt(self) -> None:
        result = await MuseumExhibitService(
            MockWikipediaMcpClient(MockWikipediaMcpSession(research_json()))
        ).research(list(APOLLO_11_FACTS))
        with (
            patch("builtins.input", return_value=""),
            redirect_stdout(StringIO()),
        ):
            additions = review_research(result)
        prompt = build_exhibit_prompt([*APOLLO_11_FACTS, *additions])
        self.assertNotIn(result.additions[0].fact, prompt)

    async def test_approved_addition_preserves_source_and_enters_prompt(self) -> None:
        result = await MuseumExhibitService(
            MockWikipediaMcpClient(MockWikipediaMcpSession(research_json()))
        ).research(list(APOLLO_11_FACTS))
        with (
            patch("builtins.input", return_value="y"),
            redirect_stdout(StringIO()),
        ):
            additions = review_research(result)
        prompt = build_exhibit_prompt([*APOLLO_11_FACTS, *additions])
        self.assertIn(result.additions[0].fact, prompt)
        self.assertEqual(
            ("Apollo 11", "https://en.wikipedia.org/wiki/Apollo_11"),
            (
                result.consulted_sources[0].title,
                result.consulted_sources[0].url,
            ),
        )

    async def test_fact_limit_prevents_addition_approval(self) -> None:
        result = await MuseumExhibitService(
            MockWikipediaMcpClient(MockWikipediaMcpSession(research_json()))
        ).research(list(APOLLO_11_FACTS))
        with (
            patch("builtins.input", return_value="y") as user_input,
            redirect_stdout(StringIO()),
        ):
            additions = review_research(result, remaining_fact_slots=0)
        self.assertFalse(additions)
        user_input.assert_not_called()

    async def test_malformed_output_does_not_invent_evidence(self) -> None:
        for content in (
            '{"reviews": []}',
            research_json().replace(
                "https://en.wikipedia.org/wiki/Apollo_11",
                "https://example.com/Apollo_11",
            ),
            unretrieved_research_json(),
            mismatched_source_json(),
        ):
            with self.subTest(content=content[:30]):
                session = MockWikipediaMcpSession(content)
                client = MockWikipediaMcpClient(session)
                result = await MuseumExhibitService(client).research(
                    list(APOLLO_11_FACTS)
                )
                self.assertFalse(result.completed)
                self.assertFalse(result.additions)
                self.assertFalse(result.consulted_sources)
                self.assertTrue(
                    all(review.status == "not checked" for review in result.reviews)
                )
                self.assertTrue(session.disconnected)
                self.assertTrue(client.stopped)

    async def test_missing_or_reversed_tool_use_is_incomplete(self) -> None:
        for tool_calls, failed_tools in (
            ([], set()),
            (["readArticle", "search"], set()),
            (["search", "readArticle"], {"readArticle"}),
        ):
            with self.subTest(tool_calls=tool_calls, failed_tools=failed_tools):
                session = MockWikipediaMcpSession(research_json())
                session.tool_calls = tool_calls
                session.failed_tools = failed_tools
                result = await MuseumExhibitService(
                    MockWikipediaMcpClient(session)
                ).research(list(APOLLO_11_FACTS))
                self.assertFalse(result.completed)
                self.assertTrue(
                    all(review.status == "not checked" for review in result.reviews)
                )

    async def test_supported_review_requires_evidence(self) -> None:
        content = research_json().replace(
            '"evidenceTitle": "Apollo 11", '
            '"evidenceUrl": "https://en.wikipedia.org/wiki/Apollo_11"',
            '"evidenceTitle": null, "evidenceUrl": null',
            1,
        )
        result = await MuseumExhibitService(
            MockWikipediaMcpClient(MockWikipediaMcpSession(content))
        ).research(list(APOLLO_11_FACTS))
        self.assertFalse(result.completed)
        self.assertIn("requires source evidence", result.failure_message)

    async def test_oversized_output_reports_incomplete_research(self) -> None:
        session = MockWikipediaMcpSession(
            "x" * (MAXIMUM_RESEARCH_RESPONSE_LENGTH + 1)
        )
        client = MockWikipediaMcpClient(session)
        result = await MuseumExhibitService(client).research(list(APOLLO_11_FACTS))
        self.assertFalse(result.completed)
        self.assertIn("size limit", result.failure_message)
        self.assertTrue(session.disconnected)
        self.assertTrue(client.stopped)

    async def test_timeout_and_startup_failure_report_incomplete_research(self) -> None:
        timeout_session = MockWikipediaMcpSession(failure=TimeoutError("timed out"))
        timeout_client = MockWikipediaMcpClient(timeout_session)
        timeout_result = await MuseumExhibitService(timeout_client).research(
            list(APOLLO_11_FACTS)
        )
        self.assertFalse(timeout_result.completed)
        self.assertIn("timed out", timeout_result.failure_message)
        self.assertTrue(timeout_session.disconnected)
        self.assertTrue(timeout_client.stopped)

        failed_session = MockWikipediaMcpSession()
        failed_client = MockWikipediaMcpClient(
            failed_session, start_failure=RuntimeError("startup failed")
        )
        failed_result = await MuseumExhibitService(failed_client).research(
            list(APOLLO_11_FACTS)
        )
        self.assertFalse(failed_result.completed)
        self.assertIn("startup failed", failed_result.failure_message)
        self.assertFalse(failed_session.disconnected)
        self.assertTrue(failed_client.stopped)

    async def test_empty_custom_facts_report_the_normal_cli_error(self) -> None:
        output = StringIO()
        errors = StringIO()
        with (
            patch("builtins.input", side_effect=["n", "", "y"]),
            patch.object(application, "CopilotClient", return_value=SimpleNamespace()),
            redirect_stdout(output),
            patch("sys.stderr", errors),
        ):
            exit_code = await application.main()
        self.assertEqual(1, exit_code)
        self.assertIn("Provide at least one approved fact", errors.getvalue())


if __name__ == "__main__":
    unittest.main()
