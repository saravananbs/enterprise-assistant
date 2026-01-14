from sqlalchemy import update
from sqlalchemy.orm import Session
from ..crud.chat_histroy import get_chat_history, append_chat_messages


def append_chat(db: Session, thread_id: str, messages: list[dict]) -> bool:
    user_id, chat_id = thread_id.split(":")
    response = append_chat_messages(db=db, user_id=user_id, chat_id=chat_id, messages=messages)
    return response


def get_chat(db: Session, thread_id: str) -> list[dict]:
    user_id, chat_id = thread_id.split(":")
    response = get_chat_history(db=db, user_id=user_id, chat_id=chat_id)
    return response
