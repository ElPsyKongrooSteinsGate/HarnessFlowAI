from typing import List, Optional, Tuple
from core.types import ToolCall


class ControlPlane:
    def __init__(self, max_steps: int = 50, require_approval_for: Optional[List[str]] = None):
        self.max_steps = max_steps
        self.require_approval_for = require_approval_for or ["terminal_execute", "file_delete"]

    def validate_step_limit(self, current_step: int) -> None:
        if current_step > self.max_steps:
            raise OverflowError(f"Control Plane Policy Violation: Exceeded max allowed steps ({self.max_steps}).")

    def check_tool_policy(
        self, tool_call: ToolCall, allowed_tools: Optional[List[str]] = None
    ) -> Tuple[bool, str]:
        if allowed_tools and tool_call.name not in allowed_tools:
            return False, f"Tool '{tool_call.name}' is not allowed by the agent policy."
        return True, "Tool is allowed by the agent policy."

    async def request_approval_if_needed(self, tool_call: ToolCall) -> bool:
        if tool_call.name in self.require_approval_for:
            # Emit hook or prompt human supervisor for approval
            return await self._prompt_human_operator(tool_call)
        return True

    async def _prompt_human_operator(self, tool_call: ToolCall) -> bool:
        # Interface hook for web console, CLI prompt, or Slack/Discord integration
        return True