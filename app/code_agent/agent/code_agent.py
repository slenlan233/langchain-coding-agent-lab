import asyncio
import os
import time

from code_agent_platform.agents import build_agent as create_shared_agent
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableConfig

from app.code_agent.model.qwen import llm_qwen
from app.code_agent.tools.browser_tools import get_stdio_browser_tools
from app.code_agent.tools.file_tools import file_tools
from app.code_agent.tools.file_saver import get_file_saver

from app.code_agent.tools.powershell_tools import get_stdio_powershell_tools
from app.code_agent.tools.shell_tools import get_stdio_shell_tools
from app.code_agent.tools.rag_self_tools import get_stdio_rag_self_tools
from app.code_agent.tools.vm_tools import get_stdio_vm_tools
from app.code_agent.utils.tool_status import format_tool_status
from app.code_agent.tools.mysql_tools import get_stdio_mysql_tools


def format_debug_output(step_name:str, content:str, is_tool_call = False)->None:
    if is_tool_call:
        print(f"🔧 【工具调用{step_name}】")
        print("-" * 40)
        print(content.strip())
        print("-" * 40)
    else:
        print(f"🤔【{step_name}】")
        print("-" * 40)
        print(content.strip())
        print("-" * 40)

async def run_agent():
    if os.getenv("AI_AGENT_ENABLE_LEGACY_TOOLS") != "true":
        raise RuntimeError("旧宿主机工具示例未接入平台审批，请使用 ai-agent。")
    # 会话覆盖整个交互循环，避免每次工具调用后关闭终端服务。
    async with get_stdio_powershell_tools() as terminal_tools, get_file_saver() as memory:
        shell_tools = await get_stdio_shell_tools()
        await run_agent_with_tools(shell_tools, terminal_tools, memory)


async def run_agent_with_tools(shell_tools, terminal_tools, memory):
    if os.getenv("AI_AGENT_ENABLE_LEGACY_TOOLS") != "true":
        raise RuntimeError("旧宿主机工具示例需要显式启用 AI_AGENT_ENABLE_LEGACY_TOOLS=true。")
    # rag_tools = await get_stdio_rag_tools()
    rag_self_tools = await get_stdio_rag_self_tools()
    browser_tools = await get_stdio_browser_tools()
    vm_tools = await get_stdio_vm_tools()
    mysql_tools = await get_stdio_mysql_tools()
    # run_shell 放在可见终端工具之前，并在提示词中明确作为默认选择。
    tools = file_tools + shell_tools + terminal_tools + rag_self_tools + browser_tools + vm_tools + mysql_tools
    await chat_with_agent(build_agent(tools, memory))


def build_agent(tools, memory=None, *, model=None):
    """创建可独立验证的 Agent；模型和 checkpoint 可由调用方传入。"""
    # 方案二：提供一个rag工具，让智能体通过工具查询知识
    system_prompt = PromptTemplate.from_template(template="""
# 角色
你是一名优秀的工程师，你的名字叫做{name}

# RAG 知识库说明
知识库主要保存各种工具的使用规范和操作流程，而不是用户任务本身的解决方案。

# RAG 使用要求
- 当用户任务需要使用工具时，在第一次使用该类工具之前，先调用 query_rag 查询该工具的使用规范。
- 查询知识库时，应查询“工具名称 + 使用规范/操作步骤”，不要直接把用户任务本身作为知识库查询词。
- 例如需要使用终端时，应查询“终端工具 Shell 命令 PowerShell 使用规范”之类的内容，而不是查询“如何创建 Vue 项目”。
- 获取知识库内容后，把其中的步骤和约束作为后续工具调用的执行规范。
- 同一类工具在一个用户任务中原则上只查询一次知识库。
- 如果知识库没有相关内容，不要反复更换相似关键词查询，直接根据已有知识继续任务。

# 任务执行原则
- 用户任务的具体解决方法可以结合你已有的工程知识完成。
- 以尽快完成用户任务为目标，只进行必要检查。
- 已经确认的信息不要重复检查。
- 同一种操作连续失败两次时，应分析原因并更换方案，不要原样重复调用。
- 完成任务后进行必要验证，然后立即结束。

# Shell 与可见终端使用规范
- 普通命令、文件检查、依赖安装、构建、测试和有限时长脚本，默认优先使用 run_shell；它在后台使用 PowerShell 7，不会打开窗口，并会直接返回退出码、标准输出和错误输出。
- 只有命令确实需要交互输入、持续会话或用户观察窗口时，才使用 open_terminal、run_terminal_script、get_terminal_text 等可见终端工具。
- 启动长期后台服务时，优先通过 run_shell 使用 Start-Process -WindowStyle Hidden 启动，然后检查端口或健康接口。
- 若必须使用可见终端，始终复用已有 terminal_id；除非用户明确要求多个窗口，否则不得传 new_window=true，也不要因为日志输出延迟而新建窗口。
""")

    return create_shared_agent(
        model=llm_qwen if model is None else model,
        tools=tools,
        memory=memory,
        system_prompt=system_prompt.format(name="Bot"),
    )


async def chat_with_agent(agent):
    config = RunnableConfig(configurable={"thread_id": "45"}, recursion_limit=100)
    while True:
        user_input = input("用户：")
        if user_input == "exit":
            break

        print("\n🤖助手正在思考和处理...")
        print("=" * 60)

        iteration_count = 0
        start_time = time.time()
        last_tool_time = start_time

        # 方案一：从RAG知识库中读取知识，并拼接到提示词中
        # rag = query_rag_from_bailian(user_input)
        #rag_prompt = \
#f"""# 要求
#执行任务之前先使用 query_rag 工具查询知识库，根据知识库中的知识执行任务

## 用户问题
#{user_input}"""

        async for chunk in agent.astream(input={"messages": [("user", user_input)]}, config=config):
            iteration_count += 1

            print(f"\n 第{iteration_count}步执行")
            print("-" * 30)



            items = chunk.items()
            for node_name, node_output in items:
                if "messages" in node_output:
                    for msg in node_output["messages"]:
                        if isinstance(msg, AIMessage):
                            if msg.content:
                                format_debug_output("AI思考", msg.text)
                            if msg.tool_calls:
                                for tool in msg.tool_calls:
                                    format_debug_output("工具调用",f"{tool['name']}：{tool['args']}")

                        elif isinstance(msg, ToolMessage):
                            tool_name = getattr(msg, "name", "unknown")
                            tool_content = msg.content
                            tool_status = format_tool_status(
                                tool_content,
                                getattr(msg, "status", None),
                            )
                            current_time = time.time()
                            tool_duration = current_time - last_tool_time
                            last_tool_time = current_time

                            tool_result = f"""🔧 工具：{tool_name}
📊 结果: {tool_content}
{tool_status}
⌚️ 执行时间：{tool_duration:.2f}秒"""
                            format_debug_output("工具执行结果", tool_result, is_tool_call=True)





        print()

if __name__ == "__main__":
    from code_agent_platform.cli import main
    main()
