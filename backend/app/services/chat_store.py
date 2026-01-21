from datetime import datetime
from sqlalchemy import select
from ..my_agents.utils.db.connection import AsyncSessionLocal
from ..models.chat import Chat


async def list_chats(user_id: str):
    async with AsyncSessionLocal() as db:  
        stmt = (
            select(Chat)
            .where(Chat.user_id == user_id)
            .order_by(Chat.created_at.desc())
        )
        result = await db.execute(stmt)
        chats = result.scalars().all()
        return [
            {
                "chat_id": str(chat.chat_id),
                "title": chat.title,
                "created_at": chat.created_at.isoformat()
            }
            for chat in chats
        ]


async def create_chat(user_id: str, title: str | None = None):
    async with AsyncSessionLocal() as db:
        chat = Chat(
            user_id=user_id,
            title=title or f"Chat: {datetime.now()}"
        )

        db.add(chat)
        await db.commit()
        await db.refresh(chat)

        return {
            "chat_id": str(chat.chat_id),
            "title": chat.title,
            "created_at": chat.created_at.isoformat()
        }
