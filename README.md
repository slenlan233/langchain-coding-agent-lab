# LangChain Coding Agent Lab

从模型调用、函数工具和 MCP 开始，探索 AI 编程助手的学习实验项目。

这是同一学习路线的第一阶段；第二阶段是 [Code Agent Platform](https://github.com/slenlan233/code-agent-platform)。本仓库保存本地当前 `app/` 的代码快照，不将后续工作台能力当作原型已具备的能力，也不是 9 月历史版本的还原。

## 学习内容

- LangChain Agent、提示词、模型与工具消息的交互。
- 文件、Shell、PowerShell、浏览器、MySQL 与虚拟机工具实验。
- MCP stdio 客户端与工具服务接入。
- 百炼 RAG 检索、会话 checkpoint，以及 LangGraph 和多 Agent 的探索示例。

入口代码为 `app/code_agent/agent/code_agent.py`，工具位于 `app/code_agent/tools/`，服务位于 `app/mcp/`。不同示例的成熟度不同，不能把示例存在等同于完整可用平台。

## 当前快照与共享依赖

当前 `app/` 已在演进过程中复用了新版的 Agent 工厂、MCP 客户端、文件工具和 MySQL/百炼封装。因此先安装同级平台仓库，以保持本次上传的 `app/` 源码原貌，不复制整套平台到本仓库，也不暗中改回旧版实现。

```powershell
git clone https://github.com/slenlan233/code-agent-platform.git
git clone https://github.com/slenlan233/langchain-coding-agent-lab.git
cd langchain-coding-agent-lab
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e "../code-agent-platform[api,graph]"
.\.venv\Scripts\python.exe -m pip install -r requirements.txt -e .
Copy-Item .env.example .env
```

私有仓库需先使用自己的 GitHub 账号认证。填入自己的本地环境配置，按实际环境准备 MCP 服务。Windows 桌面、虚拟机和浏览器示例还需要相应程序，源码中的机器路径需按自己的电脑调整。

需要主动运行旧版宿主机工具实验时，在本地配置 `AI_AGENT_ENABLE_LEGACY_TOOLS=true`，再执行：

```powershell
.\.venv\Scripts\python.exe run_legacy.py
```

原 `python -m app.code_agent.agent.code_agent` 入口已转调平台 CLI；上面的单独入口用于运行原型的 `run_agent()`。旧工具不具备工作台完整的审批、隔离与审计约束，应在实验目录中运行。

## 从原型到平台

原型帮助理解“模型如何使用工具”；后续工作台进一步处理“任务如何审批、恢复、验证和交付”。这是逐步学习、复用和改进的过程，未宣称生产成功率或未经测量的收益指标。

本仓库不包含个人密钥、本地数据库、聊天记录、运行产物或虚拟环境。
