import sys
from pathlib import Path

from app.code_agent.utils.mcp import create_mcp_stdio_client


async def get_stdio_vm_tools():
    params = {
        "command":sys.executable,
        "args":[
            str(Path(__file__).resolve().parents[2] / "mcp" / "vm.py")
        ]
    }

    client, tools = await create_mcp_stdio_client("vm_tools", params)

    return tools
