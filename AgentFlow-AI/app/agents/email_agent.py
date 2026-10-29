from typing import Any
from app.tools.email_tool import preview_email, send_email


def run_email_agent(parameters: dict[str, Any], approved: bool = False) -> dict[str, Any]:
    """Execute the email agent.

    If not approved, returns a preview and marks status as awaiting_approval.
    If approved is True, attempts SMTP transmission.
    """
    recipient = parameters.get("recipient")
    subject = parameters.get("subject")
    body = parameters.get("body")

    if not recipient or not subject or not body:
        raise ValueError("Email agent requires 'recipient', 'subject', and 'body' parameters.")

    if not approved:
        # Generate safe preview without side-effects
        preview = preview_email(recipient, subject, body)
        return {
            "status": "awaiting_approval",
            "preview": preview,
            "requires_approval": True,
            "message": "Email preview generated. Explicit human approval is required before delivery.",
        }

    # If approved is verified on backend
    return send_email(recipient, subject, body, approved=True)
