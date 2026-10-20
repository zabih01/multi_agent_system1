import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

from multi_agent.agent_registry import AgentRegistry
from multi_agent.models import TaskResult, TaskSpec, TaskStatus
from multi_agent.storage.sqlite_store import SQLiteStore
from multi_agent.task_graph import TaskGraph

logger = logging.getLogger(__name__)


class Scheduler:
    def __init__(self, registry: AgentRegistry, store: SQLiteStore, max_concurrency: int = 4, max_retries: int = 2) -> None:
        if max_concurrency < 1:
            raise ValueError("max_concurrency must be at least 1")
        self.registry = registry
        self.store = store
        self.max_concurrency = max_concurrency
        self.semaphore = asyncio.Semaphore(max_concurrency)
        self.max_retries = max_retries

    async def _run_task(self, task: TaskSpec, context: dict[str, Any]) -> TaskResult:
        agent = self.registry.get(task.agent_name)
        started = datetime.now(timezone.utc)
        attempts = 0
        async with self.semaphore:
            while True:
                attempts += 1
                task.status = TaskStatus.RUNNING
                try:
                    output = await asyncio.wait_for(agent.execute(task, context), timeout=task.timeout_seconds)
                    result = TaskResult(task_id=task.id, agent_name=task.agent_name, status=TaskStatus.COMPLETED, output=output, attempts=attempts, started_at=started)
                    self.store.save_result(result)
                    logger.info("task_completed id=%s agent=%s attempts=%s", task.id, task.agent_name, attempts)
                    return result
                except asyncio.CancelledError:
                    task.status = TaskStatus.CANCELLED
                    result = TaskResult(task_id=task.id, agent_name=task.agent_name, status=TaskStatus.CANCELLED, error="Task cancelled", attempts=attempts, started_at=started)
                    self.store.save_result(result)
                    raise
                except Exception as exc:
                    if attempts <= min(task.max_retries, self.max_retries):
                        await asyncio.sleep(min(0.2 * (2 ** (attempts - 1)), 2.0))
                        continue
                    result = TaskResult(task_id=task.id, agent_name=task.agent_name, status=TaskStatus.FAILED, error=f"{type(exc).__name__}: {exc}", attempts=attempts, started_at=started)
                    self.store.save_result(result)
                    logger.exception("task_failed id=%s agent=%s", task.id, agent.name)
                    return result

    async def run(self, tasks: list[TaskSpec], initial_context: dict[str, Any] | None = None) -> list[TaskResult]:
        graph = TaskGraph(tasks)
        context: dict[str, Any] = dict(initial_context or {})
        pending = set(graph.tasks)
        active: dict[str, asyncio.Task[TaskResult]] = {}
        results: dict[str, TaskResult] = {}

        while pending or active:
            completed_ids = {task_id for task_id, result in results.items() if result.status == TaskStatus.COMPLETED}
            for task_id in list(pending):
                task = graph.tasks[task_id]
                failed_deps = [dep for dep in task.dependencies if dep in results and results[dep].status != TaskStatus.COMPLETED]
                if failed_deps:
                    task.status = TaskStatus.BLOCKED
                    result = TaskResult(task_id=task.id, agent_name=task.agent_name, status=TaskStatus.BLOCKED, error=f"Dependency failed: {failed_deps}")
                    results[task_id] = result
                    self.store.save_result(result)
                    pending.remove(task_id)

            ready = graph.ready(completed_ids, set(active))
            for task in ready:
                if task.id in pending and len(active) < self.max_concurrency:
                    dependencies = {dep: results[dep].output for dep in task.dependencies if dep in results}
                    active[task.id] = asyncio.create_task(self._run_task(task, {**context, "dependencies": dependencies}))
                    pending.remove(task.id)
                    task.status = TaskStatus.READY

            if not active:
                if pending:
                    for task_id in list(pending):
                        task = graph.tasks[task_id]
                        result = TaskResult(task_id=task_id, agent_name=task.agent_name, status=TaskStatus.BLOCKED, error="No runnable tasks remain")
                        results[task_id] = result
                        self.store.save_result(result)
                        pending.remove(task_id)
                break

            done, _ = await asyncio.wait(active.values(), return_when=asyncio.FIRST_COMPLETED)
            for future in done:
                task_id = next(key for key, value in active.items() if value is future)
                try:
                    results[task_id] = future.result()
                except asyncio.CancelledError:
                    results[task_id] = TaskResult(task_id=task_id, agent_name=graph.tasks[task_id].agent_name, status=TaskStatus.CANCELLED, error="Task cancelled")
                del active[task_id]

        return [results[task.id] for task in tasks]
