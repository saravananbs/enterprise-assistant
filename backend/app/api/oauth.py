from fastapi import APIRouter, HTTPException
from google_auth_oauthlib.flow import Flow
from datetime import datetime
from ..my_agents.utils.db.connection import SessionLocal
from ..my_agents.utils.db.models import UserOAuthCredentials
from ..my_agents.utils.tools.email_graph import encrypt_credentials
from ..auth.google_oauth import (
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    GOOGLE_REDIRECT_URI,
    GOOGLE_SCOPES,
    create_oauth_state, consume_oauth_state
)
 

router = APIRouter()

@router.get("/oauth/google/connect")
def connect_google(user_id: str):
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=GOOGLE_SCOPES,
        redirect_uri=GOOGLE_REDIRECT_URI,
    )

    state = create_oauth_state(user_id)
    auth_url, _ = flow.authorization_url(
        access_type="offline",      
        prompt="consent",           
        state=state,
        include_granted_scopes="true",
    )
    return {"authorization_url": auth_url}


@router.get("/oauth/google/callback")
def google_callback(code: str, state: str):
    user_id = consume_oauth_state(state)
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid OAuth state")

    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=GOOGLE_SCOPES,
        redirect_uri=GOOGLE_REDIRECT_URI,
    )

    flow.fetch_token(code=code)
    creds = flow.credentials
    if not creds or not creds.token:
        raise RuntimeError("OAuth token exchange failed")
    creds_data = {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": creds.scopes,
    }
    encrypted_blob = encrypt_credentials(creds_data)
    if not encrypted_blob:
        raise RuntimeError("Credential encryption failed")
    with SessionLocal() as db:
        record = (
            db.query(UserOAuthCredentials)
            .filter_by(user_id=user_id, provider="google")
            .first()
        )
        if record:
            record.encrypted_credentials = encrypted_blob
            record.updated_at = datetime.now()
        else:
            record = UserOAuthCredentials(
                user_id=user_id,
                provider="google",
                encrypted_credentials=encrypted_blob,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            db.add(record)
        db.commit()
    return {"status": "gmail_connected_successfully"}
