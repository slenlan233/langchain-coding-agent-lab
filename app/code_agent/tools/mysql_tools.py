import sys
from pathlib import Path

from app.code_agent.utils.mcp import create_mcp_stdio_client


async def get_stdio_mysql_tools():
    params = {
        "command":sys.executable,
        "args":[
            str(Path(__file__).resolve().parents[2] / "mcp" / "mysql_tools.py")
        ]
    }

    client, tools = await create_mcp_stdio_client("mysql_tools", params)

    return tools
