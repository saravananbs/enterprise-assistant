import smtplib
from email.mime.text import MIMEText
from aiosmtplib import send
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import os

load_dotenv()

async def send_otp_email(receiver_email, otp):
    sender_email = f"{os.getenv('SMTP_EMAIL')}"
    sender_password = f"{os.getenv('SMTP_APP_PASSWORD')}" 
    smtp_server = "smtp.gmail.com"
    smtp_port = 587

    subject = "your enterprise assistant login otp is here"
    body = f"your otp is {otp}"
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = subject
    message.attach(MIMEText(body, "html"))
    try:
        await send(
            message,
            hostname=smtp_server,
            port=smtp_port,
            start_tls=True,
            username=sender_email,
            password=sender_password,
        )
        print(f"OTP sent to {receiver_email}")
        return True
    except Exception as e:
        print(f"error is: {e}")
        return False
