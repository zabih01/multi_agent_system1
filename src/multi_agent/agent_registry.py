from multi_agent.agents.specialists import SpecialistAgent


class AgentRegistry:
    def __init__(self) -> None:
        self._agents: dict[str, SpecialistAgent] = {}

    def register(self, agent: SpecialistAgent) -> None:
        if agent.name in self._agents:
            raise ValueError(f"Agent already registered: {agent.name}")
        self._agents[agent.name] = agent

    def replace(self, agent: SpecialistAgent) -> None:
        self._agents[agent.name] = agent

    def get(self, name: str) -> SpecialistAgent:
        try:
            return self._agents[name]
        except KeyError as exc:
            raise KeyError(f"Unknown agent: {name}") from exc

    def names(self) -> list[str]:
        return sorted(self._agents)
