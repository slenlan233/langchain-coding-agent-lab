from langchain_core.runnables import RunnableConfig
from langchain.agents import create_agent
from langgraph.checkpoint.mongodb import MongoDBSaver

from app.code_agent.model.qwen import llm_qwen
from app.code_agent.tools.file_tools import file_tools
from langgraph.checkpoint.redis import RedisSaver

def run_agent():
    #with RedisSaver.from_conn_string("redis://localhost:6379") as memory:
    #    memory.setup()

    MONGODB_URI = "mongodb://localhost:27017"
    MONGDB_DB = "chat"
    with MongoDBSaver.from_conn_string(MONGODB_URI,MONGDB_DB) as memory:
        agent = create_agent(
            model=llm_qwen,
            tools=file_tools,
            checkpointer=memory,
            debug=True,
        )

        config = RunnableConfig(configurable={"thread_id": "1"})

        res = agent.invoke(input={"messages": [("user", "您好，我是Sam")]}, config=config)
        print("=" * 60)
        print(res)
        print("=" * 60)

        res = agent.invoke(input={"messages": [("user", "我是谁")]}, config=config)
        print("=" * 60)
        print(res)
        print("=" * 60)

        memory.close()









if __name__ == "__main__":
    run_agent()
