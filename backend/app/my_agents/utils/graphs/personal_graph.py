from langgraph.graph import START, END, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from ..states.enterprise_state import EnterpriseState
from ..nodes.personal_graph import invoke_llm_with_tools, tools

#initalise the graph
builder = StateGraph(EnterpriseState)


#adding noded
builder.add_node('invoke_llm_with_tools', invoke_llm_with_tools)
builder.add_node('tools', ToolNode(tools=tools))


#adding edges
builder.add_edge(START, 'invoke_llm_with_tools')
builder.add_conditional_edges('invoke_llm_with_tools', tools_condition)
builder.add_edge('tools', 'invoke_llm_with_tools')


#compiling graph
personal_graph = builder.compile()