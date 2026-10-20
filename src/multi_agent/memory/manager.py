from multi_agent.storage.sqlite_store import SQLiteStore


class MemoryManager:
    def __init__(self, store: SQLiteStore, project: str = "default") -> None:
        self.store = store
        self.project = project
        self.short_term: dict[str, list[str]] = {}

    def add_task_context(self, task_id: str, content: str) -> None:
        self.short_term.setdefault(task_id, []).append(content)

    def task_context(self, task_id: str) -> list[str]:
        return list(self.short_term.get(task_id, []))

    def remember(self, content: str, provenance: str) -> None:
        self.store.remember(self.project, content, provenance)

    def retrieve(self, query: str, limit: int = 5) -> list[dict]:
        return self.store.search_memory(self.project, query, limit)
