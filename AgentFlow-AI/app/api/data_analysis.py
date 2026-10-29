from fastapi import APIRouter, File, HTTPException, UploadFile
from app.schemas.data_analysis import DataAnalysisRequest, DataAnalysisResponse
from app.tools.data_analysis_tool import analyze_tabular_data

router = APIRouter(prefix="/api/data", tags=["Data Analysis"])


@router.post("/analyze", response_model=DataAnalysisResponse, summary="Analyze tabular CSV data")
def analyze_csv_data(payload: DataAnalysisRequest) -> DataAnalysisResponse:
    try:
        res = analyze_tabular_data(payload.csv_content, filename=payload.filename)
        return DataAnalysisResponse(**res)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/upload", response_model=DataAnalysisResponse, summary="Upload and analyze CSV file")
async def upload_csv_file(file: UploadFile = File(...)) -> DataAnalysisResponse:
    if not file.filename or not file.filename.lower().endswith((".csv", ".txt")):
        raise HTTPException(status_code=400, detail="Only .csv and tabular .txt files are supported.")

    content_bytes = await file.read()
    try:
        content_str = content_bytes.decode("utf-8", errors="replace")
        res = analyze_tabular_data(content_str, filename=file.filename)
        return DataAnalysisResponse(**res)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to analyze file: {exc}") from exc
