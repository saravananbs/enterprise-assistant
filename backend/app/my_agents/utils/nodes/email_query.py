from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, AIMessage, HumanMessage
from langgraph.types import interrupt, Command
from ..states.enterprise_state import EnterpriseState
from ..prompts.email_query import DRAFT_EMAIL_SYSTEM_PROMPT, SEND_EMAIL_SYSTEM_PROMPT
from ..tools.email_graph import send_email_tool
from ..datatypes.email_query import SendEmailInput


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
    response = interrupt(
        {
            "messages": (
                "Do you want to:\n"
                "1. accept (send the email)\n"
                "2. reject (cancel)\n"
                "3. inplaceedit (edit manually)\n"
                "4. llmedit (AI edits & sends)"
            )
        }
    )
    if response == "accept":
        res = send_email_tool(input=draft_email, user_id=user_id)
        return {
            "messages": AIMessage(
                content="Email sent successfully" if res["status"] == "sent"
                else "Email sending failed due to some reasons"
            )
        }
    elif response == "reject":
        return {
            "messages": AIMessage(content="Email cancelled")
        }
    elif response == "inplaceedit":
        edited_email = interrupt(
            {
                "messages": (
                    "Please edit the email and return it in this format:\n"
                    "{\n"
                    '  "to": ["user@example.com"],\n'
                    '  "subject": "Updated subject",\n'
                    '  "body": "Updated body",\n'
                    '  "cc": ["cc@example.com"]\n'
                    "}"
                )
            }
        )
        updated_draft = SendEmailInput(**edited_email)
        res = send_email_tool(input=updated_draft, user_id=user_id)
        return {
            "messages": AIMessage(
                content="Email sent successfully" if res["status"] == "sent"
                else "Email sending failed due to some reasons"
            ),
            "drafted_email": updated_draft
        }
    elif response == "llmedit":
        updated_prompt = interrupt(
            {
                "messages": "Please enter what changes you like to make"
            }
        )
        return Command(
            update={
                "messages": HumanMessage(content=updated_prompt)
            },
            goto="draft_email"
        )