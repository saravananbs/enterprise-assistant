from pydantic import BaseModel, EmailStr
from typing import List, Optional

class SendEmailInput(BaseModel):
    to: List[EmailStr]
    subject: str
    body: str
    cc: Optional[List[EmailStr]] = None
    is_html: bool = False