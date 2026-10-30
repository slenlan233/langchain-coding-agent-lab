import os
from itertools import chain
from sys import prefix

from app.code_agent.model.configured import ConfiguredChatOpenAI as ChatOpenAI
from pydantic import SecretStr
from langchain_core.prompts import ChatPromptTemplate, ChatMessagePromptTemplate, FewShotPromptTemplate, PromptTemplate

llm = ChatOpenAI(
    model='qwen3.8-max',
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
    system_message_template, human_message_template
])

# 模版+变量
prompt = chat_prompt_template.format(role="编程",
                                     domain="Web开发",
                                     question="如何构建一个基于Vue的前端应用")

# print(prompt)
#
# resp = llm.stream(prompt)
#
# for chunk in resp:
#     print(chunk.content, end="")

example_template = "输入：{input}\n输出：{output}"

examples = [
    {"input": "将'hello'翻译为中文", "output":"你好"},
    {"input": "将'Goodbye'翻译为中文", "output":"再见"},
]

few_shot_prompt_template = FewShotPromptTemplate(
    examples=examples,
    example_prompt=PromptTemplate.from_template(example_template),
    prefix = "请将以下英文翻译为中文：",
    suffix = "输入：{text}\n输出：",
    input_variables=["text"]
)

print(few_shot_prompt_template)

chain = few_shot_prompt_template | llm

resp = chain.stream(input={"text":"thank you"})

for chunk in resp:
    print(chunk.content, end="")