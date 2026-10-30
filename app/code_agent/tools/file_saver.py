"""使用官方 SQLite saver 保存 checkpoint 和节点的 pending writes。"""

import sqlite3
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver


def _database_path(base_path: str | Path | None = None) -> Path:
    directory = (
        Path(base_path)
        if base_path is not None
        else Path(__file__).resolve().parents[3] / ".temp" / "checkpoint"
    )
    directory.mkdir(parents=True, exist_ok=True)
    # 新数据库与旧 JSON checkpoint 分开保存，不自动反序列化旧 pickle。
    return directory / "checkpoints-v2.sqlite"


class FileSaver(SqliteSaver):
    """保留同步示例的类名；用 with 或 close() 释放数据库连接。"""

    def __init__(self, base_path: str | Path | None = None):
        connection = sqlite3.connect(
            _database_path(base_path), check_same_thread=False, timeout=30
        )
        super().__init__(connection)

    def close(self) -> None:
        self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()


@asynccontextmanager
async def get_file_saver(
    base_path: str | Path | None = None,
) -> AsyncIterator[AsyncSqliteSaver]:
    """异步 Agent 使用独立异步 saver，避免同步 SQLite 阻塞事件循环。"""
    async with AsyncSqliteSaver.from_conn_string(str(_database_path(base_path))) as saver:
        yield saver


if __name__ == "__main__":
    from langchain.agents import create_agent

    from app.code_agent.model.qwen import llm_qwen
    from app.code_agent.tools.file_tools import file_tools

    with FileSaver() as memory:
        agent = create_agent(model=llm_qwen, tools=file_tools, checkpointer=memory)
        config = {"configurable": {"thread_id": "2"}}
        while True:
            user_input = input("用户：")
            if user_input == "exit":
                break
            response = agent.invoke({"messages": [("user", user_input)]}, config=config)
            print("助理：", response["messages"][-1].content)

