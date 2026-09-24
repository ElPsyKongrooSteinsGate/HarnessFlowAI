from dataclasses import dataclass
from typing import AsyncGenerator, Dict, Optional

from core.harness import AgentHarness
from core.types import Event, HarnessConfig


@dataclass
class RegisteredAgent:
    name: str
    description: str
    harness: AgentHarness


class AgentRouter:
    """Registry and dispatcher for governed agent harnesses."""

    def __init__(self):
        self._agents: Dict[str, RegisteredAgent] = {}

    def register(
        self,
        name: str,
        config: HarnessConfig,
        description: str = "",
    ) -> None:
        if name in self._agents:
            raise ValueError(f"Agent '{name}' is already registered.")
        self._agents[name] = RegisteredAgent(
            name=name,
            description=description,
            harness=AgentHarness(config),
        )

    def select(self, user_goal: str, agent_name: Optional[str] = None) -> RegisteredAgent:
        if not self._agents:
            raise RuntimeError("No agents are registered.")

        if agent_name is not None:
            try:
                return self._agents[agent_name]
            except KeyError as exc:
                raise KeyError(f"Agent '{agent_name}' is not registered.") from exc

        goal = user_goal.lower()
        for agent in self._agents.values():
            keywords = agent.description.lower().split()
            if any(keyword in goal for keyword in keywords if len(keyword) > 3):
                return agent

        return next(iter(self._agents.values()))

    async def run(
        self,
        user_goal: str,
        agent_name: Optional[str] = None,
    ) -> AsyncGenerator[Event, None]:
        agent = self.select(user_goal, agent_name)
        async for event in agent.harness.run(user_goal):
            yield event

    def names(self):
        return tuple(self._agents)
