from fastapi import APIRouter
from app.storage.chat_store import list_chats, create_chat
from ..services.graph_service import run_graph_sync
from ..schemas.chatrequest import ChatRequest

router = APIRouter(prefix="/chats", tags=["Chats"])

@router.get("/{user_id}")
def get_chats(user_id: str):
    return list_chats(user_id)


@router.post("/{user_id}")
def new_chat(user_id: str):
    return create_chat(user_id)


@router.post("/ai/send")
def chat_endpoint(payload: ChatRequest):
    response = run_graph_sync(
        user_id=payload.user_id,
        chat_id=payload.chat_id,
        user_message=payload.message
    )

    return {
        "status": "success",
        "data": response
    }