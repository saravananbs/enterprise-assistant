from typing import Literal, Optional
from pydantic import BaseModel, Field


IntentType = Literal[
    "policy_query",
    "personal_details_query",
    "email_writing",
    "others"
]

PolicyFile = Literal[
    "privacy_policy",
    "leave_policies",
    "remote_work_policy"
]

QueryTranslationType = Literal[
    "decomposition",     
    "rag_fusion",              
    "step_back_prompting",             
    "hypothetical_document_embeddings",
    "temporal_normalization",

]

class IntentClassification(BaseModel):
    intent: IntentType = Field(...  )

    policy_file: Optional[PolicyFile] = None
    personal_data_type: Optional[str] = None

    query_translation: QueryTranslationType = "rag_fusion"
