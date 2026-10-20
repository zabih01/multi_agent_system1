import asyncio
from datetime import datetime, timezone
from multi_agent.agent_registry import AgentRegistry
from multi_agent.models import TaskResult, TaskSpec, WorkflowReport
from multi_agent.scheduler import Scheduler


class Orchestrator:
    def __init__(self, registry: AgentRegistry, scheduler: Scheduler) -> None:
        self.registry = registry
        self.scheduler = scheduler

    async def delegate(self, tasks: list[TaskSpec], context: dict | None = None) -> list[TaskResult]:
        return await self.scheduler.run(tasks, context)

    async def run_objective(self, objective: str, tasks: list[TaskSpec]) -> WorkflowReport:
        started = datetime.now(timezone.utc)
        results = await self.delegate(tasks, {"objective": objective})
        failed = sum(result.status.value in {"failed", "blocked", "cancelled"} for result in results)
        status = "completed" if not failed else "partially_completed" if failed < len(results) else "failed"
        summary = "\n".join(f"- {result.agent_name}: {result.status.value} — {str(result.output or result.error)[:500]}" for result in results)
        return WorkflowReport(objective=objective, status=status, results=results, summary=summary, started_at=started)

    async def cancel_all(self) -> None:
        await asyncio.sleep(0)
