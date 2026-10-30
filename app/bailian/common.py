import os
from dataclasses import Field
from itertools import chain
from sys import prefix
from langchain_core.tools import tool
from langchain_community.agent_toolkits import FileManagementToolkit

from app.code_agent.model.configured import ConfiguredChatOpenAI as ChatOpenAI
from pydantic import SecretStr, BaseModel
from langchain_core.prompts import ChatPromptTemplate, ChatMessagePromptTemplate, FewShotPromptTemplate, PromptTemplate
from langchain_core.tools import tool
from pydantic import SecretStr, BaseModel, Field

llm = ChatOpenAI(
    model='qwen3.7-max',
    base_url='https://llm-ngs9ec0pm3nunoaa.cn-beijing.maas.aliyuncs.com/compatible-mode/v1',
    api_key=SecretStr(os.getenv("BAILIAN_API_KEY") or "not-configured"),
    streaming=True,
)

system_message_template = ChatMessagePromptTemplate.from_template(
    template = "你是一位{role}专家，擅长回答{domain}领域的问题",
    role = "system"
)

human_message_template = ChatMessagePromptTemplate.from_template(
template = "用户问题:{question}",
    role = "user"
)


# 创建提示器模版
chat_prompt_template = ChatPromptTemplate.from_messages([
    system_message_template,
    human_message_template
])

class AddInputArgs(BaseModel):
    a: int = Field(description = "first number")
    b: int = Field(description = "second number")

@tool(
    description="add two numbers",
    args_schema=AddInputArgs,
    return_direct=True,
)
def add(a,b):
    """add two numbers"""
    return a + b

def create_calc_tools():
    return [add]

calc_tools = create_calc_tools()

file_tooltik = FileManagementToolkit(root_dir="D:/学习Java/ai项目/3.xiangmu/.temp")
file_tools = file_tooltik.get_tools()