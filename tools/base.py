from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class ToolExecutionResult(BaseModel):
    tool_name: str
    output: str
    success: bool = True


class ToolRuntime:
    def __init__(self, allowed_tools: Optional[List[str]] = None):
        self.allowed_tools = allowed_tools or []
        self.local_tools: Dict[str, Any] = {}

    def register(self, name: str, tool: Any) -> None:
        self.local_tools[name] = tool

    def get_schemas(self) -> List[Dict[str, Any]]:
        return []

    async def execute(self, tool_call: Any) -> ToolExecutionResult:
        if tool_call.name not in self.allowed_tools and self.allowed_tools:
            return ToolExecutionResult(
                tool_name=tool_call.name,
                output=f"Tool '{tool_call.name}' is not allowed.",
                success=False,
            )
        return ToolExecutionResult(tool_name=tool_call.name, output="Tool execution stubbed successfully.", success=True)
