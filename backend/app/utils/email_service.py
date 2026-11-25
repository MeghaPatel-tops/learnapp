import logging
import smtplib
from email.message import EmailMessage

from app.config import get_settings

logger = logging.getLogger("lms.email")


def send_email_notification(to_email: str, subject: str, body: str) -> bool:
    """
    Send an email via SMTP when EMAIL_ENABLED=true.
    In local/dev mode when disabled, logs the dispatch safely without secrets.
    """
    settings = get_settings()
    if not settings.EMAIL_ENABLED or not settings.SMTP_HOST:
        logger.info("Email delivery skipped (EMAIL_ENABLED=false) to=%s subject=%s", to_email, subject)
        return False

    msg = EmailMessage()
    msg["From"] = settings.SMTP_FROM
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
            server.starttls()
            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as exc:
        logger.warning("Failed to send email to=%s: %s", to_email, exc)
        return False
