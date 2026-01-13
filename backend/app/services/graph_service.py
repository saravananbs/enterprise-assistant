from typing import Dict, Any, Generator
from langgraph.types import Command
from ..my_agents.agent import graph
from ..utils.serializers import serialize_message
from ..my_agents.utils.datatypes.email_query import EmailAction

def run_graph_sync(
    user_id: str,
    chat_id: str,
    user_message: str | None = None,
    interrupt_response: EmailAction | None = None,
) -> Generator[Dict[str, Any], None, None]:

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
    else:
        input_data = Command(resume=interrupt_response)

    for event in graph.stream(
        input_data,
        config=config,
        stream_mode="values", 
    ):
        if "__interrupt__" in event:
            parent = graph.get_state(config)
            task = parent.tasks[0]
            task_config = task.state

            sub = graph.get_state(task_config)
            snapshot = graph.get_state(config)
            print("VALUESSS", snapshot.values)      
            print("NEXTTT", snapshot.next)        
            print("TASKSSS", snapshot.tasks)
            yield {
                "type": "message",
                "message": serialize_message(sub.values.get("messages")[-2]),
            }
            yield {
                "type": "message",
                "message": serialize_message(sub.values.get("messages")[-1]),
            }
            yield {
                "type": "interrupt",
                "payload": str(event["__interrupt__"]),
                "draft_email": sub.values.get("drafted_email").model_dump() if sub.values.get("drafted_email") else None,
            } 
            return
        messages = event.get("messages")
        if messages:
            last_message = messages[-1]
            yield {
                "type": "message",
                "message": serialize_message(last_message),
            }
