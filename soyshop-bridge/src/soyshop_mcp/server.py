"""SoyShop Bridge MCP server - stdio transport."""

from __future__ import annotations

import asyncio
import json
import logging
import sys
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from .client import SoyShopClient
from .tools import (
    version,
    search_items,
    get_item,
    create_draft_item,
    update_item,
    change_open,
    list_categories,
)


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("soyshop-mcp")


TOOLS = [
    version,
    search_items,
    get_item,
    create_draft_item,
    update_item,
    change_open,
    list_categories,
]

TOOL_REGISTRY = {t.TOOL_NAME: t for t in TOOLS}


def build_server() -> Server:
    server = Server("soyshop-mcp")

    @server.list_tools()
    async def handle_list_tools() -> list[Tool]:
        return [
            Tool(name=t.TOOL_NAME, description=t.DESCRIPTION, inputSchema=t.INPUT_SCHEMA)
            for t in TOOLS
        ]

    @server.call_tool()
    async def handle_call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        tool = TOOL_REGISTRY.get(name)
        if not tool:
            return [TextContent(type="text", text=json.dumps({"error": f"unknown_tool: {name}"}))]
        try:
            with SoyShopClient() as client:
                result = tool.execute(client, arguments or {})
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
        except Exception as e:
            logger.exception("tool execution failed: %s", name)
            return [
                TextContent(
                    type="text",
                    text=json.dumps({"error": "tool_execution_failed", "detail": str(e)}),
                )
            ]

    return server


async def _run() -> None:
    server = build_server()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def main() -> None:
    asyncio.run(_run())


if __name__ == "__main__":
    main()
