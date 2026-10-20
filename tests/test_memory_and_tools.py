import pytest
from pydantic import BaseModel
from multi_agent.storage.sqlite_store import SQLiteStore
from multi_agent.tools.registry import ToolDefinition, ToolRegistry


class Args(BaseModel):
    value: int


@pytest.mark.asyncio
async def test_tool_permission_enforced():
    async def handler(value: int):
        return value + 1
    registry = ToolRegistry()
    registry.register(ToolDefinition("increment", Args, handler, frozenset({"execute"})))
    with pytest.raises(PermissionError):
        await registry.invoke("increment", {"value": 1}, set())
    assert await registry.invoke("increment", {"value": 1}, {"execute"}) == 2


def test_memory_persistence_and_retrieval(tmp_path):
    store = SQLiteStore(tmp_path / "store.sqlite")
    store.remember("project-a", "Use bounded retries for flaky network requests", "reviewed decision")
    found = store.search_memory("project-a", "bounded retries")
    assert found and found[0]["provenance"] == "reviewed decision"
