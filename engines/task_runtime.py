import uuid
from typing import Optional


class TaskRecord:
    def __init__(self, goal: str, task_id: Optional[str] = None):
        self.id = task_id or str(uuid.uuid4())
        self.goal = goal
        self.status = "pending"
        self.result = None


class TaskRuntime:
    def __init__(self):
        self._tasks = {}

    async def initialize_task(self, user_goal: str) -> TaskRecord:
        task = TaskRecord(goal=user_goal)
        self._tasks[task.id] = task
        return task

    async def mark_complete(self, task_id: str, result: str) -> None:
        task = self._tasks.get(task_id)
        if task is not None:
            task.status = "completed"
            task.result = result

    async def get_task(self, task_id: str) -> Optional[TaskRecord]:
        return self._tasks.get(task_id)
