# MCP Server List - Project Architecture

## Quick Reference

### Directory Structure
```
mpc-server-list/
├── config/
│   └── mcp_servers.json      # Server registry
├── src/
│   ├── __init__.py
│   ├── catalog_server.py      # MCP catalog exposed over stdio
│   ├── exceptions.py         # Custom exceptions
│   └── router.py             # Core routing engine
├── frontend/
│   ├── index.html             # Server catalog and tool execution UI
│   └── monitor.html           # HTTP/MCP traffic monitor
├── app.py                     # Dashboard and HTTP gateway
├── main.py                   # Demo & entry point
├── requirements.txt          # Dependencies
├── README.md                 # Quick start
├── ARCHITECTURE.md           # This file
└── mcp_architecture_router.md # Detailed design docs
```

## Core Components

### 1. **Dashboard HTTP Gateway** (`app.py`)

`DashboardHandler` serves the static frontend and adapts HTTP requests to the
shared `MCPRouter` instance. The gateway provides:

| Method | Path | Behavior |
| --- | --- | --- |
| `GET` | `/api/servers` | Returns the configured catalog and environment metadata. |
| `GET` | `/api/servers/{server_key}/tools` | Discovers tools through `MCPRouter.list_tools()`. |
| `POST` | `/api/servers/{server_key}/execute` | Calls `MCPRouter.execute_tool()` using `tool_name` and `arguments` from the JSON body. |
| `GET` | `/api/monitor` | Returns the in-memory activity snapshot. |

The listener records gateway requests with status, duration, client address,
protocol metadata, and MCP request/response payloads. It redacts sensitive
headers and ignores requests marked as dashboard polling. The buffer is bounded
to 200 events and is lost when the process stops.

### 2. **MCP Catalog Server** (`src/catalog_server.py`)

The stdio entry point exposes the configured catalog as MCP tools. It delegates
server lookup, tool discovery, and execution to `MCPRouter`, allowing an MCP
client to launch `main.py` without using the HTTP dashboard.

### 3. **MCPRouter** (`src/router.py`)
The main class that handles all MCP server interactions.

**Key Methods:**
- `execute_tool()` - Run a tool on a server
- `list_tools()` - Get available tools
- `get_server_info()` - Get server configuration
- `list_servers()` - Get all registered servers

### 2. **Configuration** (`config/mcp_servers.json`)
JSON catalog defining how to launch each MCP server.

**Schema:**
```json
{
  "server_name": {
    "command": "executable",
    "args": ["arg1", "arg2"],
    "env": { "VAR": "value" },
    "description": "Human-readable description"
  }
}
```

### 3. **Exceptions** (`src/exceptions.py`)
- `MCPException` - Base exception
- `MCPServerNotFoundError` - Server not in catalog
- `MCPConfigurationError` - Configuration file issues

## Design Patterns

| Pattern | Purpose | Implementation |
|---------|---------|-----------------|
| **Gateway Pattern** | Centralized entry point | MCPRouter class |
| **Factory Method** | Abstract server creation | `_build_server_params()` |
| **RAII** | Resource cleanup | `async with` context managers |
| **Separation of Concerns** | Decoupled config & logic | JSON config separate from router |

## Async/Await Pattern

All tool execution uses Python's async/await pattern for non-blocking I/O:

```python
async def execute_tool(server_key, tool_name, arguments):
    # Spawn subprocess
    async with stdio_client(server_params) as (read, write):
        # Initialize MCP session
        async with ClientSession(read, write) as session:
            await session.initialize()
            # Execute tool
            result = await session.call_tool(tool_name, arguments)
            # Auto cleanup on exit
    return result
```

## Execution Flow Diagram

```
┌─────────────┐
│ Client Code │
└─────┬───────┘
      │ await router.execute_tool(server_key, tool, args)
      ↓
┌──────────────────────────┐
│ MCPRouter.execute_tool() │
└─────┬────────────────────┘
      │ Lookup server_key in mcp_servers.json
      ↓
┌────────────────────────┐
│ StdioServerParameters  │
│ (command + args)       │
└─────┬──────────────────┘
      │ Launch subprocess via stdio
      ↓
┌────────────────────────┐
│ MCP Server Process     │
│ (node/python/npx)      │
└─────┬──────────────────┘
      │ JSON-RPC call_tool request
      ↓
┌────────────────────────┐
│ Tool Execution         │
│ (filesystem/fetch/sql) │
└─────┬──────────────────┘
      │ JSON-RPC response
      ↓
┌──────────────────────────┐
│ MCPRouter.execute_tool() │
│ Returns result           │
└─────┬────────────────────┘
      │ await completes
      ↓
┌─────────────┐
│ Client Code │
│ Gets Result │
└─────────────┘
```

