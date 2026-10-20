import asyncio
from pathlib import Path
from tempfile import TemporaryDirectory
import pytest
from multi_agent.agent_registry import AgentRegistry
from multi_agent.models import TaskSpec, TaskStatus
from multi_agent.scheduler import Scheduler
from multi_agent.storage.sqlite_store import SQLiteStore


class FakeAgent:
    name = "fake"
    def __init__(self, delay=0.05, fail=0):
        self.delay = delay
        self.fail = fail
        self.calls = 0
        self.active = 0
        self.max_active = 0
    async def execute(self, task, context):
        self.calls += 1
        self.active += 1
        self.max_active = max(self.max_active, self.active)
        try:
            await asyncio.sleep(self.delay)
            if self.fail and self.calls <= self.fail:
                raise RuntimeError("transient")
            return {"task": task.name, "deps": context.get("dependencies", {})}
        finally:
            self.active -= 1


@pytest.mark.asyncio
async def test_independent_tasks_overlap():
    with TemporaryDirectory() as directory:
        registry = AgentRegistry()
        agent = FakeAgent(delay=0.12)
        registry._agents["fake"] = agent
        scheduler = Scheduler(registry, SQLiteStore(Path(directory) / "db.sqlite"), max_concurrency=2, max_retries=0)
        tasks = [TaskSpec(name=str(i), description="run", agent_name="fake", timeout_seconds=2) for i in range(2)]
        start = asyncio.get_running_loop().time()
        results = await scheduler.run(tasks)
        elapsed = asyncio.get_running_loop().time() - start
        assert all(result.status == TaskStatus.COMPLETED for result in results)
        assert agent.max_active == 2
        assert elapsed < 0.22


@pytest.mark.asyncio
async def test_concurrency_limit():
    with TemporaryDirectory() as directory:
        registry = AgentRegistry()
        agent = FakeAgent(delay=0.05)
        registry._agents["fake"] = agent
        scheduler = Scheduler(registry, SQLiteStore(Path(directory) / "db.sqlite"), max_concurrency=2, max_retries=0)
        tasks = [TaskSpec(name=str(i), description="run", agent_name="fake", timeout_seconds=2) for i in range(5)]
        results = await scheduler.run(tasks)
        assert all(result.status == TaskStatus.COMPLETED for result in results)
        assert agent.max_active <= 2


@pytest.mark.asyncio
async def test_retry_transient_failure():
    with TemporaryDirectory() as directory:
        registry = AgentRegistry()
        agent = FakeAgent(delay=0, fail=1)
        registry._agents["fake"] = agent
        scheduler = Scheduler(registry, SQLiteStore(Path(directory) / "db.sqlite"), max_concurrency=1, max_retries=1)
        result = (await scheduler.run([TaskSpec(name="retry", description="run", agent_name="fake", timeout_seconds=2)]))[0]
        assert result.status == TaskStatus.COMPLETED
        assert result.attempts == 2
