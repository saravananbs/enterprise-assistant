import base64
import os
import json
from email.message import EmailMessage
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from datetime import datetime
from cryptography.fernet import Fernet
from sqlalchemy import select
import asyncio
from ..db.models import UserOAuthCredentials
from ..db.connection import AsyncSessionLocal
from ..datatypes.email_query import SendEmailInput


FERNET_KEY = os.environ["OAUTH_ENCRYPTION_KEY"]
fernet = Fernet(FERNET_KEY)


async def encrypt_credentials(data: dict) -> bytes:
    return fernet.encrypt(json.dumps(data).encode())


async def decrypt_credentials(blob: bytes) -> dict:
    return json.loads(fernet.decrypt(blob).decode())


async def load_user_oauth_token(user_id: str) -> Credentials | None:
    async with AsyncSessionLocal() as session:
        stmt = (
            select(UserOAuthCredentials)
            .where(
                UserOAuthCredentials.user_id == user_id,
                UserOAuthCredentials.provider == "google",
            )
        )
        result = await session.execute(stmt)
        record = result.scalars().first()
        if not record:
            return None

        creds_data = await decrypt_credentials(record.encrypted_credentials)

        creds = Credentials(
            token=creds_data["token"],
            refresh_token=creds_data["refresh_token"],
            token_uri=creds_data["token_uri"],
            client_id=creds_data["client_id"],
            client_secret=creds_data["client_secret"],
            scopes=creds_data["scopes"],
        )

        if creds.expired and creds.refresh_token:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(
                None,
                lambda: creds.refresh(Request())
            )

            creds_data["token"] = creds.token
            creds_data["refresh_token"] = creds.refresh_token

            record.encrypted_credentials = encrypt_credentials(creds_data)
            record.updated_at = datetime.now()
            await session.commit()
        return creds

def _send_email_sync(oauth_token, to, subject, body, cc=None, is_html=False):
    service = build("gmail", "v1", credentials=oauth_token)

    msg = EmailMessage()
    msg["To"] = ", ".join(to)
    msg["Subject"] = subject

    if cc:
        msg["Cc"] = ", ".join(cc)

    if is_html:
        msg.add_alternative(body, subtype="html")
    else:
        msg.set_content(body)

    encoded_msg = base64.urlsafe_b64encode(
        msg.as_bytes()
    ).decode()

    service.users().messages().send(
        userId="me",
        body={"raw": encoded_msg}
    ).execute()

async def send_email_via_provider(oauth_token, to: list[str], subject: str, body: str, cc: list[str] | None = None, is_html: bool = False):
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(
        None,
        _send_email_sync,
        oauth_token,
        to,
        subject,
        body,
        cc,
        is_html,
    )

async def send_email_tool(input: SendEmailInput, user_id: str):
    if not input.to:
        raise ValueError("Recipient list cannot be empty")

    if len(input.to) > 10:
        raise ValueError("Too many recipients")

    oauth_token = await load_user_oauth_token(user_id)

    if not oauth_token:
        return {"status": "not sent"}

    await send_email_via_provider(
        oauth_token=oauth_token,
        to=input.to,
        subject=input.subject,
        body=input.body,
        cc=input.cc,
        is_html=input.is_html,
    )

    return {"status": "sent"}