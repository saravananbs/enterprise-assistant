from sqlalchemy import update
from sqlalchemy.orm import Session
from ..models.chat import ChatHistory

def append_chat_messages(db: Session, user_id: str, chat_id: str, messages: list[dict]) -> bool:
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
    result = db.execute(stmt)
    if result.rowcount == 0:
        db.add(
            ChatHistory(
                chat_id=chat_id,
                user_id=user_id,
                chats=messages
            )
        )
    db.commit()
    return True


def get_chat_history(db: Session, user_id: str, chat_id) -> list[dict]:
    chat = (
        db.query(ChatHistory.chats)
        .filter(
            ChatHistory.chat_id == chat_id,
            ChatHistory.user_id == user_id
        )
        .one_or_none()
    )
    return chat.chats if chat else []
