import os

GOOGLE_CLIENT_ID = os.environ["GOOGLE_CLIENT_ID"]
GOOGLE_CLIENT_SECRET = os.environ["GOOGLE_CLIENT_SECRET"]
GOOGLE_REDIRECT_URI = os.environ["GOOGLE_REDIRECT_URI"]

GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/gmail.send"
]

import uuid

_OAUTH_STATE_STORE = {}

def create_oauth_state(user_id: str) -> str:
    state = uuid.uuid4().hex
    _OAUTH_STATE_STORE[state] = user_id
    return state

def consume_oauth_state(state: str) -> str | None:
    return _OAUTH_STATE_STORE.pop(state, None)
