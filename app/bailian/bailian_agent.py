from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from pydantic import BaseModel, Field

from app.bailian.common import create_calc_tools, llm


# 1. 定义最终输出格式
class Output(BaseModel):
    args: str = Field(description="输入的参数")
    result: str = Field(description="返回的结果")


def build_calculator_agent(*, model=None):
    # 不能让计算工具提前 return_direct，否则来不及生成结构化最终答案。
    tools = [item.model_copy(update={"return_direct": False}) for item in create_calc_tools()]
    return create_agent(
        model=llm if model is None else model,
        tools=tools,
        system_prompt="使用计算工具求解问题，并按指定结构返回输入参数和计算结果。",
        response_format=ToolStrategy(Output),
    )


def run_example():
    response = build_calculator_agent().invoke(
        {"messages": [("user", "100+100=？")]}
    )
    result = response["structured_response"]
    print("结构化结果：")
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    run_example()
