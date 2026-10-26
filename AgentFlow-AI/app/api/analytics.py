from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.analytics import AnalyticsResponse
from app.services.workflow_service import get_analytics_summary

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("", response_model=AnalyticsResponse, summary="Get real system analytics")
def get_analytics(db: Session = Depends(get_db)) -> AnalyticsResponse:
    data = get_analytics_summary(db)
    return AnalyticsResponse(**data)
