from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, AIMessage, HumanMessage
from langgraph.types import interrupt, Command
from ..states.enterprise_state import EnterpriseState
from ..prompts.email_query import DRAFT_EMAIL_SYSTEM_PROMPT
from ..tools.email_graph import send_email_tool
from ..datatypes.email_query import SendEmailInput, EmailAction


llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)

tools = [send_email_tool]

llm_with_tools = llm.bind_tools(tools)

llm_structured_output = llm.with_structured_output(SendEmailInput)

def draft_email(state: EnterpriseState) -> EnterpriseState:
    messages = state["messages"]
    if not messages or not isinstance(messages[0], SystemMessage):
        messages = [SystemMessage(content=DRAFT_EMAIL_SYSTEM_PROMPT)] + messages

    response = llm_structured_output.invoke(messages)
    return {
        "messages": [
            AIMessage(content="I've drafted the email kindly review and make decisions"),
            AIMessage(content=str(response))
        ],
        "drafted_email": response
    }


def routing_email(state: EnterpriseState) -> EnterpriseState | Command:
    draft_email: SendEmailInput = state["drafted_email"]
    user_id = state["user_id"]
    response = interrupt({
        "messages": (
            "choose one action and respond in json:\n\n"
            "{\n"
            '  "action": "accept | reject | inplaceedit | llmedit",\n'
            '  "to": [...],        // required only for inplaceedit\n'
            '  "subject": "...",\n'
            '  "body": "...",\n'
            '  "cc": [...],\n'
            '  "instructions": "..." // required only for llmedit\n'
            "}"
        )
    })

    if isinstance(response, EmailAction):
        cmd = response
    else:
        cmd = EmailAction(**response)

    if cmd.action == "accept":
        send_email_tool(input=draft_email, user_id=user_id)
        return {"messages": AIMessage(content="Email sent")}

    elif cmd.action == "reject":
        return {"messages": AIMessage(content="Email cancelled")}

    elif cmd.action == "inplaceedit":
        updated = SendEmailInput(
            to=cmd.to,
            subject=cmd.subject,
            body=cmd.body,
            cc=cmd.cc
        )
        send_email_tool(input=updated, user_id=user_id)
        return {
            "messages": AIMessage(content="Email sent"),
            "drafted_email": updated
        }

    elif cmd.action == "llmedit":
        return Command(
            update={"messages": HumanMessage(content=cmd.instructions)},
            goto="draft_email"
        )
