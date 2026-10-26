import pytest
from unittest.mock import MagicMock, patch

from app.agents.supervisor import create_deterministic_fallback_plan, validate_plan_structure
from app.tools.data_analysis_tool import analyze_tabular_data
from app.tools.email_tool import preview_email, send_email, validate_email_address
from app.tools.text_analysis_tool import analyze_text
from app.tools.weather_tool import get_weather


def test_text_analysis_accuracy():
    text = "The engineering team delivered great results, high reliability, and clean code."
    res = analyze_text(text)
    assert res["word_count"] == 11
    assert res["sentence_count"] == 1
    assert res["average_word_length"] > 4.0
    assert len(res["keywords"]) > 0
    # Positive sentiment check
    assert res["deterministic_sentiment"]["label"] == "positive"
    assert res["deterministic_sentiment"]["positive_terms"] >= 2


def test_text_analysis_empty_rejected():
    with pytest.raises(ValueError, match="must not be empty"):
        analyze_text("   ")


def test_text_analysis_length_limit():
    huge_text = "a" * 150_000
    with pytest.raises(ValueError, match="exceeds maximum allowed length"):
        analyze_text(huge_text)


def test_email_validation():
    valid = validate_email_address("operator@company.org")
    assert valid == "operator@company.org"

    with pytest.raises(ValueError, match="invalid"):
        validate_email_address("not-an-email")


def test_email_preview_does_not_send():
    preview = preview_email("user@example.com", "Test Subject", "Test Body")
    assert preview["status"] == "preview"
    assert preview["recipient"] == "user@example.com"
    assert preview["requires_approval"] is True


def test_email_send_without_approval_blocked():
    with pytest.raises(PermissionError, match="requires explicit server-side approval"):
        send_email("user@example.com", "Subject", "Body", approved=False)


@patch("httpx.Client")
def test_weather_tool_mocked_success(mock_client_class):
    mock_client = MagicMock()
    mock_client_class.return_value.__enter__.return_value = mock_client

    # Mock geocoding response
    geo_res = MagicMock()
    geo_res.json.return_value = {
        "results": [{"name": "Cairo", "country": "Egypt", "latitude": 30.04, "longitude": 31.23}]
    }
    geo_res.raise_for_status = MagicMock()

    # Mock weather response
    weather_res = MagicMock()
    weather_res.json.return_value = {
        "current": {
            "temperature_2m": 26.5,
            "apparent_temperature": 27.0,
            "weather_code": 1,
            "relative_humidity_2m": 45,
            "wind_speed_10m": 8.0,
            "time": "2026-10-26T12:00",
        }
    }
    weather_res.raise_for_status = MagicMock()

    mock_client.get.side_effect = [geo_res, weather_res]

    weather = get_weather("Cairo")
    assert weather["city"] == "Cairo"
    assert weather["temperature_c"] == 26.5
    assert weather["conditions"] == "Mainly clear"


def test_weather_empty_city_rejected():
    with pytest.raises(ValueError, match="must not be empty"):
        get_weather("")


def test_data_analysis_tool():
    csv_sample = (
        "Name,Department,Salary\n"
        "Alice,Engineering,120000\n"
        "Bob,Engineering,110000\n"
        "Charlie,Product,95000\n"
        "Diana,Design,90000\n"
    )
    result = analyze_tabular_data(csv_sample, "staff.csv")
    assert result["row_count"] == 4
    assert result["column_count"] == 3
    assert "Salary" in result["numeric_columns"]
    salary_col = next(c for c in result["columns"] if c["name"] == "Salary")
    assert salary_col["mean"] == 103750.0
    assert salary_col["min"] == 90000.0
    assert len(result["chart_data"]) == 4


def test_supervisor_plan_validation():
    valid_plan = {
        "goal": "Test Goal",
        "steps": [
            {
                "step_id": 1,
                "agent": "weather_agent",
                "description": "Fetch weather",
                "parameters": {"city": "Cairo"},
            }
        ],
        "requires_approval": False,
    }
    validated = validate_plan_structure(valid_plan)
    assert validated["goal"] == "Test Goal"
    assert validated["requires_approval"] is False

    # Unknown agent must be rejected
    invalid_plan = {
        "goal": "Bad Goal",
        "steps": [{"step_id": 1, "agent": "unknown_hacker_agent", "parameters": {}}],
    }
    with pytest.raises(ValueError, match="unknown agent"):
        validate_plan_structure(invalid_plan)


def test_supervisor_deterministic_fallback():
    plan = create_deterministic_fallback_plan("Check the weather in Paris and analyze text 'Antigravity rocks'")
    assert len(plan["steps"]) >= 2
    agents = [s["agent"] for s in plan["steps"]]
    assert "weather_agent" in agents
    assert "text_analysis_agent" in agents
