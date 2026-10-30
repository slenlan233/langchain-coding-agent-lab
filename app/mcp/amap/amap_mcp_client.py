import os
import asyncio

from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_core.prompts import PromptTemplate
from app.bailian.common import llm, file_tools


async def create_amap_mcp_client():
    amap_key = os.getenv("AMAP_API_KEY", "")

    mcp_config = {
        "amap": {
            "url": f"https://mcp.amap.com/sse?key={amap_key}",
            "transport": "sse",
        }
    }

    client = MultiServerMCPClient(mcp_config)
    print(client)

    tools = await client.get_tools()
    print(tools)
    return client,tools

async def create_and_run_agent():
    client,tools = await create_amap_mcp_client()

    print(file_tools)

    agent = create_agent(
        model=llm,
        tools=tools + file_tools,
        system_prompt="你是一个智能助手，可以调用高德 MCP 工具。",
    )

    prompt_template = PromptTemplate.from_template("你是一个智能助手，可以调用高德 MCP 工具。\n\n问题：{input}")
    prompt = prompt_template.format(input="""
    目标：
    - 明天上午十点我要从北京南站到望京SOHO
    - 线路选择：公交地铁或打车
    - 考虑出行时间和路线，以及天气状况和穿衣建议
    
    要求：
    - 制作网页来展示出现线路和位置，输出一个 HTML 页面到：D:/学习Java/ai项目/3.xiangmu/.temp 目录下
    - 网页使用简约美观的页面风格，以及卡片展示
    - 行程规划的结果要能够在高德APP中展示，并集成到H5界面中
    """)
    print(prompt)

    resp = await agent.ainvoke({"messages": [("user", prompt)]})
    print(resp)
    return resp
if __name__ == "__main__":
    asyncio.run(create_and_run_agent())
