import json
import sqlite3
from pathlib import Path
from typing import Any
from multi_agent.models import TaskResult


class SQLiteStore:
    def __init__(self, path: Path | str) -> None:
        self.path = str(path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute("CREATE TABLE IF NOT EXISTS task_results (task_id TEXT PRIMARY KEY, status TEXT NOT NULL, payload TEXT NOT NULL)")
            connection.execute("CREATE TABLE IF NOT EXISTS memories (id INTEGER PRIMARY KEY AUTOINCREMENT, project TEXT NOT NULL, content TEXT NOT NULL, provenance TEXT NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP)")

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path, timeout=10)

    def save_result(self, result: TaskResult) -> None:
        payload = result.model_dump_json()
        with self._connect() as connection:
            connection.execute("INSERT OR REPLACE INTO task_results(task_id, status, payload) VALUES (?, ?, ?)", (result.task_id, result.status.value, payload))

    def list_results(self) -> list[TaskResult]:
        with self._connect() as connection:
            rows = connection.execute("SELECT payload FROM task_results ORDER BY rowid").fetchall()
        return [TaskResult.model_validate_json(row[0]) for row in rows]

    def remember(self, project: str, content: str, provenance: str) -> None:
        with self._connect() as connection:
            connection.execute("INSERT INTO memories(project, content, provenance) VALUES (?, ?, ?)", (project, content, provenance))

    def search_memory(self, project: str, query: str, limit: int = 5) -> list[dict[str, Any]]:
        terms = [term for term in query.lower().split() if len(term) > 2]
        with self._connect() as connection:
            rows = connection.execute("SELECT content, provenance, created_at FROM memories WHERE project = ? ORDER BY id DESC", (project,)).fetchall()
        scored = []
        for content, provenance, created_at in rows:
            score = sum(term in content.lower() for term in terms)
            if score:
                scored.append((score, {"content": content, "provenance": provenance, "created_at": created_at}))
        return [item for _, item in sorted(scored, key=lambda pair: pair[0], reverse=True)[:limit]]
