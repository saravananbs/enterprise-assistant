from sqlalchemy import update, select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.chat import ChatHistory, Chat

async def append_chat_messages(db: AsyncSession, user_id: str, chat_id: str, messages: list[dict]) -> bool:
    stmt = (
        update(ChatHistory)
        .where(
            ChatHistory.chat_id == chat_id,
            ChatHistory.user_id == user_id
        )
        .values(
            chats=ChatHistory.chats.op("||")(messages)
        )
    )
    result = await db.execute(stmt)
    if result.rowcount == 0:
        db.add(
            ChatHistory(
                chat_id=chat_id,
                user_id=user_id,
                chats=messages
            )
        )
    await db.commit()
    return True


async def get_chat_history(db: AsyncSession, user_id: str, chat_id) -> list[dict]:
    stmt = (
        select(ChatHistory.chats)
        .where(
            ChatHistory.chat_id == chat_id,
            ChatHistory.user_id == user_id,
        )
    )
    result = await db.execute(stmt)
    chats = result.scalar_one_or_none()
    return chats if chats else []

async def delete_chat_history(db: AsyncSession, user_id: str, chat_id) -> bool:
    stmt = (
        delete(ChatHistory)
        .where(
            ChatHistory.chat_id == chat_id,
            ChatHistory.user_id == user_id
        )
    )
    result = await db.execute(stmt)
    stmt = (
        delete(Chat)
        .where(
            Chat.chat_id == chat_id,
            Chat.user_id == user_id
        )
    )
    res = await db.execute(stmt)
    await db.commit()
    return result.rowcount > 0 or res.rowcount > 0
