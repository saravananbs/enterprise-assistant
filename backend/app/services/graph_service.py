from typing import Dict
from ..my_agents.agent import graph
from ..utils.serializers import serialize_message

def run_graph_sync(
    user_id: str,
    chat_id: str,
    user_message: str
) -> Dict:
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

    result = graph.invoke(input_data, config=config)

    messages = result.get("messages", [])
    draft_email = result.get("drafted_email")
    if not messages:
        return {
            "message": None
        }

    last_message = messages[-1]

    return {
        "message": serialize_message(last_message),
        "draft_email": draft_email if draft_email else None
    }
