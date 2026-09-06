# MCP Server List - Dynamic Router Engine

A centralized catalog and dynamic routing engine for **Model Context Protocol (MCP)** servers. This project abstracts the initialization, communication, and execution of tools offered by both public and private MCP servers, functioning as a gateway or API catalog for MCP connections.

## 🎯 Overview

The **MCP Dynamic Router Engine** provides:
- **Centralized server registry** via JSON configuration
- **Dynamic connection management** through stdio-based sub-processes
- **Tool execution abstraction** across multiple MCP servers
- **Clean lifecycle management** with async context managers
- **Extensible architecture** supporting various server types

## 📁 Project Structure

```
mpc-server-list/
│
├── config/
│   └── mcp_servers.json       # Catalog of registered MCP servers
│
├── src/
│   ├── __init__.py
│   ├── config.py              # Configuration parsing and validation
│   ├── exceptions.py           # Custom application exceptions
│   └── router.py              # Core routing engine and lifecycle management
│
├── main.py                    # Entry point and execution example
├── requirements.txt           # Project dependencies
├── mcp_architecture_router.md # Detailed architecture documentation
└── README.md                  # This file
```

## 🏗️ Architecture Patterns

### Design Patterns Applied

1. **Gateway Pattern / Dynamic Router**
   - Centralized point for receiving calls and dynamic dispatch based on `server_key`

2. **Factory Method / Adapter Pattern**
   - Abstracts creation and initialization of subprocess commands (`StdioServerParameters`)
   - Supports various execution methods (`npx`, `uvx`, `python`)

3. **Resource Acquisition Is Initialization (RAII)**
   - Asynchronous lifecycle management via async context managers
   - Ensures clean subprocess termination without orphaned processes

4. **Separation of Concerns (SoC)**
   - Server connection specifications (`mcp_servers.json`) are fully decoupled from the execution engine (`MCPRouter`)

## 🚀 Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Configuration

Create or edit `config/mcp_servers.json`:

```json
{
  "filesystem": {
    "command": "npx",
    "args": [
      "-y",
      "@modelcontextprotocol/server-filesystem",
      "./data"
    ],
    "description": "MCP Server for local file manipulation in ./data folder"
  },
  "fetch": {
    "command": "uvx",
    "args": ["mcp-server-fetch"],
    "description": "MCP Server for HTTP requests and web content extraction"
  },
  "sqlite": {
    "command": "uvx",
    "args": ["mcp-server-sqlite", "--db-path", "./database.db"],
    "description": "MCP Server for SQLite database access and queries"
  }
}
```

### Usage

```bash
python main.py
```

Example code:

```python
import asyncio
from src.router import MCPRouter

async def main():
    router = MCPRouter("config/mcp_servers.json")
    
    # List available tools
    tools = await router.list_tools("fetch")
    for tool in tools:
        print(f"- {tool.name}: {tool.description}")
    
    # Execute a tool
    result = await router.execute_tool(
        server_key="fetch",
        tool_name="fetch",
        arguments={"url": "https://httpbin.org/get"}
    )
    print(result.content[0].text)

asyncio.run(main())
```

## 📦 Dependencies

- `mcp>=1.0.0` - Model Context Protocol SDK
- `pydantic>=2.0.0` - Data validation and settings management

## 🔧 API Reference

### `MCPRouter` Class

#### Methods

**`__init__(config_path: str = "config/mcp_servers.json")`**
- Initializes the router with the provided configuration file

**`async execute_tool(server_key: str, tool_name: str, arguments: Optional[Dict[str, Any]] = None) -> Any`**
- Connects to the specified MCP server, executes the tool, and returns the result

**`async list_tools(server_key: str) -> List[Any]`**
- Returns the list of available tools on a specified MCP server

### Exceptions

- `MCPException` - Base exception for all MCP Router errors
- `MCPServerNotFoundError` - Raised when server key is not in the catalog
- `MCPConfigurationError` - Raised when configuration file has issues

## 📚 Documentation

For detailed architecture documentation, design patterns, and implementation details, see [mcp_architecture_router.md](./mcp_architecture_router.md).

## 🛠️ Best Practices & Extensibility

### Environment Variables
Extend `mcp_servers.json` to accept API tokens and secrets dynamically via the `env` field:

```json
{
  "api_server": {
    "command": "npx",
    "args": ["@mcp/server-api"],
    "env": {
      "API_TOKEN": "${API_TOKEN}",
      "API_KEY": "${API_KEY}"
    }
  }
}
```

### Connection Pooling
For high-throughput scenarios, replace the point-in-time async context manager creation with a Pool Manager maintaining persistent background connections.

### Schema Validation
Integrate Pydantic for input parameter validation before passing to the `call_tool` layer.

## 📝 Execution Flow

```
┌──────────────┐        1. Request Execution      ┌────────────────┐
│ Client / LLM │ ────────────────────────────────> │ MCP Router     │
└──────────────┘  (server_key, tool_name, args)   │ Engine         │
                                                   └────────────────┘
                                                           │
                                                  2. Query Config
                                                           ↓
                                                   ┌────────────────┐
                                                   │mcp_servers.json│
                                                   └────────────────┘
                                                           │
                                                  3. Start Subprocess
                                                           ↓
                                                   ┌────────────────┐
                                                   │ MCP Server     │
                                                   │ Process        │
                                                   └────────────────┘
                                                           │
                                                  4. Call Tool (JSON-RPC)
                                                           ↓
┌──────────────┐        5. Result                 ┌────────────────┐
│ Response     │ <──────────────────────────────── │ Tool Execution │
│ (Text/JSON)  │        (Content)                 └────────────────┘
└──────────────┘
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues or pull requests to improve the project.

## 📄 License

This project is open source and available under the MIT License.

## 🔗 Resources

- [Model Context Protocol Documentation](https://modelcontextprotocol.io/)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)

---

**Author:** [GiovaniRodrigo](https://github.com/GiovaniRodrigo)  
**Last Updated:** 2026-09-06
