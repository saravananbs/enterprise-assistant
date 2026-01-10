from langchain_core.messages import (
    HumanMessage,
    AIMessage,
    SystemMessage,
    ToolMessage
)

def serialize_message(msg):
    if isinstance(msg, HumanMessage):
        return {"role": "user", "content": msg.content}

    if isinstance(msg, AIMessage):
        return {"role": "assistant", "content": msg.content}

    if isinstance(msg, SystemMessage):
        return {"role": "system", "content": msg.content}

    if isinstance(msg, ToolMessage):
        return {
            "role": "tool",
            "content": msg.content,
            "tool_name": msg.name
        }

    return {"role": "unknown", "content": str(msg)}
