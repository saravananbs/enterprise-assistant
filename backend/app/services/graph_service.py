from typing import Dict, Any, Generator
from langgraph.types import Command
from langchain_core.messages import AIMessage
from sqlalchemy.orm import Session
from datetime import datetime
from ..my_agents.agent import graph
from ..utils.serializers import serialize_message
from ..my_agents.utils.datatypes.email_query import EmailAction
from ..services.chat_history import append_chat

def run_graph_sync(
    user_id: str,
    chat_id: str,
    db: Session,
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
        append_chat(
            db=db,
            thread_id=thread_id,
            messages=[{
                "role": "user",
                "content": user_message,
                "timestamp": datetime.now().isoformat(),
            }]
        )
    else:
        input_data = Command(resume=interrupt_response)
        append_chat(
            db=db,
            thread_id=thread_id,
            messages=[{
                "role": "user",
                "content": interrupt_response.model_dump(),
                "timestamp": datetime.now().isoformat(),
            }]
        )

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
            append_chat(
                db=db,
                thread_id=thread_id,
                messages=[{
                    "role": "assistant",
                    "content": [
                        {"type": "message", "message": serialize_message(sub.values.get("messages")[-2])},
                        {"type": "message", "message": serialize_message(sub.values.get("messages")[-1])}
                    ],
                    "timestamp": datetime.now().isoformat(),
                }]
            )
            return
        messages = event.get("messages")
        if messages:
            last_message = messages[-1]
            yield {
                "type": "message",
                "message": serialize_message(last_message),
            }
            if isinstance(last_message, AIMessage):
                append_chat(
                    db=db,
                    thread_id=thread_id,
                    messages=[{
                        "role": "assistant",
                        "content": [
                            {"type": "message", "message": serialize_message(last_message)}
                        ],
                        "timestamp": datetime.now().isoformat(),
                    }]
                )
