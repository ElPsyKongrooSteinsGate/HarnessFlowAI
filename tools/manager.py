from typing import List, Dict, Any
from pydantic import BaseModel
from tools.mcp_adapter import MCPClientAdapter, MCPServerConfig
from core.types import ToolCall


class ToolExecutionResult(BaseModel):
    tool_name: str
    output: str
    success: bool = True


class ToolManager:
    """
    Unified manager routing tool execution requests to either
    local python functions or external MCP protocol adapters.
    """

    def __init__(self, mcp_configs: List[MCPServerConfig]):
        self.mcp_adapter = MCPClientAdapter(mcp_configs)
        self.local_tools: Dict[str, Any] = {}

    async def initialize(self) -> None:
        """Connect to external MCP infrastructure."""
        await self.mcp_adapter.connect_all()

    def get_all_schemas(self) -> List[Dict[str, Any]]:
        """Aggregates tool schemas from local tools and MCP servers."""
        schemas = []
        # Add local tool schemas
        for name, tool in self.local_tools.items():
            schemas.append(tool.schema)

        # Add MCP tool schemas
        schemas.extend(self.mcp_adapter.get_openai_tool_schemas())
        return schemas

    async def execute(self, tool_call: ToolCall) -> ToolExecutionResult:
        """Routes execution based on name prefix."""
        try:
            if tool_call.name.startswith("mcp__"):
                output = await self.mcp_adapter.execute_tool(tool_call.name, tool_call.args)
            elif tool_call.name in self.local_tools:
                output = await self.local_tools[tool_call.name].execute(tool_call.args)
            else:
                output = f"Error: Tool '{tool_call.name}' not found."
                return ToolExecutionResult(tool_name=tool_call.name, output=output, success=False)

            return ToolExecutionResult(tool_name=tool_call.name, output=output, success=True)
        except Exception as exc:
            return ToolExecutionResult(
                tool_name=tool_call.name, output=f"Execution error: {str(exc)}", success=False
            )