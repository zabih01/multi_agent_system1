from typing import Protocol


class LLMProvider(Protocol):
    async def complete(self, *, system: str, prompt: str) -> str: ...
