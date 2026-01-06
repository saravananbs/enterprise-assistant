from langgraph.graph import START, END, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from utils.states.enterprise_state import EnterpriseState
from utils.nodes.email_query import draft_email, send_email, tools

#initalise the graph
builder = StateGraph(EnterpriseState)


#adding noded
builder.add_node("draft_email", draft_email)
builder.add_node("send_email", send_email)
builder.add_node("tools", ToolNode(tools))


#adding edges
builder.add_edge(START, "draft_email")
builder.add_edge("draft_email", "send_email")
builder.add_conditional_edges("send_email", tools_condition)
builder.add_edge("tools", "send_email")

#compiling graph
email_graph = builder.compile()