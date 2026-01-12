from typing import Dict, Any
from langgraph.types import Command, StateSnapshot
from ..my_agents.agent import graph
from ..utils.serializers import serialize_message
from ..my_agents.utils.datatypes.email_query import EmailAction

def run_graph_sync(
    user_id: str,
    chat_id: str,
    user_message: str | None = None,
    interrupt_response:  EmailAction | None = None
) -> Dict[str, Any]:
    thread_id = f"{user_id}:{chat_id}"

    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    if user_message is not None:
        input_data = {
            "messages": [("human", user_message)],
            "user_id": user_id
        }

        result = graph.invoke(input_data, config=config)

    else:
        result = graph.invoke(
            Command(resume=interrupt_response),
            config=config
        )

    if "__interrupt__" in result:
        parent = graph.get_state(config)
        task = parent.tasks[0]  
        task_config = task.state 

        sub = graph.get_state(task_config)

        return {
            "type": "interrupt",
            "payload": result["__interrupt__"],
            "draft_email": sub.values.get("drafted_email"),
        }


    messages = result.get("messages", [])
    draft_email = result.get("drafted_email")

    last_message = messages[-1] if messages else None

    return {
        "type": "message",
        "message": serialize_message(last_message) if last_message else None,
        "draft_email": draft_email
    }
