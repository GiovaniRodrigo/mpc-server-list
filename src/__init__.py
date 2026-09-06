"""
MCP Dynamic Router Engine - A centralized catalog and routing engine for Model Context Protocol servers.
"""

__version__ = "1.0.0"
__author__ = "GiovaniRodrigo"
__license__ = "MIT"

from src.router import MCPRouter
from src.exceptions import MCPException, MCPServerNotFoundError, MCPConfigurationError

__all__ = [
    "MCPRouter",
    "MCPException",
    "MCPServerNotFoundError",
    "MCPConfigurationError",
]
