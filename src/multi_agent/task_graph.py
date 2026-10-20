from collections import defaultdict, deque
from multi_agent.models import TaskSpec


class TaskGraph:
    def __init__(self, tasks: list[TaskSpec]) -> None:
        self.tasks = {task.id: task for task in tasks}
        if len(self.tasks) != len(tasks):
            raise ValueError("Duplicate task IDs are not allowed")
        for task in tasks:
            missing = set(task.dependencies) - self.tasks.keys()
            if missing:
                raise ValueError(f"Task {task.id} has unknown dependencies: {sorted(missing)}")
            if task.id in task.dependencies:
                raise ValueError("A task cannot depend on itself")
        self._validate_acyclic()

    def _validate_acyclic(self) -> None:
        indegree = {task_id: 0 for task_id in self.tasks}
        children: dict[str, list[str]] = defaultdict(list)
        for task in self.tasks.values():
            for dependency in task.dependencies:
                indegree[task.id] += 1
                children[dependency].append(task.id)
        queue = deque(task_id for task_id, degree in indegree.items() if degree == 0)
        visited = 0
        while queue:
            current = queue.popleft()
            visited += 1
            for child in children[current]:
                indegree[child] -= 1
                if indegree[child] == 0:
                    queue.append(child)
        if visited != len(self.tasks):
            raise ValueError("Task dependencies contain a cycle")

    def ready(self, completed: set[str], active: set[str]) -> list[TaskSpec]:
        ready = [
            task for task in self.tasks.values()
            if task.id not in completed and task.id not in active
            and all(dep in completed for dep in task.dependencies)
        ]
        return sorted(ready, key=lambda task: (-task.priority, task.created_at))
