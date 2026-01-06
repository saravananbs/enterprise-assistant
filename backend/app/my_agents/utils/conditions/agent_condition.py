from utils.states.enterprise_state import EnterpriseState

def intent_router_condittion(state: EnterpriseState):
    intent = state.get("intent")

    if intent == "policy_query":
        return "policy_graph"
    if intent == "personal_details_query":
        return "personal_graph"
    if intent == "email_writing":
        return "email_graph"

    return "others"