from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, AIMessage
from langgraph.types import interrupt
from ..states.enterprise_state import EnterpriseState
from ..prompts.email_query import DRAFT_EMAIL_SYSTEM_PROMPT, SEND_EMAIL_SYSTEM_PROMPT
from ..tools.email_graph import send_email_tool


llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)

tools = [send_email_tool]

llm_with_tools = llm.bind_tools(tools)

def draft_email(state: EnterpriseState) -> EnterpriseState:
    messages = state["messages"]
    if not messages or not isinstance(messages[0], SystemMessage):
        messages = [SystemMessage(content=DRAFT_EMAIL_SYSTEM_PROMPT)] + messages

    response = llm.invoke(messages)
    return {
        "messages": response
    }

def send_email(state: EnterpriseState) -> EnterpriseState:
    approval = interrupt({
        "message": "Do you want me to send this email?",
    })
    if approval not in ("yes", "send", True):
        return {
            "messages": AIMessage(content="Email cancelled.")
        }

    messages = state["messages"]
    # if not messages or not isinstance(messages[0], SystemMessage):
    messages = [SystemMessage(content=SEND_EMAIL_SYSTEM_PROMPT)] + messages

    response = llm_with_tools.invoke(messages)
    return {
        "messages": response
    }