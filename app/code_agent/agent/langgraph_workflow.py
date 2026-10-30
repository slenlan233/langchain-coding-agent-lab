import os

from langchain_core.messages import AIMessage
from langchain_core.prompt_values import StringPromptValue
from langgraph.constants import START, END
from langgraph.graph import StateGraph, MessagesState

from app.code_agent.model.qwen import llm_qwen
from app.mcp.browser_tools import search_in_baidu_with_html


class BaiduSearchMessagesState(MessagesState):
    search_question: str
    search_keyword: str
    search_results: str


def output_graph_image(graph, filename):
    try:
        png_data = graph.get_graph().draw_mermaid_png()

        output_file_dir = os.path.dirname(__file__)
        output_file_path = os.path.join(output_file_dir,filename + ".png")

        with open(output_file_path, "wb") as f:
            f.write(png_data)

        print(f"文件写入成功：{output_file_path}")

    except Exception as e:
        print(e)


key_extract_query_keyword = "key_extract_query_keyword"
key_search_baidu = "key_search_baidu"
key_reply_user = "key_reply_user"


# 1. 提取搜索关键词
def node_extract_query_keyword(state: BaiduSearchMessagesState):
    last_message = state["messages"][-1]
    content = last_message.content

    prompt = StringPromptValue(
        text=f"""
请从如下信息中提取需要在百度中搜索的关键词。
直接返回搜索关键词，不要解释。

用户问题：
{content}
"""
    )

    message = llm_qwen.invoke(prompt)

    return {
        # 保存原始问题
        "search_question": content,

        # 保存提取出的关键词
        "search_keyword": message.content,

        # 把模型输出加入消息历史
        "messages": [message]
    }


# 2. 百度搜索
def node_search_baidu(state: BaiduSearchMessagesState):
    keyword = state["search_keyword"]

    html = search_in_baidu_with_html(keyword)

    search_message = AIMessage(
        content=f"百度搜索结果：{html}"
    )

    return {
        "search_results": html,
        "messages": [search_message]
    }


# 3. 根据搜索结果回答用户
def node_reply_user(state: BaiduSearchMessagesState):
    result = llm_qwen.invoke(
        input=f"""
# 要求
请结合百度搜索结果回答用户的问题。

# 用户问题
{state["search_question"]}

# 百度搜索结果
{state["search_results"]}
"""
    )

    return {
        "messages": [result]
    }


# ===============================
# 构建 LangGraph
# ===============================

state_graph = StateGraph(BaiduSearchMessagesState)
state_graph.add_node(key_extract_query_keyword, node_extract_query_keyword)
state_graph.add_node(key_search_baidu, node_search_baidu)
state_graph.add_node(key_reply_user, node_reply_user)

state_graph.add_edge(START, key_extract_query_keyword)
state_graph.add_edge(key_extract_query_keyword, key_search_baidu)
state_graph.add_edge(key_search_baidu, key_reply_user)
state_graph.add_edge(key_reply_user, END)

compiled_graph = state_graph.compile()

# output_graph_image(compiled_graph, "graph")


results = compiled_graph.stream({
    "messages": [
        ("user", "请问北京今天的天气如何")
    ]
})


for s in results:
    key = list(s)[0]

    print(f"当前节点：{key}")
    print(s[key]["messages"][-1].content)
    print("-" * 60)