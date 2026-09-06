"""
Unit tests for the MCP Router Engine.
Tests cover configuration loading, exception handling, and router functionality.
"""

import pytest
import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.router import MCPRouter
from src.exceptions import (
    MCPException,
    MCPServerNotFoundError,
    MCPConfigurationError
)

CONFIG_PATH = PROJECT_ROOT / "config" / "mcp_servers.json"


class TestConfigurationLoading:
    """Test suite for configuration file loading and validation."""

    def test_load_valid_config(self):
        """Test loading a valid configuration file."""
        router = MCPRouter(CONFIG_PATH)
        assert router.servers_config is not None
        assert isinstance(router.servers_config, dict)
        assert len(router.servers_config) > 0

    def test_config_has_required_servers(self):
        """Test that configuration contains the essential servers."""
        router = MCPRouter(CONFIG_PATH)
        required_servers = ["filesystem", "fetch", "sqlite"]
        for server in required_servers:
            assert server in router.servers_config

    def test_server_has_required_fields(self):
        """Test that each server has required fields."""
        router = MCPRouter(CONFIG_PATH)
        for server_key, server_config in router.servers_config.items():
            assert "command" in server_config
            assert isinstance(server_config["command"], str)
            assert "args" in server_config or "description" in server_config

    def test_invalid_config_path_raises_error(self):
        """Test that invalid config path raises MCPConfigurationError."""
        with pytest.raises(MCPConfigurationError):
            MCPRouter("nonexistent/config.json")

    def test_malformed_json_raises_error(self):
        """Test that malformed JSON raises MCPConfigurationError."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("{invalid json}")
            f.flush()
            
            with pytest.raises(MCPConfigurationError):
                MCPRouter(f.name)
            
            Path(f.name).unlink()


class TestExceptionHierarchy:
    """Test suite for custom exceptions."""

    def test_mcp_exception_is_base_exception(self):
        """Test that MCPException is the base exception."""
        assert issubclass(MCPServerNotFoundError, MCPException)
        assert issubclass(MCPConfigurationError, MCPException)

    def test_server_not_found_exception_message(self):
        """Test MCPServerNotFoundError exception message."""
        exc = MCPServerNotFoundError("Test error")
        assert str(exc) == "Test error"

    def test_configuration_error_message(self):
        """Test MCPConfigurationError exception message."""
        exc = MCPConfigurationError("Config issue")
        assert str(exc) == "Config issue"


class TestRouterFunctionality:
    """Test suite for MCPRouter core functionality."""

    def test_list_servers(self):
        """Test listing all registered servers."""
        router = MCPRouter(CONFIG_PATH)
        servers = router.list_servers()
        assert isinstance(servers, list)
        assert len(servers) > 0
        assert all(isinstance(s, str) for s in servers)

    def test_get_server_info_valid(self):
        """Test getting info for a valid server."""
        router = MCPRouter(CONFIG_PATH)
        info = router.get_server_info("fetch")
        assert info is not None
        assert "command" in info

    def test_get_server_info_invalid_raises_error(self):
        """Test that getting info for invalid server raises error."""
        router = MCPRouter(CONFIG_PATH)
        with pytest.raises(MCPServerNotFoundError):
            router.get_server_info("nonexistent_server")

    def test_build_server_params_valid(self):
        """Test building server parameters for valid server."""
        router = MCPRouter(CONFIG_PATH)
        params = router._build_server_params("fetch")
        assert params is not None
        assert params.command == "uvx"
        assert isinstance(params.args, list)

    def test_build_server_params_invalid_raises_error(self):
        """Test that building params for invalid server raises error."""
        router = MCPRouter(CONFIG_PATH)
        with pytest.raises(MCPServerNotFoundError):
            router._build_server_params("invalid_server")

    def test_server_catalog_completeness(self):
        """Test that all servers have descriptions."""
        router = MCPRouter(CONFIG_PATH)
        for server_key, server_config in router.servers_config.items():
            assert "description" in server_config
            assert len(server_config["description"]) > 0


class TestEnvironmentVariables:
    """Test suite for environment variable handling."""

    def test_servers_with_env_vars(self):
        """Test that servers with env variables are properly configured."""
        router = MCPRouter(CONFIG_PATH)
        
        # Check that some servers have env configuration
        env_servers = [
            server for server, config in router.servers_config.items()
            if "env" in config and config["env"] is not None
        ]
        
        assert len(env_servers) > 0

    def test_env_vars_are_dict(self):
        """Test that env vars are dictionaries with string values."""
        router = MCPRouter(CONFIG_PATH)
        
        for server_key, server_config in router.servers_config.items():
            if "env" in server_config and server_config["env"]:
                assert isinstance(server_config["env"], dict)
                for key, value in server_config["env"].items():
                    assert isinstance(key, str)
                    assert isinstance(value, str)


class TestServerCategories:
    """Test suite for server categorization."""

    def test_development_servers_present(self):
        """Test that development infrastructure servers are present."""
        router = MCPRouter(CONFIG_PATH)
        dev_servers = ["github", "docker", "playwright"]
        present = [s for s in dev_servers if s in router.list_servers()]
        assert len(present) > 0

    def test_database_servers_present(self):
        """Test that database servers are present."""
        router = MCPRouter(CONFIG_PATH)
        db_servers = ["postgresql", "mongodb", "mysql", "sqlite"]
        present = [s for s in db_servers if s in router.list_servers()]
        assert len(present) > 0

    def test_productivity_servers_present(self):
        """Test that productivity servers are present."""
        router = MCPRouter(CONFIG_PATH)
        prod_servers = ["notion", "slack", "stripe"]
        present = [s for s in prod_servers if s in router.list_servers()]
        assert len(present) > 0


class TestConfigurationStructure:
    """Test suite for overall configuration structure."""

    def test_config_is_dict(self):
        """Test that configuration is a dictionary."""
        router = MCPRouter(CONFIG_PATH)
        assert isinstance(router.servers_config, dict)

    def test_min_server_count(self):
        """Test that minimum number of servers are configured."""
        router = MCPRouter(CONFIG_PATH)
        assert len(router.servers_config) >= 20

    def test_all_commands_are_strings(self):
        """Test that all commands are valid strings."""
        router = MCPRouter(CONFIG_PATH)
        for server_key, server_config in router.servers_config.items():
            assert isinstance(server_config["command"], str)
            assert len(server_config["command"]) > 0

    def test_all_args_are_lists(self):
        """Test that all args are lists."""
        router = MCPRouter(CONFIG_PATH)
        for server_key, server_config in router.servers_config.items():
            if "args" in server_config:
                assert isinstance(server_config["args"], list)
                assert all(isinstance(arg, str) for arg in server_config["args"])


# Test execution results tracking
class TestResults:
    """Collect test statistics."""
    
    @staticmethod
    def count_tests():
        """Count total number of test methods."""
        test_classes = [
            TestConfigurationLoading,
            TestExceptionHierarchy,
            TestRouterFunctionality,
            TestEnvironmentVariables,
            TestServerCategories,
            TestConfigurationStructure
        ]
        
        total_tests = 0
        for test_class in test_classes:
            methods = [m for m in dir(test_class) if m.startswith('test_')]
            total_tests += len(methods)
        
        return total_tests
