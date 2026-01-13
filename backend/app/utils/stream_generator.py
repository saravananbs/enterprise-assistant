import json
from sqlalchemy.orm import Session
from ..schemas.chatrequest import ChatRequest
from ..services.graph_service import run_graph_sync


def chat_event_generator(db:Session, payload: ChatRequest):
    for event in run_graph_sync(
        db=db,
        user_id=payload.user_id,
        chat_id=payload.chat_id,
        user_message=payload.message
    ):
        yield f"data: {json.dumps(event)}\n\n"

def interrupt_event_generator(db: Session, user_id: str, chat_id: str, payload: ChatRequest):
    for event in run_graph_sync(
        db=db,
        user_id=user_id,
        chat_id=chat_id,
        interrupt_response=payload
    ):
        yield f"data: {json.dumps(event)}\n\n"