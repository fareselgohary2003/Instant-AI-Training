from fastapi import APIRouter
from app.config import get_settings_status
from app.schemas.settings import SettingsStatusResponse

router = APIRouter(prefix="/api/settings", tags=["Settings"])


@router.get("/status", response_model=SettingsStatusResponse, summary="Get safe configuration and integration status")
def get_status() -> SettingsStatusResponse:
    data = get_settings_status()
    return SettingsStatusResponse(**data)
