import os

from app.code_agent.model.configured import ConfiguredChatOpenAI as ChatOpenAI
from pydantic import SecretStr




llm_qwen = ChatOpenAI(
    model="deepseek-flash",
    base_url="https://api.deepseek.com",
    api_key=SecretStr(os.getenv("AI_AGENT_API_KEY") or "not-configured"),
    streaming=True,
    extra_body={
        "thinking": {"type": "disabled"},
    },
)


def create_model(*, timeout: float = 60, max_retries: int = 0) -> ChatOpenAI:
    """使用现有连接配置创建客户端，不修改其他示例共用的模型实例。"""
    return ChatOpenAI(
        model=llm_qwen.model_name,
        base_url=llm_qwen.openai_api_base,
        api_key=llm_qwen.openai_api_key,
        streaming=llm_qwen.streaming,
        extra_body=llm_qwen.extra_body,
        timeout=timeout,
        max_retries=max_retries,
    )
