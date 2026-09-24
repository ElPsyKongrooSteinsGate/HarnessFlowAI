import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class MCPToolSchema(BaseModel):
    """Standardized representation of an MCP tool definition."""
    server_name: str
    original_name: str
    namespaced_name: str  # e.g., "mcp__filesystem__read_file"
    description: str
    input_schema: Dict[str, Any]


class MCPServerConfig(BaseModel):
    """Configuration for an external MCP server connection."""
    name: str
    transport: str = Field(..., description="Transport protocol: 'stdio' or 'sse'")
    command: Optional[str] = None  # Required for 'stdio'
    args: List[str] = Field(default_factory=list)
    env: Dict[str, str] = Field(default_factory=dict)
    url: Optional[str] = None      # Required for 'sse'


class MCPClientAdapter:
    """
    Adapter interfacing the Agent Harness with Model Context Protocol (MCP) servers.
    Handles discovery, JSON Schema translation, and remote tool execution.
    """

    def __init__(self, server_configs: List[MCPServerConfig]):
        self.configs = server_configs
        self.discovered_tools: Dict[str, MCPToolSchema] = {}
        self._processes: Dict[str, asyncio.subprocess.Process] = {}

    async def connect_all(self) -> None:
        """Initialize connections to all configured MCP servers and discover tools."""
        for config in self.configs:
            if config.transport == "stdio":
                await self._connect_stdio(config)
            elif config.transport == "sse":
                await self._connect_sse(config)
            else:
                logger.error(f"Unsupported MCP transport: {config.transport}")

    async def _connect_stdio(self, config: MCPServerConfig) -> None:
        """Establishes an MCP STDIO transport process connection."""
        if not config.command:
            raise ValueError(f"STDIO transport for '{config.name}' requires a command.")

        try:
            process = await asyncio.create_subprocess_exec(
                config.command,
                *config.args,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={**config.env}
            )
            self._processes[config.name] = process

            # Step 1: Protocol Handshake (initialize)
            init_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "clientInfo": {"name": "AgentHarnessAdapter", "version": "1.0.0"}
                }
            }
            init_response = await self._send_json_rpc(config.name, init_request)
            
            # Send initialized notification
            await self._send_notification(config.name, {"jsonrpc": "2.0", "method": "notifications/initialized"})

            # Step 2: Tool Discovery (tools/list)
            list_tools_req = {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}
            tools_response = await self._send_json_rpc(config.name, list_tools_req)

            # Register tools in memory with namespacing to avoid collisions
            for tool in tools_response.get("result", {}).get("tools", []):
                namespaced_name = f"mcp__{config.name}__{tool['name']}"
                schema = MCPToolSchema(
                    server_name=config.name,
                    original_name=tool["name"],
                    namespaced_name=namespaced_name,
                    description=tool.get("description", ""),
                    input_schema=tool.get("inputSchema", {"type": "object", "properties": {}})
                )
                self.discovered_tools[namespaced_name] = schema
                logger.info(f"Registered MCP tool: {namespaced_name}")

        except Exception as e:
            logger.error(f"Failed to connect to MCP server '{config.name}': {e}")

    async def _connect_sse(self, config: MCPServerConfig) -> None:
        """Placeholder for HTTP SSE transport connection."""
        # Implements HTTP SSE stream client initialization & tool discovery
        pass

    async def execute_tool(self, namespaced_name: str, arguments: Dict[str, Any]) -> str:
        """Executes a tool call over the corresponding MCP connection."""
        if namespaced_name not in self.discovered_tools:
            raise KeyError(f"MCP tool '{namespaced_name}' is not registered.")

        tool = self.discovered_tools[namespaced_name]
        request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": tool.original_name,
                "arguments": arguments
            }
        }

        response = await self._send_json_rpc(tool.server_name, request)
        
        # Parse MCP CallToolResult structure
        result = response.get("result", {})
        if response.get("error"):
            return f"MCP Error: {response['error'].get('message')}"
        
        content_blocks = result.get("content", [])
        output_text = []
        for block in content_blocks:
            if block.get("type") == "text":
                output_text.append(block.get("text", ""))
        
        return "\n".join(output_text) if output_text else "Tool executed with no output."

    def get_openai_tool_schemas(self) -> List[Dict[str, Any]]:
        """Converts discovered MCP tools into standard OpenAI/Anthropic tool definitions."""
        schemas = []
        for namespaced_name, tool in self.discovered_tools.items():
            schemas.append({
                "type": "function",
                "function": {
                    "name": namespaced_name,
                    "description": tool.description,
                    "parameters": tool.input_schema
                }
            })
        return schemas

    async def _send_json_rpc(self, server_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Utility method to send JSON-RPC over STDIO."""
        proc = self._processes.get(server_name)
        if not proc or proc.stdin is None or proc.stdout is None:
            raise RuntimeError(f"Server process for '{server_name}' unavailable.")

        data = json.dumps(payload) + "\n"
        proc.stdin.write(data.encode("utf-8"))
        await proc.stdin.drain()

        line = await proc.stdout.readline()
        if not line:
            raise ConnectionResetError(f"No response from MCP server '{server_name}'")
        
        return json.loads(line.decode("utf-8"))

    async def _send_notification(self, server_name: str, payload: Dict[str, Any]) -> None:
        proc = self._processes.get(server_name)
        if proc and proc.stdin:
            data = json.dumps(payload) + "\n"
            proc.stdin.write(data.encode("utf-8"))
            await proc.stdin.drain()

    async def close_all(self) -> None:
        """Clean termination of sub-processes."""
        for proc in self._processes.values():
            if proc.returncode is None:
                proc.terminate()
                await proc.wait()