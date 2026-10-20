
import argparse
import asyncio
import json

from multi_agent.agent_registry import AgentRegistry
from multi_agent.agents.specialists import SpecialistAgent
from multi_agent.config import get_settings
from multi_agent.observability.logging import configure_logging
from multi_agent.orchestrator import Orchestrator
from multi_agent.providers.mock import MockProvider
from multi_agent.scheduler import Scheduler
from multi_agent.storage.sqlite_store import SQLiteStore
from multi_agent.models import TaskSpec


def build_system():
    settings = get_settings()
    configure_logging(settings.log_level)

    if settings.llm_provider == "gemini":
        from multi_agent.providers.gemini_provider import GeminiProvider

        if not settings.gemini_api_key:
            raise ValueError(
                "GEMINI_API_KEY is missing. "
                "Add it to your .env file."
            )

        provider = GeminiProvider(
            settings.gemini_api_key,
            settings.gemini_model,
        )

    elif settings.llm_provider == "mock":
        provider = MockProvider()

    else:
        raise ValueError(
            f"Unsupported LLM_PROVIDER: {settings.llm_provider!r}. "
            "Set LLM_PROVIDER=gemini or LLM_PROVIDER=mock in .env."
        )

    registry = AgentRegistry()

    agents = [
        ("planner", "Break objectives into clear, dependency-aware steps."),
        (
            "research",
            "Research assigned topics and distinguish evidence from uncertainty.",
        ),
        (
            "coding",
            "Design and explain code changes without claiming unverified execution.",
        ),
        (
            "analysis",
            "Analyze inputs, compare alternatives, and state assumptions.",
        ),
        (
            "execution",
            "Handle only explicitly approved, bounded execution tasks.",
        ),
        (
            "reviewer",
            "Review outputs for correctness, completeness, and unsupported claims.",
        ),
        (
            "testing",
            "Propose and interpret tests; distinguish proposed tests from executed tests.",
        ),
        (
            "memory",
            "Summarize reusable decisions and task context with provenance.",
        ),
        (
            "coordinator",
            "Coordinate work and reconcile conflicts across agents.",
        ),
        (
            "final",
            "Produce a concise final response with evidence and limitations.",
        ),
    ]

    for name, role in agents:
        registry.register(
            SpecialistAgent(name, provider, role)
        )

    store = SQLiteStore(settings.database_path)

    scheduler = Scheduler(
        registry,
        store,
        settings.max_concurrency,
        settings.max_retries,
    )

    return Orchestrator(registry, scheduler), registry, store


async def run_demo(workflow: str) -> None:
    orchestrator, _, _ = build_system()

    if workflow == "research":
        topic_a = TaskSpec(
            name="topic-a",
            description=(
                "Summarize the technical landscape for async Python agents."
            ),
            agent_name="research",
            input_data={"focus": "async"},
        )

        topic_b = TaskSpec(
            name="topic-b",
            description=(
                "Identify reliability patterns for task schedulers."
            ),
            agent_name="analysis",
            input_data={"focus": "reliability"},
        )

        review = TaskSpec(
            name="review",
            description=(
                "Review the independent findings and list caveats."
            ),
            agent_name="reviewer",
            dependencies=[topic_a.id, topic_b.id],
        )

        tasks = [topic_a, topic_b, review]

    elif workflow == "coding":
        design = TaskSpec(
            name="design",
            description="Define a small typed task-result interface.",
            agent_name="planner",
        )

        implementation = TaskSpec(
            name="implementation",
            description=(
                "Implement the interface described in the dependency output."
            ),
            agent_name="coding",
            dependencies=[design.id],
        )

        tests = TaskSpec(
            name="tests",
            description=(
                "Suggest tests for the implementation and report gaps."
            ),
            agent_name="testing",
            dependencies=[design.id],
        )

        review = TaskSpec(
            name="review",
            description="Review implementation and test findings.",
            agent_name="reviewer",
            dependencies=[implementation.id, tests.id],
        )

        tasks = [design, implementation, tests, review]

    else:
        scope = TaskSpec(
            name="scope",
            description="Break the objective into scope and assumptions.",
            agent_name="planner",
        )

        risk = TaskSpec(
            name="risk",
            description="Analyze risks and mitigations.",
            agent_name="analysis",
        )

        options = TaskSpec(
            name="options",
            description="Compare feasible implementation options.",
            agent_name="research",
        )

        synthesis = TaskSpec(
            name="synthesis",
            description=(
                "Synthesize scope, risks, and options into a plan."
            ),
            agent_name="coordinator",
            dependencies=[scope.id, risk.id, options.id],
        )

        final = TaskSpec(
            name="final",
            description=(
                "Write a final report from the synthesized plan."
            ),
            agent_name="final",
            dependencies=[synthesis.id],
        )

        tasks = [scope, risk, options, synthesis, final]

    report = await orchestrator.run_objective(
        f"Example workflow: {workflow}",
        tasks,
    )

    print(
        json.dumps(
            report.model_dump(mode="json"),
            indent=2,
            default=str,
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser(prog="mas")

    parser.add_argument(
        "workflow",
        choices=["research", "coding", "complex"],
        nargs="?",
        default="complex",
    )

    args = parser.parse_args()
    asyncio.run(run_demo(args.workflow))


if __name__ == "__main__":
    main()
