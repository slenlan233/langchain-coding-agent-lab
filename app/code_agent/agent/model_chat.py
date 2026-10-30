import uuid

from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_community.chat_message_histories import ChatMessageHistory,FileChatMessageHistory
from langchain_core.runnables import Runnable, RunnableWithMessageHistory
from langchain_community.agent_toolkits.file_management import  FileManagementToolkit
from app.code_agent.prompts.multi_chat_prompts import multi_chat_prompt
from app.code_agent.model.qwen import llm_qwen



def get_session_history(session_id: str) -> ChatMessageHistory:
    return FileChatMessageHistory(f"{session_id}.json")

file_toolkit = FileManagementToolkit(root_dir="D:/学习Java/ai项目/3.xiangmu/llm/.temp")
file_tools = file_toolkit.get_tools()

llm_with_tools = llm_qwen.bind_tools(tools=file_tools)

chain = multi_chat_prompt | llm_with_tools | StrOutputParser()

chain_with_history = RunnableWithMessageHistory(
    runnable=chain,
    get_session_history=get_session_history,
    input_messages_key="question",
    history_messages_key="chat_history",
)

chat_session_id = uuid.uuid4()

while True:
    user_input = input("用户：")
    if user_input.lower() == "exit" or user_input.lower() == "quit":
        break

    print("助理：", end="")
    for chunk in chain_with_history.stream(
            {"question": user_input},
            config={"configurable": {"session_id": chat_session_id}}):
        print(chunk, end="")


    print("\n")



# for chunk in chain.stream({"question": "我们要做什么项目？", "chat_history": []}):
#     print(chunk, end="")
