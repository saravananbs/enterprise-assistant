from datetime import datetime
from ..my_agents.utils.db.connection import AsyncSessionLocal
from ..models.chat import Chat


async def list_chats(user_id: str):
    with AsyncSessionLocal() as db:
        chats = await (
            db.query(Chat)
            .filter(Chat.user_id == user_id)
            .order_by(Chat.created_at.desc())
            .all()
        )

        return [
            {
                "chat_id": str(chat.chat_id),
                "title": chat.title,
                "created_at": chat.created_at.isoformat()
            }
            for chat in chats
        ]


async def create_chat(user_id: str, title: str | None = None):
    with AsyncSessionLocal() as db:
        chat = Chat(
            user_id=user_id,
            title=title or f"Chat: {datetime.now()}"
        )

        db.add(chat)
        db.commit()
        await db.refresh(chat)

        return {
            "chat_id": str(chat.chat_id),
            "title": chat.title,
            "created_at": chat.created_at.isoformat()
        }
