from typing import Any
from app.tools.data_analysis_tool import analyze_tabular_data


def run_data_analysis_agent(parameters: dict[str, Any]) -> dict[str, Any]:
    """Execute data analysis agent on CSV tabular content."""
    csv_content = parameters.get("csv_content") or parameters.get("data")
    filename = parameters.get("filename", "dataset.csv")

    if not isinstance(csv_content, str) or not csv_content.strip():
        # Provide sample tabular demonstration if empty
        csv_content = (
            "Task,Agent,Duration_Sec,Status\n"
            "Weather Check,weather_agent,1.2,completed\n"
            "Text Analysis,text_analysis_agent,0.8,completed\n"
            "Web Research,research_agent,2.4,completed\n"
            "Email Notification,email_agent,0.5,awaiting_approval\n"
            "Summary Report,general_agent,1.6,completed\n"
        )
        filename = "default_workflow_metrics.csv"

    return analyze_tabular_data(csv_content, filename=filename)
