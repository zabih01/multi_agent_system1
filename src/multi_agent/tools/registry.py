import asyncio
from dataclasses import dataclass
from typing import Any, Awaitable, Callable
from pydantic import BaseModel


@dataclass
class ToolDefinition:
    name: str
    input_model: type[BaseModel]
    handler: Callable[..., Awaitable[Any]]
    permissions: frozenset[str]
    timeout_seconds: float = 10.0


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}

    def register(self, definition: ToolDefinition) -> None:
        if definition.name in self._tools:
            raise ValueError(f"Tool already registered: {definition.name}")
        self._tools[definition.name] = definition

    async def invoke(self, name: str, payload: dict[str, Any], granted_permissions: set[str]) -> Any:
        if name not in self._tools:
            raise KeyError(f"Unknown tool: {name}")
        definition = self._tools[name]
        if not definition.permissions.issubset(granted_permissions):
            raise PermissionError(f"Missing permissions for tool {name}: {sorted(definition.permissions - granted_permissions)}")
        validated = definition.input_model.model_validate(payload)
        return await asyncio.wait_for(definition.handler(**validated.model_dump()), timeout=definition.timeout_seconds)

    def names(self) -> list[str]:
        return sorted(self._tools)
