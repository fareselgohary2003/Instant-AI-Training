from typing import Any
from pydantic import BaseModel, Field


class DataAnalysisRequest(BaseModel):
    csv_content: str = Field(..., min_length=1, description="CSV formatted tabular text")
    filename: str = Field(default="data.csv", max_length=255)


class ColumnInfo(BaseModel):
    name: str
    type: str
    missing_count: int
    missing_percent: float
    mean: float | None = None
    median: float | None = None
    min: float | None = None
    max: float | None = None
    std: float | None = None
    top_values: dict[str, int] | None = None


class DataAnalysisResponse(BaseModel):
    filename: str
    row_count: int
    column_count: int
    numeric_columns: list[str]
    categorical_columns: list[str]
    columns: list[ColumnInfo]
    chart_data: list[dict[str, Any]]
    summary: str
