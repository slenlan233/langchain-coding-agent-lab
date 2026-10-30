import asyncio
import os

from langchain_core.messages import convert_to_messages
from langchain_core.runnables import RunnableConfig
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver

from app.bailian.common import file_tools
from app.code_agent.agent.team import create_team_agent
from app.code_agent.model.qwen import create_model
from app.code_agent.tools.shell_tools import get_stdio_shell_tools


def pretty_print_messages(update, last_message=False):
    for node_name, node_update in update.items():
        print(f"Update from node {node_name}:")

        if not isinstance(node_update, dict):
            continue

        if "messages" not in node_update:
            print(node_update)
            print("\n")
            continue

        messages = convert_to_messages(node_update["messages"])

        if last_message:
            messages = messages[-1:]

        for message in messages:
            pretty_message = message.pretty_repr(html=False)
            print(pretty_message, flush=True)

        print("\n\n")


async def run_agent():
    if os.getenv("AI_AGENT_ENABLE_LEGACY_TOOLS") != "true":
        raise RuntimeError("这是未接入平台审批的教学示例。请使用 ai-agent；如确需运行旧示例，显式设置 AI_AGENT_ENABLE_LEGACY_TOOLS=true。")
    memory = InMemorySaver()
    shell_tools = await get_stdio_shell_tools()
    model = create_model(timeout=60, max_retries=0)

    research_agent = create_agent(
        model=model,
        tools=[tool for tool in file_tools if tool.name in {"read_file", "file_search", "list_directory"}],
        name="research_expert",
        system_prompt="你是一个技术方案设计专家，专门负责设计技术方案，请不要直接写代码，请指导 code_agent 进行工作",
    )

    code_agent = create_agent(
        model=model,
        tools=shell_tools + file_tools,
        name="code_expert",
        system_prompt="""
    你是一个编程和系统操作专家。

    你的职责包括：
    - 编写和修改代码
    - 操作项目文件
    - 执行终端命令
    - Git 操作
    - 安装依赖
    - 启动、测试和调试程序

    当用户要求执行实际操作时：
    - 必须使用提供的工具真正执行操作
    - 不要只把命令告诉用户
    - 执行之后检查结果是否成功
    - 如果失败，根据错误继续排查
    - 同一命令连续失败或超时两次后，向用户报告原因，不要无限重试
    - Shell 工具用于有限时间的非交互命令，不要用它启动常驻开发服务器

    如果 research_expert 已经提供技术方案，则按照方案执行。
    如果任务很简单，例如 git clone、查看文件、运行命令，
    可以直接执行，不需要等待 research_expert。
    """
    )

    app = create_team_agent(
        agents=[
            (research_agent, "分析需求并设计技术方案，输入完整任务和已知约束。"),
            (code_agent, "执行编程与系统操作，输入明确的任务和需要遵守的方案。"),
        ],
        model=model,
        checkpointer=memory,
        system_prompt="""
    你是一个多智能体团队的 supervisor。

    你负责调度以下两个 Agent：

    1. research_expert
       - 负责分析需求
       - 设计技术方案
       - 调研技术问题
       - 不负责实际修改文件或执行代码

    2. code_expert
       - 负责实际执行编程任务
       - 可以调用 shell 工具
       - 可以读取、创建和修改文件
       - 可以执行 Git、Python、Node.js、PowerShell 等命令

    重要规则：

    - 你只负责调度，不要自己完成用户要求的实际任务。
    - 如果用户要求执行终端命令、操作文件、克隆仓库、修改项目、
      编写代码、安装依赖、运行程序等，必须将任务交给 code_expert。
    - 如果任务需要先进行方案分析，可以先交给 research_expert，
      再根据其结果交给 code_expert。
    - 不要只告诉用户应该执行什么命令。
    - 用户要求实际操作时，必须让对应 Agent 真正调用工具完成操作。
    - Agent 完成工作后，你再根据 Agent 的执行结果向用户回复。
    """
    )

    while True:
        user_input = input("用户：")

        if user_input == "exit":
            break

        config = RunnableConfig(configurable={"thread_id": 7}, recursion_limit=100)

        print("正在处理；模型单次请求超时 60s，Shell 默认超时 120s。", flush=True)
        try:
            async for namespace, chunk in app.astream(
                input={"messages": [("user", user_input)]}, config=config,
                stream_mode="updates", subgraphs=True,
            ):
                if namespace:
                    print(f"子代理：{' / '.join(namespace)}", flush=True)
                pretty_print_messages(chunk)
        except Exception as exc:
            print(f"执行失败：{type(exc).__name__}: {exc}", flush=True)

if __name__ == "__main__":
    asyncio.run(run_agent())
