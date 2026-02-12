from typing import Optional, List, Any
from langgraph.graph import MessagesState
from ..datatypes.email_query import SendEmailInput

class EnterpriseState(MessagesState):
    intent: Optional[str] = None
    policy_file: Optional[str] = None
    personal_data_type: Optional[str] = None
    query_translation: Optional[str] = None
    translated_queries: Optional[List[str]] = None
    retrieved_context: Optional[List[Any]] = None
    drafted_email: Optional[SendEmailInput] = None