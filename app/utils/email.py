import smtplib
from email.message import EmailMessage
import os
import asyncio
import logging

logger = logging.getLogger(__name__)

def _send_email_sync(to_email: str, subject: str, content: str):
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASSWORD")
    from_email = os.getenv("SMTP_FROM_EMAIL", "noreply@example.com")
    from_name = os.getenv("SMTP_FROM_NAME", "System")

    if not all([smtp_host, smtp_user, smtp_pass]):
        logger.warning("SMTP credentials not fully configured. Email not sent.")
        return False

    msg = EmailMessage()
    msg.set_content(content)
    msg['Subject'] = subject
    msg['From'] = f"{from_name} <{from_email}>"
    msg['To'] = to_email

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
        return True
    except Exception as e:
        logger.error(f"Error sending email to {to_email}: {e}")
        return False

async def send_email_async(to_email: str, subject: str, content: str):
    """Asynchronously send an email using smtplib via a thread pool."""
    return await asyncio.to_thread(_send_email_sync, to_email, subject, content)
