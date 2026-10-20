import asyncio


class MockProvider:
    async def complete(self, *, system: str, prompt: str) -> str:
        await asyncio.sleep(0)
        return f"[{system}] {prompt[:1200]}"
