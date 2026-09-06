"""MCP server exposing the configured catalog through the router."""

import json
from typing import Any, Dict, Optional

from mcp.server.mcpserver import MCPServer

from src.router import MCPRouter


class CatalogMCPServer:
    """Expose catalog and delegated tool execution as MCP tools."""

    def __init__(self, config_path: str = "config/mcp_servers.json") -> None:
        self.router = MCPRouter(config_path)
        self.server = MCPServer(
            name="mcp-server-list",
            title="MCP Server List",
            description="Catalog and gateway for configured MCP servers.",
            version="1.0.0",
        )
        self._register_tools()

    def _register_tools(self) -> None:
        @self.server.tool(
            name="list_servers",
            description="List all MCP servers registered in the catalog.",
        )
        async def list_servers() -> str:
            catalog = [
                {
                    "key": key,
                    "description": self.router.get_server_info(key).get("description", ""),
                }
                for key in self.router.list_servers()
            ]
            return json.dumps({"servers": catalog}, ensure_ascii=False)

        @self.server.tool(
            name="list_server_tools",
            description="Discover tools exposed by one registered MCP server.",
        )
        async def list_server_tools(server_key: str) -> str:
            tools = await self.router.list_tools(server_key)
            return json.dumps(
                {"server_key": server_key, "tools": [self._serialize(tool) for tool in tools]},
                ensure_ascii=False,
                default=self._serialize,
            )

        @self.server.tool(
            name="execute_server_tool",
            description="Execute a tool on one registered MCP server.",
        )
        async def execute_server_tool(
            server_key: str,
            tool_name: str,
            arguments: Optional[Dict[str, Any]] = None,
        ) -> str:
            result = await self.router.execute_tool(server_key, tool_name, arguments or {})
            return json.dumps(
                {"server_key": server_key, "tool_name": tool_name, "result": self._serialize(result)},
                ensure_ascii=False,
                default=self._serialize,
            )

    @staticmethod
    def _serialize(value: Any) -> Any:
        if hasattr(value, "model_dump"):
            return value.model_dump(mode="json")
        if hasattr(value, "__dict__"):
            return value.__dict__
        return value

    async def run_stdio(self) -> None:
        """Run as a standalone MCP server over stdio."""
        await self.server.run_stdio_async()
