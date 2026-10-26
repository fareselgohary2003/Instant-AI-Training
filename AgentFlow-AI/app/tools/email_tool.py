import os
import smtplib
from email.message import EmailMessage
from typing import Any

from dotenv import load_dotenv
from email_validator import EmailNotValidError, validate_email

load_dotenv()


def validate_email_address(email: str) -> str:
    """Validate and normalize an email address."""
    if not isinstance(email, str) or not email.strip():
        raise ValueError("Recipient email address cannot be empty.")
    try:
        validated = validate_email(email.strip(), check_deliverability=False)
        return validated.normalized
    except EmailNotValidError as exc:
        raise ValueError(f"The recipient email address '{email}' is invalid.") from exc


def preview_email(recipient: str, subject: str, body: str) -> dict[str, Any]:
    """Prepare a preview of an email without sending it."""
    valid_recipient = validate_email_address(recipient)
    clean_subject = (subject or "").strip()
    clean_body = (body or "").strip()

    if not clean_subject:
        raise ValueError("Email subject cannot be empty.")
    if not clean_body:
        raise ValueError("Email body cannot be empty.")

    sender_email = os.getenv("SENDER_EMAIL", os.getenv("SMTP_USERNAME", "noreply@aitaskagent.local"))

    return {
        "status": "preview",
        "sender": sender_email,
        "recipient": valid_recipient,
        "subject": clean_subject,
        "body_preview": clean_body,
        "character_count": len(clean_body),
        "requires_approval": True,
        "message": "Email prepared and awaiting human approval before transmission.",
    }


def send_email(
    recipient: str,
    subject: str,
    body: str,
    approved: bool = False,
) -> dict[str, Any]:
    """Send an email using configured SMTP provider ONLY when approval is verified."""
    if not approved:
        raise PermissionError(
            "Email transmission is a protected operation that requires explicit server-side approval."
        )

    valid_recipient = validate_email_address(recipient)
    clean_subject = (subject or "").strip()
    clean_body = (body or "").strip()

    if not clean_subject:
        raise ValueError("Email subject cannot be empty.")
    if not clean_body:
        raise ValueError("Email body cannot be empty.")

    smtp_host = os.getenv("SMTP_HOST", "")
    smtp_port_raw = os.getenv("SMTP_PORT", "587")
    try:
        smtp_port = int(smtp_port_raw)
    except ValueError:
        smtp_port = 587

    smtp_username = os.getenv("SMTP_USERNAME", "")
    smtp_password = os.getenv("SMTP_PASSWORD", "")
    sender_email = os.getenv("SENDER_EMAIL", smtp_username)

    if not all((smtp_host, smtp_username, smtp_password, sender_email)):
        raise RuntimeError(
            "SMTP credentials are not configured in the backend environment. "
            "Please configure SMTP_HOST, SMTP_PORT, SMTP_USERNAME, and SMTP_PASSWORD in .env."
        )

    message = EmailMessage()
    message["From"] = sender_email
    message["To"] = valid_recipient
    message["Subject"] = clean_subject
    message.set_content(clean_body)

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=20) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(message)
    except (OSError, smtplib.SMTPException) as exc:
        raise RuntimeError(f"Email delivery failed through SMTP server: {exc}") from exc

    return {
        "success": True,
        "recipient": valid_recipient,
        "subject": clean_subject,
        "status": "delivered",
        "message": "Email accepted by the SMTP server for delivery.",
    }
