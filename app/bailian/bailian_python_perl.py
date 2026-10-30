from langchain.agents import create_agent
from langchain_core.prompts import PromptTemplate
from langchain_experimental.tools.python.tool import PythonREPLTool
from app.bailian.common import llm

# 定义工具
tools = [PythonREPLTool()]
tool_names = ["PythonREPLTool"]

# 创建智能体
agent = create_agent(
    tools=tools,
    model=llm,
    system_prompt="使用 PythonREPLTool 时，参数只传 Python 源码，不添加 Markdown 代码围栏。",
)

# 创建提示词模版
prompt_template = PromptTemplate.from_template(template="""
尽你所能回答以下问题或执行用户的命令，你可以使用以下工具:{tool_names}
--
通过结构化工具调用执行 Python，完成后说明结果和验证情况。
--
注意：
- PythonREPLTool工具的入参是python代码，不允许添加'''python 或 '''py等标记
要求：{input}
""")

# 创建提示词
prompt = prompt_template.format(
    tool_names=", ".join(tool_names),
    input='''
    要求：
    1. 向 D:/学习Java/ai项目/3.xiangmu/.temp 目录下写入一个新文件，名称为：index.html
    2. 写一个企业的官网
    '''
)

print(prompt)
