from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from app.services.chat_store import list_chats, create_chat
from sqlalchemy.ext.asyncio import AsyncSession
from ..schemas.chatrequest import ChatRequest
from ..services.chat_history import get_chat
from ..my_agents.utils.datatypes.email_query import EmailAction
from ..utils.stream_generator import chat_event_generator, interrupt_event_generator
from ..my_agents.utils.db.connection import get_async_session

router = APIRouter(prefix="/chats", tags=["Chats"])

@router.get("/lists/{user_id}")
async def get_chat_lists(user_id: str):
    return await list_chats(user_id)


@router.post("/lists/{user_id}")
async def create_new_chat(user_id: str):
    return await create_chat(user_id)

@router.get("/history/{user_id}/{chat_id}")
async def get_chat_history(
    user_id: str, 
    chat_id: str,
    db: AsyncSession = Depends(get_async_session),
):
    return await get_chat(db=db, thread_id=f"{user_id}:{chat_id}")

@router.post("/ai/send")
async def chat_endpoint(
    payload: ChatRequest,
    db: AsyncSession = Depends(get_async_session),
):
    return StreamingResponse(
        chat_event_generator(db=db, payload=payload),
        media_type="text/event-stream",
    )

@router.post("/ai/interrupt/respond")
async def interrupt_response_endpoint(
    user_id: str, 
    chat_id: str, 
    payload: EmailAction, 
    db:AsyncSession = Depends(get_async_session)
):
    return StreamingResponse(
        interrupt_event_generator(db=db, user_id=user_id, chat_id=chat_id, payload=payload),
        media_type="text/event-stream"
    )
