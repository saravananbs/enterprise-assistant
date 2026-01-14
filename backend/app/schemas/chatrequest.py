from pydantic import BaseModel
from typing import Literal, Optional
from ..my_agents.utils.datatypes.email_query import SendEmailInput

class ChatRequest(BaseModel):
    user_id: str
    chat_id: str
    message: str


class InterruptResponse(BaseModel):
    action: Literal["accept", "reject", "llmedit", "inplaceedit"]
    edited_email: Optional[SendEmailInput]
    feedback: Optional[str]
