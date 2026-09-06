"""
Custom exceptions for the MCP Router Engine.
"""


class MCPException(Exception):
    """Base exception for all MCP Router errors."""
    pass


class MCPServerNotFoundError(MCPException):
    """Raised when the MCP server key is not found in the catalog."""
    pass


class MCPConfigurationError(MCPException):
    """Raised when there is an inconsistency in reading the configuration file."""
    pass
