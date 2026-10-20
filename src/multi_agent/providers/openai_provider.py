from .base import LLMProvider


class OpenAIProvider:
    def __init__(self, api_key: str, model: str = "gpt-4o-mini") -> None:
        if not api_key:
            raise ValueError("An OpenAI API key is required")
        try:
            from openai import AsyncOpenAI
        except ImportError as exc:
            raise RuntimeError("Install the optional dependency: uv add --extra openai openai") from exc
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model

    async def complete(self, *, system: str, prompt: str) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
        )
        content = response.choices[0].message.content
        return content or ""
