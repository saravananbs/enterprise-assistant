import base64
from email.message import EmailMessage
from googleapiclient.discovery import build
from langchain_core.tools import tool
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from sqlalchemy.orm import Session
from datetime import datetime
from ..db.models import UserOAuthCredentials
from ..db.connection import SessionLocal
from cryptography.fernet import Fernet
from ..datatypes.email_query import SendEmailInput


# FERNET_KEY = os.environ["OAUTH_ENCRYPTION_KEY"]
# fernet = Fernet(FERNET_KEY)


def encrypt_credentials(data: dict) -> bytes:
    return #fernet.encrypt(json.dumps(data).encode())


def decrypt_credentials(blob: bytes) -> dict:
    return #json.loads(fernet.decrypt(blob).decode())


def load_user_oauth_token(user_id: str) -> Credentials:
    """
    Load and refresh OAuth token securely for a user.
    """

    with SessionLocal() as db:  # type Session
        record = (
            db.query(UserOAuthCredentials)
            .filter(
                UserOAuthCredentials.user_id == user_id,
                UserOAuthCredentials.provider == "google"
            )
            .first()
        )

        if not record:
            raise PermissionError("User has not connected email account")

        # 1. Decrypt credentials
        creds_data = decrypt_credentials(record.encrypted_credentials)

        # 2. Build Credentials object
        creds = Credentials(
            token=creds_data["token"],
            refresh_token=creds_data["refresh_token"],
            token_uri=creds_data["token_uri"],
            client_id=creds_data["client_id"],
            client_secret=creds_data["client_secret"],
            scopes=creds_data["scopes"],
        )

        # 3. Refresh if expired
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())

            # 4. Persist refreshed token
            creds_data["token"] = creds.token
            creds_data["refresh_token"] = creds.refresh_token

            record.encrypted_credentials = encrypt_credentials(creds_data)
            record.updated_at = datetime.utcnow()
            db.commit()

        return creds


def send_email_via_provider(oauth_token, to, subject, body, cc=None, is_html=False):
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


@tool
def send_email_tool(input: SendEmailInput, user_id: str):
    """
    Send an email on behalf of the authenticated user.
    """
    print("send_email_tool executed")
    return {"status":"sent"}
    if not input.to:
        raise ValueError("Recipient list cannot be empty")

    if len(input.to) > 10:
        raise ValueError("Too many recipients")

    oauth_token = load_user_oauth_token(user_id)

    send_email_via_provider(
        oauth_token=oauth_token,
        to=input.to,
        subject=input.subject,
        body=input.body,
        cc=input.cc,
        is_html=input.is_html
    )

    # log_email_event(user_id, input)

    return {"status": "sent"}


