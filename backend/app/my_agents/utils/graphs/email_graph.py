from langgraph.graph import START, END, StateGraph
from ..states.enterprise_state import EnterpriseState
from ..nodes.email_query import draft_email, routing_email

#initalise the graph
builder = StateGraph(EnterpriseState)


#adding noded
builder.add_node("draft_email", draft_email)
builder.add_node("routing_email", routing_email)

#adding edges
builder.add_edge(START, "draft_email")
builder.add_edge("draft_email", "routing_email")
builder.add_edge("routing_email", END)

#compiling graph
email_graph = builder.compile()