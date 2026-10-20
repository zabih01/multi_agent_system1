from typing import Any
from multi_agent.models import ReviewFeedback, TaskSpec
from multi_agent.providers.base import LLMProvider


class SpecialistAgent:
    def __init__(self, name: str, provider: LLMProvider, role: str) -> None:
        self.name = name
        self.provider = provider
        self.role = role

    async def plan(self, objective: str) -> list[TaskSpec]:
        return [TaskSpec(name=f"{self.name}-task", description=objective, agent_name=self.name)]

    async def execute(self, task: TaskSpec, context: dict[str, Any]) -> Any:
        prompt = f"Task: {task.description}\nInput: {task.input_data}\nContext: {context}"
        return await self.provider.complete(system=self.role, prompt=prompt)

    async def review(self, content: str) -> ReviewFeedback:
        verdict = await self.provider.complete(
            system="Review outputs for clarity, correctness, and unsupported claims. Return concise feedback.",
            prompt=content,
        )
        return ReviewFeedback(approved=True, score=0.8, findings=[verdict])

    async def communicate(self, message: str, recipient: str | None = None) -> str:
        return f"{self.name} -> {recipient or 'orchestrator'}: {message}"

    async def cancel(self, task_id: str) -> None:
        return None
