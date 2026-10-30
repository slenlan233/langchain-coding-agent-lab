"""将工具返回值转换为不会误导用户的状态文案。"""

import json
from typing import Any


def format_tool_status(content: Any, message_status: str | None = None) -> str:
    """根据工具的结构化返回值生成准确的状态文案。"""
    if message_status == "error":
        return "❌ 状态：工具调用失败，需要分析原因后再决定下一步"

    payload = content
    if isinstance(content, str):
        try:
            payload = json.loads(content)
        except (json.JSONDecodeError, TypeError):
            payload = None

    if isinstance(payload, dict):
        success = payload.get("success")
        if success is True:
            return "✅️ 状态：执行成功，可以开始下一个任务"
        if success is False or payload.get("isError") is True:
            return "❌ 状态：执行失败，需要分析原因后再决定下一步"

    # 例如终端工具这里只表示命令已经发送，不能据此断言命令执行成功。
    return "ℹ️ 状态：工具已返回结果，请根据结果确认任务是否完成"
