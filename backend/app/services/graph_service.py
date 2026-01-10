from typing import AsyncGenerator
from ..my_agents.agent import graph

async def run_graph_stream(
    user_id: str,
    chat_id: str,
    user_message: str
) -> AsyncGenerator[dict, None]:
    thread_id = f"{user_id}:{chat_id}"

    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    input_data = {
        "messages": [
            ("human", user_message)
        ],
        "user_id": user_id
    }

    async for event in graph.astream(
        input_data,
        config=config,
        stream_mode="values"
    ):
        yield event
