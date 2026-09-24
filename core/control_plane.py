from typing import List
from core.types import ToolCall

class ControlPlane:
    def __init__(self, max_steps: int = 50, require_approval_for: List[str] = None):
        self.max_steps = max_steps
        self.require_approval_for = require_approval_for or ["terminal_execute", "file_delete"]

    def validate_step_limit(self, current_step: int) -> None:
        if current_step > self.max_steps:
            raise OverflowError(f"Control Plane Policy Violation: Exceeded max allowed steps ({self.max_steps}).")

    async def request_approval_if_needed(self, tool_call: ToolCall) -> bool:
        if tool_call.name in self.require_approval_for:
            # Emit hook or prompt human supervisor for approval
            return await self._prompt_human_operator(tool_call)
        return True

    async def _prompt_human_operator(self, tool_call: ToolCall) -> bool:
        # Interface hook for web console, CLI prompt, or Slack/Discord integration
        return True