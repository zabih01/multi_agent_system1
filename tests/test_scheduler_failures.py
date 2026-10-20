import asyncio
from pathlib import Path
from tempfile import TemporaryDirectory
import pytest
from multi_agent.agent_registry import AgentRegistry
from multi_agent.models import TaskSpec, TaskStatus
from multi_agent.scheduler import Scheduler
from multi_agent.storage.sqlite_store import SQLiteStore


class SwitchAgent:
    name = "switch"
    def __init__(self, fail_always=False, delay=0):
        self.fail_always = fail_always
        self.delay = delay
    async def execute(self, task, context):
        if self.delay:
            await asyncio.sleep(self.delay)
        if self.fail_always:
            raise RuntimeError("deliberate failure")
        return "ok"


def make_scheduler(directory, agent, retries=0):
    registry = AgentRegistry()
    registry._agents[agent.name] = agent
    return Scheduler(registry, SQLiteStore(Path(directory) / "db.sqlite"), max_concurrency=2, max_retries=retries)


@pytest.mark.asyncio
async def test_failed_dependency_blocks_child():
    with TemporaryDirectory() as directory:
        scheduler = make_scheduler(directory, SwitchAgent(fail_always=True), retries=0)
        parent = TaskSpec(name="parent", description="fails", agent_name="switch", max_retries=0)
        child = TaskSpec(name="child", description="depends", agent_name="switch", dependencies=[parent.id])
        results = await scheduler.run([parent, child])
        assert results[0].status == TaskStatus.FAILED
        assert results[1].status == TaskStatus.BLOCKED


@pytest.mark.asyncio
async def test_timeout_is_bounded_and_persisted():
    with TemporaryDirectory() as directory:
        store = SQLiteStore(Path(directory) / "db.sqlite")
        registry = AgentRegistry()
        registry._agents["switch"] = SwitchAgent(delay=0.2)
        scheduler = Scheduler(registry, store, max_concurrency=1, max_retries=0)
        task = TaskSpec(name="slow", description="slow", agent_name="switch", timeout_seconds=0.02, max_retries=0)
        result = (await scheduler.run([task]))[0]
        assert result.status == TaskStatus.FAILED
        assert "TimeoutError" in result.error
        assert store.list_results()[0].task_id == task.id
