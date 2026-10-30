import sys
from datetime import timedelta
from pathlib import Path

from app.code_agent.utils.mcp import create_mcp_stdio_client


async def get_stdio_shell_tools():
    params = {
        "command":sys.executable,
        "args":[
            str(Path(__file__).resolve().parents[2] / "mcp" / "shell_tools.py")
        ],
        "session_kwargs": {"read_timeout_seconds": timedelta(seconds=630)},
    }

    client, tools = await create_mcp_stdio_client("shell_tools", params)

    return tools
