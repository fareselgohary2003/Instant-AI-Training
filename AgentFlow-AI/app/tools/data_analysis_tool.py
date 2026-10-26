import io
from typing import Any
import pandas as pd

MAX_FILE_BYTES = 10 * 1024 * 1024  # 10MB limit


def analyze_tabular_data(csv_content: str, filename: str = "dataset.csv") -> dict[str, Any]:
    """Perform safe, deterministic data analysis on CSV content using pandas.

    Does not execute any user-provided code, macros, or arbitrary SQL.
    """
    if not isinstance(csv_content, str) or not csv_content.strip():
        raise ValueError("Data content must not be empty.")

    if len(csv_content.encode("utf-8")) > MAX_FILE_BYTES:
        raise ValueError(f"File size exceeds maximum safety limit of {MAX_FILE_BYTES / (1024 * 1024):.0f}MB.")

    try:
        df = pd.read_csv(io.StringIO(csv_content))
    except Exception as exc:
        raise ValueError(f"Could not parse CSV tabular data: {exc}") from exc

    if df.empty:
        return {
            "filename": filename,
            "row_count": 0,
            "column_count": len(df.columns),
            "columns": list(df.columns),
            "summary": "The dataset is empty.",
            "metrics": {},
            "chart_data": [],
        }

    row_count = int(len(df))
    col_count = int(len(df.columns))

    column_info = []
    numeric_columns = []
    categorical_columns = []

    for col in df.columns:
        col_type = str(df[col].dtype)
        null_count = int(df[col].isnull().sum())
        null_percent = round((null_count / max(1, row_count)) * 100, 1)

        info: dict[str, Any] = {
            "name": str(col),
            "type": col_type,
            "missing_count": null_count,
            "missing_percent": null_percent,
        }

        if pd.api.types.is_numeric_dtype(df[col]):
            numeric_columns.append(col)
            info["mean"] = round(float(df[col].mean()), 2) if not df[col].dropna().empty else None
            info["median"] = round(float(df[col].median()), 2) if not df[col].dropna().empty else None
            info["min"] = round(float(df[col].min()), 2) if not df[col].dropna().empty else None
            info["max"] = round(float(df[col].max()), 2) if not df[col].dropna().empty else None
            info["std"] = round(float(df[col].std()), 2) if not df[col].dropna().empty else None
        else:
            categorical_columns.append(col)
            top_vals = df[col].value_counts().head(3).to_dict()
            info["top_values"] = {str(k): int(v) for k, v in top_vals.items()}

        column_info.append(info)

    # Prepare chart-ready data points (first 30 rows of numeric or first categorical + numeric)
    chart_data = []
    preview_df = df.head(30)
    for _, row in preview_df.iterrows():
        point: dict[str, Any] = {}
        for col in df.columns[:6]:  # Limit width for clean chart visualization
            val = row[col]
            if pd.isna(val):
                point[str(col)] = None
            elif isinstance(val, (int, float)):
                point[str(col)] = round(float(val), 2)
            else:
                point[str(col)] = str(val)
        chart_data.append(point)

    summary = (
        f"Analyzed {row_count:,} rows across {col_count} columns "
        f"({len(numeric_columns)} numeric, {len(categorical_columns)} categorical). "
        f"Missing values total: {int(df.isnull().sum().sum())}."
    )

    return {
        "filename": filename,
        "row_count": row_count,
        "column_count": col_count,
        "numeric_columns": [str(c) for c in numeric_columns],
        "categorical_columns": [str(c) for c in categorical_columns],
        "columns": column_info,
        "chart_data": chart_data,
        "summary": summary,
    }
