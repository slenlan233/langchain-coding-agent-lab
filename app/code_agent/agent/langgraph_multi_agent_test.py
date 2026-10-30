from langchain_core.messages import convert_to_messages
from langchain.agents import create_agent

from app.code_agent.model.qwen import llm_qwen
from app.code_agent.agent.team import create_team_agent

def pretty_print_messages(update, last_message=False):
    for node_name, node_update in update.items():
        update_label = f"Update from node {node_name}:"
        print(update_label)

        messages = convert_to_messages(node_update['messages'])
        if last_message:
            messages = messages[-1:]

        for message in messages:
            pretty_message = message.pretty_repr(html=True)
            print(pretty_message)

        print("\n\n")

def add(a: float, b: float) -> float:
    """add two numbers"""
    return a + b

def multiply(a: float, b: float) -> float:
    """multiply two numbers"""
    return a * b

def web_search(query: str) -> str:
    """Search the web for information."""
    return (
        "Here are the headcounts for each of the FAANG companies in 2024:\n"
        "1. **Facebook (Meta)**: 67,317 employees.\n"
        "2. **Apple**: 164,000 employees.\n"
        "3. **Amazon**: 1,551,000 employees.\n"
        "4. **Netflix**: 14,000 employees.\n"
        "5. **Google (Alphabet)**: 181,269 employees."
    )

def build_workflow(*, model=None):
    model = llm_qwen if model is None else model
    math_agent = create_agent(
        model=model,
        tools=[add, multiply],
        name="math_agent",
        system_prompt="你是一个数学专家，一次执行只使用一个工具",
    )
    research_agent = create_agent(
        model=model,
        tools=[web_search],
        name="research_expert",
        system_prompt="你是一个调研专家，使用 web_search，不使用数学工具",
    )
    return create_team_agent(
        agents=[
            (math_agent, "Solve arithmetic using add and multiply. Input the full calculation."),
            (research_agent, "Look up information with web_search. Input the research question."),
        ],
        model=model,
        system_prompt=(
            "You supervise research_expert and math_agent. "
            "For current events, use research_expert; for math, use math_agent."
        ),
    )


if __name__ == "__main__":
    app = build_workflow()
    for chunk in app.stream({
        "messages": [("user", "what's the combined headcount of the FAANG companies in 2024?")]
    }):
        pretty_print_messages(chunk)
