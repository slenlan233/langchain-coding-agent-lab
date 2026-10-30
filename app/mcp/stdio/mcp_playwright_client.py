import asyncio

from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain_mcp_adapters.tools import load_mcp_tools
from mcp import StdioServerParameters, stdio_client, ClientSession
from langchain.agents import create_agent

from app.bailian.common import llm


async def mcp_playwright_client():
    server_params = StdioServerParameters(
        command="npx",
        args=["-y", "@executeautomation/playwright-mcp-server"]
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await  session.initialize()
            tools = await load_mcp_tools(session)
            print(tools)

            agent = create_agent(model=llm, tools=tools, debug=True)
            response = await agent.ainvoke(input={"messages": [("user","在百度中查询北京今天的天气")]})
            print(response)

            messages = response["messages"]
            for message in messages:
                if isinstance(message, HumanMessage):
                    print("用户", message.content)
                elif isinstance(message, AIMessage):
                    # AI说的话
                    if message.content:
                        print("助理", message.content)
                    # AI决定调用的工具
                    if message.tool_calls:
                        for tool_call in message.tool_calls:
                            print(
                                "助理【决定调用工具】",
                                tool_call["name"],
                                tool_call["args"]
                            )
                elif isinstance(message, ToolMessage):
                    print(
                        "【调用工具的结果】",
                        message.name,
                        message.content
                    )


if __name__ == "__main__":
    asyncio.run(mcp_playwright_client())
