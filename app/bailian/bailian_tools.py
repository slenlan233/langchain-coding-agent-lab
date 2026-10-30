from langchain_core.tools import tool
from app.bailian.common import chat_prompt_template, llm


@tool
def add(a: int, b: int) -> int:
    """计算两个整数的和"""
    return a + b


tool_dict = {
    "add": add
}

llm_with_tools = llm.bind_tools([add])

chain = chat_prompt_template | llm_with_tools

resp = chain.invoke({
    "role": "计算",
    "domain": "数学计算",
    "question": "100+100"
})

print(resp)

for tool_call in resp.tool_calls:
    print(tool_call)

    args = tool_call["args"]
    print(args)

    func_name = tool_call["name"]
    print(func_name)

    tool_func = tool_dict[func_name]

    tool_content = tool_func.invoke(args)

    print(tool_content)