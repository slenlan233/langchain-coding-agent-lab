"""用标准工具封装子 Agent，替代已停止维护的 supervisor 扩展。"""

from langchain.agents import create_agent
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import StructuredTool


def _subagent_tool(agent, description: str):
    def call(query: str, config: RunnableConfig) -> str:
        result = agent.invoke({"messages": [("user", query)]}, config=config)
        return result["messages"][-1].text

    async def acall(query: str, config: RunnableConfig) -> str:
        result = await agent.ainvoke({"messages": [("user", query)]}, config=config)
        return result["messages"][-1].text

    return StructuredTool.from_function(
        func=call,
        coroutine=acall,
        name=agent.name,
        description=description,
    )


def create_team_agent(*, model, agents, system_prompt: str, checkpointer=None):
    """agents 为 (已创建的子 Agent, 工具说明) 序列；仅外层持有 checkpointer。"""
    tools = [_subagent_tool(agent, description) for agent, description in agents]
    return create_agent(
        model=model,
        tools=tools,
        system_prompt=system_prompt,
        checkpointer=checkpointer,
        name="supervisor",
    )
