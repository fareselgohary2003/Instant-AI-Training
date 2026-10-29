from typing import Any
from pydantic import BaseModel


class AgentUsageStat(BaseModel):
    agent: str
    count: int


class DailyVolumeStat(BaseModel):
    date: str
    count: int
    completed: int
    failed: int


class AnalyticsResponse(BaseModel):
    total_workflows: int
    completed: int
    failed: int
    awaiting_approval: int
    running: int
    success_rate_percent: float
    avg_duration_seconds: float
    agent_usage: list[AgentUsageStat]
    daily_volume: list[DailyVolumeStat]
