from pydantic import BaseModel, EmailStr
from typing import List, Optional, Literal

class SendEmailInput(BaseModel):
    to: List[EmailStr]
    subject: str
    body: str
    cc: Optional[List[EmailStr]] = None
    is_html: bool = False


class EmailAction(SendEmailInput):
    action: Literal["accept", "reject", "inplaceedit", "llmedit"]
    instructions: Optional[str] = None
