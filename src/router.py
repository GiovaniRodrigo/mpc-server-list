"""
MCP Dynamic Router Engine - Core routing and lifecycle management.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from src.exceptions import MCPConfigurationError, MCPServerNotFoundError


class MCPRouter:
    """
    Dynamic routing engine for managing connections to MCP servers via stdio.
    
    This class provides a centralized gateway for discovering available tools
    and executing them on registered MCP servers.
    
    Attributes:
        config_path (Path): Path to the MCP servers configuration file
        servers_config (Dict[str, Any]): Loaded server configuration
    """

    def __init__(self, config_path: str = "config/mcp_servers.json") -> None:
        """
        Initialize the MCPRouter with a configuration file.
        
        Args:
            config_path: Path to the mcp_servers.json configuration file.
            
        Raises:
            MCPConfigurationError: If the configuration file cannot be loaded.
        """
        self.config_path = Path(config_path)
        self.servers_config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """
        Load and validate the JSON server catalog file.
        
        Returns:
            Dictionary containing the server configurations.
            
        Raises:
            MCPConfigurationError: If the file doesn't exist or JSON is invalid.
        """
        if not self.config_path.exists():
            raise MCPConfigurationError(
                f"Configuration file not found at: {self.config_path.resolve()}"
            )

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise MCPConfigurationError(
                f"Error decoding configuration JSON file: {e}"
            )

    def _build_server_params(self, server_key: str) -> StdioServerParameters:
        """
        Build subprocess parameters for the requested server.
        
        Args:
            server_key: The key identifying the server in the configuration.
            
        Returns:
            StdioServerParameters configured for the specified server.
            
        Raises:
            MCPServerNotFoundError: If the server_key is not in the catalog.
        """
        if server_key not in self.servers_config:
            raise MCPServerNotFoundError(
                f"MCP Server '{server_key}' is not registered in the catalog."
            )

        server_info = self.servers_config[server_key]
        return StdioServerParameters(
            command=server_info["command"],
            args=server_info.get("args", []),
            env=server_info.get("env", None)
        )

    async def execute_tool(
        self,
        server_key: str,
        tool_name: str,
        arguments: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Connect to the specified MCP server, execute a tool, and return the result.
        
        The connection is automatically opened and closed using async context managers
        to ensure clean resource management.
        
        Args:
            server_key: The key identifying the server in the configuration.
            tool_name: The name of the tool to execute.
            arguments: Optional dictionary of arguments to pass to the tool.
            
        Returns:
            The result from the MCP server tool execution.
            
        Raises:
            MCPServerNotFoundError: If the server_key is not registered.
            Exception: Any error raised during tool execution.
        """
        server_params = self._build_server_params(server_key)

        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, arguments or {})
                return result

    async def list_tools(self, server_key: str) -> List[Any]:
        """
        Inspect and return the list of available tools on an MCP server.
        
        Args:
            server_key: The key identifying the server in the configuration.
            
        Returns:
            List of available tools on the specified server.
            
        Raises:
            MCPServerNotFoundError: If the server_key is not registered.
            Exception: Any error raised during tool listing.
        """
        server_params = self._build_server_params(server_key)

        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                response = await session.list_tools()
                return response.tools

    def get_server_info(self, server_key: str) -> Dict[str, Any]:
        """
        Get the configuration information for a registered server.
        
        Args:
            server_key: The key identifying the server in the configuration.
            
        Returns:
            Dictionary containing the server configuration.
            
        Raises:
            MCPServerNotFoundError: If the server_key is not registered.
        """
        if server_key not in self.servers_config:
            raise MCPServerNotFoundError(
                f"MCP Server '{server_key}' is not registered in the catalog."
            )
        return self.servers_config[server_key]

    def list_servers(self) -> List[str]:
        """
        Return a list of all registered server keys.
        
        Returns:
            List of server keys registered in the configuration.
        """
        return list(self.servers_config.keys())
