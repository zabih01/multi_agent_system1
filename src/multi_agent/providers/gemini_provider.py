
from google import genai

from multi_agent.providers.base import LLMProvider


class GeminiProvider:
    def __init__(self, api_key: str, model: str) -> None:
        self.client = genai.Client(api_key=api_key)
        self.model = model

    async def complete(self, *, system: str, prompt: str) -> str:
        response = await self.client.aio.models.generate_content(
            model=self.model,
            contents=prompt,
            config={
                "system_instruction": system,
            },
        )

        return response.text or ""
