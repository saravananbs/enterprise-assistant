from langgraph.graph import START, END, StateGraph
from utils.states.enterprise_state import EnterpriseState
from ..nodes.policy_graph import  (
    query_translation_node, retrival_node, answer_generation_node
)

#initialising graph
builder = StateGraph(EnterpriseState)

#adding nodes
builder.add_node('query_translation', query_translation_node)
builder.add_node('retrival_node', retrival_node)
builder.add_node('answer_generation_node', answer_generation_node)

#adding edges
builder.add_edge(START, 'query_translation')
builder.add_edge('query_translation', 'retrival_node')
builder.add_edge('retrival_node', "answer_generation_node")
builder.add_edge('answer_generation_node', END)

#compiling graph
policy_graph = builder.compile()