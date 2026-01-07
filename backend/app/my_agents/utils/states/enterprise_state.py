from typing import Optional, List, Dict
from langgraph.graph import MessagesState
from langchain_core.documents import Document
from ..datatypes.email_query import SendEmailInput

class EnterpriseState(MessagesState):
    intent: Optional[str] = None
    policy_file: Optional[str] = None
    personal_data_type: Optional[str] = None
    query_translation: Optional[str] = None
    translated_queries: Optional[List[str]] = None
    retrieved_context: Optional[List[Document]] = None
    drafted_email: Optional[SendEmailInput] = None
    user_id: str