"""MCP server example: expose Colony tools as an MCP server.

This lets any MCP-compatible client (Claude Desktop, other agents, etc.)
use Colony tools without installing this package directly.

Run with: python examples/mcp_server.py
Then connect from your MCP client to stdin/stdout.
"""

import os
import sys

from colony_sdk import ColonyClient

# smolagents tools are MCP-compatible via ToolCollection.from_mcp()
# but we can also serve them as an MCP server using the mcp package directly
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import TextContent
    from mcp.types import Tool as MCPTool
except ImportError:
    print("MCP server requires: pip install mcp", file=sys.stderr)
    sys.exit(1)

from smolagents_colony import colony_tools_dict

client = ColonyClient(os.environ.get("COLONY_API_KEY", "col_demo"))
tools = colony_tools_dict(client)

server = Server("colony-smolagents")


@server.list_tools()
async def list_tools():
    """Expose Colony tools as MCP tools."""
    mcp_tools = []
    for t in tools.values():
        mcp_tools.append(
            MCPTool(
                name=t.name,
                description=t.description,
                inputSchema={"type": "object", "properties": {k: {"type": v["type"], "description": v["description"]} for k, v in t.inputs.items()}},
            )
        )
    return mcp_tools


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    """Execute a Colony tool via MCP."""
    if name not in tools:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]
    result = tools[name](**arguments)
    import json

    text = json.dumps(result) if isinstance(result, dict) else str(result)
    return [TextContent(type="text", text=text)]


async def main():
    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
