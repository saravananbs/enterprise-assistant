from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.services.chat_store import list_chats, create_chat
from ..schemas.chatrequest import ChatRequest
from ..my_agents.utils.datatypes.email_query import EmailAction
from ..utils.stream_generator import chat_event_generator, interrupt_event_generator

router = APIRouter(prefix="/chats", tags=["Chats"])

@router.get("/{user_id}")
def get_chats(user_id: str):
    return list_chats(user_id)


@router.post("/{user_id}")
def new_chat(user_id: str):
    return create_chat(user_id)


@router.post("/ai/send")
def chat_endpoint(payload: ChatRequest):
    return StreamingResponse(
        chat_event_generator(payload=payload),
        media_type="text/event-stream"
    )

@router.post("/ai/interrupt/respond")
def interrupt_response_endpoint(user_id: str, chat_id: str, payload: EmailAction):
    return StreamingResponse(
        interrupt_event_generator(user_id=user_id, chat_id=chat_id, payload=payload),
        media_type="text/event-stream"
    )
