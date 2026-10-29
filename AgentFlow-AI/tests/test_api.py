import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from app.main import app
from app.db.database import init_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def ensure_db():
    init_db()


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "running"
    assert "AI Task Agent" in data["name"]


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_empty_goal_rejected():
    response = client.post("/api/workflows/run", json={"goal": "   "})
    assert response.status_code == 422


def test_agents_endpoint():
    response = client.get("/api/agents")
    assert response.status_code == 200
    agents = response.json()
    assert len(agents) >= 7
    agent_ids = [a["id"] for a in agents]
    assert "supervisor" in agent_ids
    assert "weather_agent" in agent_ids
    assert "text_analysis_agent" in agent_ids
    assert "email_agent" in agent_ids
    assert "code_execution_agent" in agent_ids


def test_settings_status_endpoint():
    response = client.get("/api/settings/status")
    assert response.status_code == 200
    data = response.json()
    assert "app_name" in data
    assert "groq_configured" in data
    assert "cors_origins" in data
    # Verify no raw secrets leaked
    assert "password" not in str(data).lower()
    assert "api_key" not in data


def test_history_endpoint():
    response = client.get("/api/workflows/history?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert "count" in data
    assert "items" in data
    assert isinstance(data["items"], list)


def test_history_detail_missing_id():
    response = client.get("/api/workflows/history/999999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_analytics_endpoint():
    response = client.get("/api/analytics")
    assert response.status_code == 200
    data = response.json()
    assert "total_workflows" in data
    assert "success_rate_percent" in data
    assert "agent_usage" in data
    assert "daily_volume" in data
