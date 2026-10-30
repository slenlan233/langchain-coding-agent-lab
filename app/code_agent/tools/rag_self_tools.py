import sys
from pathlib import Path

from app.code_agent.utils.mcp import create_mcp_stdio_client


async def get_stdio_rag_self_tools():
    params = {
        "command":sys.executable,
        "args":[
            str(Path(__file__).resolve().parents[1] / "rag" / "rag.py")
        ]
    }

    client, tools = await create_mcp_stdio_client("self_rag_tools", params)

    return tools