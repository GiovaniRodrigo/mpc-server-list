"""
Entry point and example usage of the MCP Dynamic Router Engine.

This script demonstrates:
1. Loading the MCP server configuration
2. Listing available tools on a server
3. Executing a tool with arguments
"""

import asyncio
from src.router import MCPRouter
from src.exceptions import MCPException


async def run_demo():
    """Run a demonstration of the MCP Router functionality."""
    
    try:
        # Initialize the router with the configuration
        router = MCPRouter("config/mcp_servers.json")
        
        # Display all registered servers
        print("=== Registered MCP Servers ===")
        servers = router.list_servers()
        for server_key in servers:
            server_info = router.get_server_info(server_key)
            print(f"\n📍 {server_key}")
            print(f"   Command: {server_info['command']}")
            print(f"   Description: {server_info.get('description', 'N/A')}")
        
        # Example 1: List tools from a server
        server_target = "fetch"
        print(f"\n=== Tools Available in '{server_target}' Server ===")
        try:
            tools = await router.list_tools(server_target)
            for tool in tools:
                print(f"\n- {tool.name}")
                print(f"  Description: {tool.description}")
                if hasattr(tool, 'inputSchema'):
                    print(f"  Input Schema: {tool.inputSchema}")
        except Exception as e:
            print(f"⚠️  Could not list tools: {e}")
            print("   (Make sure the server is properly installed and configured)")
        
        # Example 2: Execute a tool (requires the server to be available)
        print(f"\n=== Executing Tool on '{server_target}' Server ===")
        try:
            response = await router.execute_tool(
                server_key="fetch",
                tool_name="fetch",
                arguments={"url": "https://httpbin.org/get"}
            )
            
            print("\n✅ Response received from MCP:")
            if response.content:
                content = response.content[0].text
                # Print first 500 characters to avoid too much output
                print(content[:500] + "..." if len(content) > 500 else content)
        except Exception as e:
            print(f"⚠️  Could not execute tool: {e}")
            print("   (Make sure the server is running or properly configured)")

    except MCPException as err:
        print(f"❌ [MCP Error]: {err}")
    except Exception as err:
        print(f"❌ [Unexpected Error]: {err}")


if __name__ == "__main__":
    print("🚀 MCP Dynamic Router Engine - Demo\n")
    asyncio.run(run_demo())
    print("\n✨ Demo completed!")
