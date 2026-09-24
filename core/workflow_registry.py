from typing import Dict, Iterable

from core.types import WorkflowDefinition


class WorkflowRegistry:
    """Stores declarative business workflows and resolves them by capability."""

    def __init__(self):
        self._workflows: Dict[str, WorkflowDefinition] = {}

    def register(self, workflow: WorkflowDefinition) -> None:
        if workflow.name in self._workflows:
            raise ValueError(f"Workflow '{workflow.name}' is already registered.")
        self._workflows[workflow.name] = workflow

    def get(self, name: str) -> WorkflowDefinition:
        try:
            return self._workflows[name]
        except KeyError as exc:
            raise KeyError(f"Workflow '{name}' is not registered.") from exc

    def resolve(self, goal: str) -> WorkflowDefinition:
        if not self._workflows:
            raise RuntimeError("No workflows are registered.")

        words = set(goal.lower().split())
        ranked = []
        for workflow in self._workflows.values():
            keywords = set(word.lower() for word in workflow.capabilities)
            score = len(words.intersection(keywords))
            ranked.append((score, workflow))

        score, workflow = max(ranked, key=lambda item: item[0])
        if score == 0 and len(self._workflows) > 1:
            raise LookupError(f"No workflow matches goal: {goal}")
        return workflow

    def names(self) -> Iterable[str]:
        return tuple(self._workflows)