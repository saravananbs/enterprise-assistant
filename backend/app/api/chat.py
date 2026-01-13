from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from app.services.chat_store import list_chats, create_chat
from sqlalchemy.orm import Session
from ..schemas.chatrequest import ChatRequest
from ..services.chat_history import get_chat
from ..my_agents.utils.datatypes.email_query import EmailAction
from ..utils.stream_generator import chat_event_generator, interrupt_event_generator
from ..core.database import get_db

router = APIRouter(prefix="/chats", tags=["Chats"])

@router.get("/lists/{user_id}")
def get_chat_lists(user_id: str):
    return list_chats(user_id)


@router.post("/lists/{user_id}")
def create_new_chat(user_id: str):
    return create_chat(user_id)

@router.get("/history/{user_id}/{chat_id}")
def get_chat_history(
    user_id: str, 
    chat_id: str,
    db: Session = Depends(get_db),
):
    return get_chat(db=db, thread_id=f"{user_id}:{chat_id}")

@router.post("/ai/send")
def chat_endpoint(payload: ChatRequest, db:Session = Depends(get_db)):
    return StreamingResponse(
        chat_event_generator(db=db, payload=payload),
        media_type="text/event-stream"
    )

@router.post("/ai/interrupt/respond")
def interrupt_response_endpoint(user_id: str, chat_id: str, payload: EmailAction, db:Session = Depends(get_db)):
    return StreamingResponse(
        interrupt_event_generator(db=db, user_id=user_id, chat_id=chat_id, payload=payload),
        media_type="text/event-stream"
    )
