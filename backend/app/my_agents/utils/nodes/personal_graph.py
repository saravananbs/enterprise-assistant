from typing import Dict, Any
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage
from langchain_core.runnables import RunnableConfig
from ..states.enterprise_state import EnterpriseState
from ..tools.personal_graph import query_database
from ..prompts.tools import SCHEMA, TOOLS_SYSTEM_MESSAGE_TEMPLATE
from ..llms.llm_factory import get_llm

llm = get_llm()

tools = [query_database]

llm_with_tools = llm.bind_tools(tools)

async def invoke_llm_with_tools(state: EnterpriseState, config: RunnableConfig | None = None) -> Dict[str, Any]:
    messages = state["messages"]
    user_id   = config["configurable"].get("user_id",   "unknown")
    user_role = config["configurable"].get("user_role", "unknown") 
    system_content = TOOLS_SYSTEM_MESSAGE_TEMPLATE.format(user_id=user_id, user_role=user_role, schema=SCHEMA)
    if not messages or not isinstance(messages[0], SystemMessage):
        messages = [SystemMessage(content=system_content)] + messages 
    response = await llm_with_tools.ainvoke(messages)
    print(response)
    return {
        "messages": [response]
    }
