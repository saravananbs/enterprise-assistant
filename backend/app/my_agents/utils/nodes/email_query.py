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

async def draft_email(state: EnterpriseState) -> EnterpriseState:
    messages = state["messages"]
    if not messages or not isinstance(messages[0], SystemMessage):
        messages = [SystemMessage(content=DRAFT_EMAIL_SYSTEM_PROMPT)] + messages

    response = await llm_structured_output.ainvoke(messages)
    return {
        "messages": [
            AIMessage(content="I've drafted the email kindly review and make decisions"),
            AIMessage(content=str(response))
        ],
        "drafted_email": response
    }


async def routing_email(state: EnterpriseState) -> EnterpriseState | Command:
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
        response = await send_email_tool(input=draft_email, user_id=user_id)
        if response["status"] == "sent":
            return {"messages": AIMessage(content="Email sent")}
        else:
            return {"messages": AIMessage(content="Please give access to send email on behalf of you via the authenticate email button")}

    elif cmd.action == "reject":
        return {"messages": AIMessage(content="Email cancelled")}

    elif cmd.action == "inplaceedit":
        updated = SendEmailInput(
            to=cmd.to,
            subject=cmd.subject,
            body=cmd.body,
            cc=cmd.cc
        )
        response = await send_email_tool(input=updated, user_id=user_id)

        if response["status"] == "sent":
            return {
                "messages": AIMessage(content="Email sent"),
                "drafted_email": updated
            }
        else:
            return {"messages": AIMessage(content="Please give access to send email on behalf of you via the authenticate email button")}

    elif cmd.action == "llmedit":
        return Command(
            update={"messages": HumanMessage(content=cmd.instructions)},
            goto="draft_email"
        )
