from typing import Any
from pydantic import BaseModel


class SettingsStatusResponse(BaseModel):
    app_name: str
    app_version: str
    llm_provider: str
    llm_model: str
    groq_configured: bool
    smtp_configured: bool
    smtp_host: str
    sender_email: str
    search_configured: bool
    search_provider: str
    database: str
    cors_origins: list[str]
