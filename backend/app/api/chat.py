from fastapi import APIRouter, WebSocket
from app.storage.chat_store import list_chats, create_chat
from ..services.websocket import chat_socket

router = APIRouter(prefix="/chats", tags=["Chats"])

@router.get("/{user_id}")
def get_chats(user_id: str):
    return list_chats(user_id)

@router.post("/{user_id}")
def new_chat(user_id: str):
    return create_chat(user_id)

@router.websocket("/ws/chat")
async def ws_chat(websocket: WebSocket):
    await chat_socket(websocket)
