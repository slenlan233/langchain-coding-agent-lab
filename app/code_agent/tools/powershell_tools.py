import sys
from contextlib import asynccontextmanager
from pathlib import Path

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools


@asynccontextmanager
async def get_stdio_powershell_tools():
    """在 async with 期间保留终端 MCP 会话及其进程状态。"""
    params = {
        "command": sys.executable,
        "args": [
            str(Path(__file__).resolve().parents[2] / "mcp" / "powershell_tools.py")
        ],
    }

    client = MultiServerMCPClient({
        "powershell_tools": {"transport": "stdio", **params}
    })
    async with client.session("powershell_tools") as session:
        yield await load_mcp_tools(session)
