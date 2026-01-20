from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage
from ..states.enterprise_state import EnterpriseState
from ..tools.personal_graph import (
    get_payroll_summary, get_leave_history, get_current_salary_structure,
    get_employee_by_code, get_leave_balances, get_all_employees
)
from ..prompts.tools import TOOLS_SYSTEM_MESSAGE


llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0
)

tools = [
    get_payroll_summary, get_leave_history, get_current_salary_structure,
    get_employee_by_code, get_leave_balances, get_all_employees
]

llm_with_tools = llm.bind_tools(tools)

async def invoke_llm_with_tools(state: EnterpriseState) -> dict:
    messages = state["messages"]
    if not messages or not isinstance(messages[0], SystemMessage):
        messages = [SystemMessage(content=TOOLS_SYSTEM_MESSAGE)] + messages

    response = await llm_with_tools.ainvoke(messages)
    return {
        "messages": response
    }
