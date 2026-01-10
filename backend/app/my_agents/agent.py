from langgraph.graph import START, END, StateGraph
from .utils.states.enterprise_state import EnterpriseState
from .utils.nodes.initial_intent import classify_user_query
from .utils.graphs.policy_graph import policy_graph
from .utils.graphs.email_graph import email_graph
from .utils.graphs.personal_graph import personal_graph
from .utils.conditions.agent_condition import intent_router_condittion



#initialise graph
builder = StateGraph(EnterpriseState)

#ading nodes
builder.add_node('classify_user_query', classify_user_query)
builder.add_node('policy_graph', policy_graph)
builder.add_node('email_graph', email_graph)
builder.add_node('personal_graph', personal_graph)

#adding edges
builder.add_edge(START, 'classify_user_query')
builder.add_conditional_edges(
    'classify_user_query',
    intent_router_condittion,
    {
        "policy_graph": "policy_graph",
        "personal_graph": "personal_graph",
        "email_graph": "email_graph",
        "others": END
    }
)
builder.add_edge('policy_graph', END)
builder.add_edge('email_graph', END)
builder.add_edge('personal_graph', END)


#compiling graph
graph = builder.compile()

