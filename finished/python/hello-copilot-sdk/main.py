import asyncio
import sys

from copilot import CopilotClient, define_tool
from copilot.session_events import AssistantMessageData, AssistantMessageDeltaData, SessionErrorData, SessionIdleData
from pydantic import BaseModel, Field

from accessibility_rule_catalog import ACCESSIBILITY_RULES


class LookupParams(BaseModel):
    query: str = Field(description="The accessibility issue or WCAG criterion to look up.")


@define_tool(
    name="accessibility_rule_lookup",
    description="Looks up read-only WCAG guidance maintained by this application.",
    skip_permission=True,
)
def accessibility_rule_lookup(params: LookupParams) -> dict[str, object]:
    query = params.query.strip().lower()
    rule = next(
        (
            item
            for item in ACCESSIBILITY_RULES
            if item.criterion.lower() in query
            or item.title.lower() in query
            or any(keyword in query for keyword in item.keywords)
        ),
        None,
    )
    if rule is None:
        return {
            "criterion": "No exact match",
            "title": "Criterion not found",
            "when_it_applies": "The issue is not represented in the workshop catalog.",
            "recommendation": "Verify the evidence and consult the complete WCAG reference.",
        }
    return rule.__dict__


def read_question() -> str:
    argument = " ".join(sys.argv[1:]).strip()
    return argument or input("Accessibility question: ").strip()


async def main() -> None:
    question = read_question()
    if not question:
        print("Enter an accessibility question to continue.", file=sys.stderr)
        return

    async with CopilotClient() as client:
        async with await client.create_session(
            streaming=True,
            tools=[accessibility_rule_lookup],
            available_tools=["accessibility_rule_lookup"],
        ) as session:
            done = asyncio.Event()
            error: RuntimeError | None = None
            received_delta = False

            def on_event(event) -> None:
                nonlocal error, received_delta
                match event.data:
                    case AssistantMessageDeltaData(delta_content=delta) if delta:
                        received_delta = True
                        print(delta, end="", flush=True)
                    case AssistantMessageData(content=content) if content and not received_delta:
                        print(content)
                    case SessionErrorData(message=message):
                        error = RuntimeError(message)
                        done.set()
                    case SessionIdleData():
                        done.set()

            session.on(on_event)
            print("\nCopilot:")
            await session.send(
                f"Use accessibility_rule_lookup to answer this question: {question}"
            )
            await done.wait()
            if error is not None:
                raise error


if __name__ == "__main__":
    asyncio.run(main())
