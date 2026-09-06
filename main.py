"""Standalone MCP catalog server entrypoint."""

import asyncio

from src.catalog_server import CatalogMCPServer


if __name__ == "__main__":
    asyncio.run(CatalogMCPServer().run_stdio())
