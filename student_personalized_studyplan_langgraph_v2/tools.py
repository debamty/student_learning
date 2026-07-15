"""MCP client-backed LangChain tools."""
import asyncio
import os
from typing import Any
from langchain_core.tools import tool
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from mcp.types import TextContent

MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://127.0.0.1:8001/mcp")

async def _call(name: str, arguments: dict[str, Any]) -> str:
    async with streamable_http_client(MCP_SERVER_URL) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(name, arguments=arguments)
    texts = [item.text for item in result.content if isinstance(item, TextContent)]
    if result.isError or not texts:
        raise RuntimeError("; ".join(texts) or f"MCP tool {name} failed")
    return texts[0]

def call_mcp_tool(name: str, **arguments: str) -> str:
    return asyncio.run(_call(name, arguments))

@tool
def mcp_analyze_marks(student_json: str) -> str:
    """Analyze marks through MCP."""
    return call_mcp_tool("analyze_marks", student_json=student_json)

@tool
def mcp_build_learning_path(student_json: str) -> str:
    """Build a learning path through MCP."""
    return call_mcp_tool("build_learning_path", student_json=student_json)

@tool
def mcp_refine_learning_path(student_json: str, path_json: str, critic_json: str) -> str:
    """Refine a learning path through MCP."""
    return call_mcp_tool("refine_learning_path", student_json=student_json, path_json=path_json, critic_json=critic_json)

MCP_TOOLS = [mcp_analyze_marks, mcp_build_learning_path, mcp_refine_learning_path]
