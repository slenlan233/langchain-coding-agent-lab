import asyncio
import sys
from pathlib import Path

from langchain.agents import create_agent
from mcp import StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp import ClientSession
from langchain_mcp_adapters.tools import load_mcp_tools

from app.bailian.common import llm


async def create_mcp_stdio_client():
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[str(Path(__file__).with_name("mcp_stdio_server.py"))]
    )

    async with stdio_client(server_params) as (read,write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await load_mcp_tools(session)

            print(tools)

            agent = create_agent(
                model=llm,
                tools = tools,
            )

            resp = await agent.ainvoke({"messages": [("user", "1+2*5=?")]})

            return resp

if __name__ == "__main__":
    asyncio.run(create_mcp_stdio_client())
