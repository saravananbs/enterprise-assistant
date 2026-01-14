from pydantic import BaseModel, EmailStr
from typing import List, Optional, Literal

class SendEmailInput(BaseModel):
    to: List[EmailStr]
    subject: str
    body: str
    cc: Optional[List[EmailStr]] = None
    is_html: bool = False


class EmailAction(BaseModel):
    action: Literal["accept", "reject", "inplaceedit", "llmedit"]
    to: Optional[List[EmailStr]] = None
    subject: Optional[str] = None
    body: Optional[str] = None
    cc: Optional[List[EmailStr]] = None
    is_html: bool = False
    instructions: Optional[str] = None
