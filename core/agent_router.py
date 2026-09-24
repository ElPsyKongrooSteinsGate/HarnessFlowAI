from dataclasses import dataclass
from typing import AsyncGenerator, Dict, Optional

from core.harness import AgentHarness
from core.types import Event, HarnessConfig, WorkflowDefinition
from core.workflow_registry import WorkflowRegistry
from engines.rag_engine import RAGEngine
from engines.governance_loader import load_governance_csv


@dataclass
class RegisteredAgent:
    name: str
    description: str
    harness: AgentHarness
    workflow: Optional[WorkflowDefinition] = None


class AgentRouter:
    """Registry and dispatcher for governed agent harnesses."""

    def __init__(self):
        self._agents: Dict[str, RegisteredAgent] = {}
        self.workflows = WorkflowRegistry()
        self.rag_engine = RAGEngine()
        self.governance_documents_loaded = load_governance_csv(self.rag_engine)

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

    def register_workflow(self, workflow: WorkflowDefinition) -> None:
        """Register a business workflow and create its governed worker."""
        self.workflows.register(workflow)
        workflow_documents = workflow.workflow_documents or [
            f"Workflow: {workflow.name}. {workflow.description}. "
            f"Steps: {', '.join(step.name for step in workflow.steps)}."
        ]
        for document in workflow_documents:
            self.rag_engine.add_document(
                content=document,
                collection=workflow.workflow_collection,
                metadata={"workflow": workflow.name, "knowledge_type": "workflow"},
            )
        for document in workflow.governance_documents:
            self.rag_engine.add_document(
                content=document,
                collection=workflow.governance_collection,
                metadata={"workflow": workflow.name, "knowledge_type": "governance"},
            )
        self._agents[workflow.name] = RegisteredAgent(
            name=workflow.name,
            description=workflow.description,
            workflow=workflow,
            harness=AgentHarness(
                HarnessConfig(
                    system_prompt=workflow.system_prompt,
                    max_steps=workflow.max_steps,
                    allowed_tools=workflow.allowed_tools,
                    approval_tools=workflow.approval_tools,
                ),
                rag_engine=self.rag_engine,
                workflow_name=workflow.name,
                workflow_collection=workflow.workflow_collection,
                governance_collection=workflow.governance_collection,
            ),
        )

    def add_workflow_document(
        self,
        workflow_name: str,
        content: str,
        source: str = "user-input",
    ) -> None:
        """Add user-provided domain knowledge to a registered workflow."""
        agent = self._agents.get(workflow_name)
        if agent is None or agent.workflow is None:
            raise KeyError(f"Workflow '{workflow_name}' is not registered.")
        self.rag_engine.add_document(
            content=content,
            collection=agent.workflow.workflow_collection,
            metadata={
                "workflow": workflow_name,
                "knowledge_type": "workflow",
                "source": source,
            },
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
        if agent_name is None and self.workflows.names():
            try:
                workflow = self.workflows.resolve(goal)
                return self._agents[workflow.name]
            except LookupError:
                pass

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
