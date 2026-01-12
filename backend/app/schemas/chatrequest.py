from pydantic import BaseModel

class ChatRequest(BaseModel):
    user_id: str
    chat_id: str
    message: str