## Error Handling

All errors propagate as exceptions:
- **MCPConfigurationError** - Fix config file
- **MCPServerNotFoundError** - Check server_key in config
- **Other exceptions** - Server-specific issues

## Extensibility Points

### Add a New Server
1. Update `config/mcp_servers.json`:
```json
{
  "my_server": {
    "command": "my-command",
    "args": ["--flag"],
    "description": "My server"
  }
}
```

2. Use it:
```python
await router.execute_tool("my_server", "my_tool", {"param": "value"})
```

### Add Environment Variables
```json
{
  "api_server": {
    "command": "my-api",
    "env": {
      "API_KEY": "${API_KEY}",
      "DEBUG": "true"
    }
  }
}
```

### Add Validation
Extend `src/router.py` to validate arguments:
```python
from pydantic import BaseModel, validate_arguments

class FetchArgs(BaseModel):
    url: str

@validate_arguments
async def execute_tool(self, server_key, tool_name, arguments: FetchArgs):
    # arguments.url is validated
    ...
```

### Connection Pooling
Create a pool manager for persistent connections:
```python
class MCPRouterWithPool(MCPRouter):
    def __init__(self, config_path, pool_size=5):
        super().__init__(config_path)
        self.pool = {}  # {server_key: [connections]}
    
    async def get_connection(self, server_key):
        # Reuse existing connection or create new
        ...
```

## Security Considerations

1. **Input Validation** - Sanitize tool arguments
2. **Process Isolation** - Async context managers prevent orphaned processes
3. **Rate Limiting** - Implement throttling for high-frequency calls
4. **Logging** - Audit all tool executions
5. **Environment Secrets** - Use `.env` files or secure vaults

Example with validation:
```python
from typing import Literal

async def execute_tool(
    self,
    server_key: Literal["fetch", "filesystem", "sqlite"],  # Whitelist
    tool_name: str,
    arguments: dict
):
    # Only allowed servers
    if server_key not in self.servers_config:
        raise MCPServerNotFoundError(...)
    
    # Validate arguments (add Pydantic schemas)
    # ...
    
    return await self.execute_tool(server_key, tool_name, arguments)
```

## Performance Tips

1. **Reuse Router Instance** - Create once, use many times
2. **Parallel Execution** - Use `asyncio.gather()` for multiple tools
3. **Connection Pooling** - For high-throughput scenarios
4. **Lazy Loading** - Only initialize servers when needed

Example:
```python
router = MCPRouter()

# Parallel execution
results = await asyncio.gather(
    router.execute_tool("fetch", "fetch", {"url": "..."}),
    router.execute_tool("sqlite", "execute", {"query": "..."}),
    router.execute_tool("filesystem", "read", {"path": "..."})
)
```

## Testing

Unit tests for each component:
```python
# tests/test_router.py
async def test_execute_tool():
    router = MCPRouter("config/test_servers.json")
    result = await router.execute_tool("fetch", "fetch", {"url": "..."})
    assert result is not None

# tests/test_exceptions.py
def test_server_not_found():
    with pytest.raises(MCPServerNotFoundError):
        router.get_server_info("nonexistent")
```

## Deployment

### Local Development
```bash
pip install -r requirements.txt
python main.py
```

### Docker
```dockerfile
FROM python:3.11
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["python", "main.py"]
```

### FastAPI Integration
```python
from fastapi import FastAPI
app = FastAPI()
router = MCPRouter()

@app.post("/tools/{server}/{tool}")
async def api_execute(server: str, tool: str, args: dict):
    return await router.execute_tool(server, tool, args)
```

---

For detailed architecture documentation, see [mcp_architecture_router.md](./mcp_architecture_router.md)
