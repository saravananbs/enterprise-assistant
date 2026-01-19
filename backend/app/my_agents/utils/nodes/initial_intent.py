from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, AIMessage, HumanMessage
from dotenv import load_dotenv
from ..datatypes.initial_intent import IntentClassification
from ..prompts.initial_intent import INITIAL_INTENT_SYSTEM_PROMPT
from ..states.enterprise_state import EnterpriseState

load_dotenv()

llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
classifier = llm.with_structured_output(IntentClassification)

def classify_user_query(state: EnterpriseState):
    # if state.get("intent"):
    #     return {}
    
    if not isinstance(state['messages'][-1], HumanMessage):
        raise Exception("Need Human messages but got", type(state['messages'][-1]))
    
    response: IntentClassification = classifier.invoke(
        [SystemMessage(content=INITIAL_INTENT_SYSTEM_PROMPT)]
        + state["messages"]
    )
    return {
        "intent": response.intent,
        "policy_file": response.policy_file,
        "personal_data_type": response.personal_data_type,
        "query_translation": response.query_translation,
    }
