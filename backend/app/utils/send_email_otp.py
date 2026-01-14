import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import os

load_dotenv()

def send_otp_email(receiver_email, otp):
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
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()  
        server.login(sender_email, sender_password)
        server.send_message(message)
        server.quit()
        print(f"otp send to  {receiver_email}")
        return True
    except Exception as e:
        print(f"error is: {e}")
        return False
