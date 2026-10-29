"""
Tests for FastAPI endpoints, security, and backward compatibility.
"""

from __future__ import annotations

from pathlib import Path
import pytest
from fastapi.testclient import TestClient

import database
from config import ALERTS_DIR, BASE_DIR, INCIDENTS_DIR
from main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Provide a TestClient connected to an isolated database and test folders."""
    db_file = tmp_path / "test_api.db"
    monkeypatch.setattr(database, "DB_PATH", db_file)
    database.init_db()

    # Prepopulate with 2 test incidents
    test_img = INCIDENTS_DIR / "test_api_img.jpg"
    test_img.write_bytes(b"\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xFF\xDB\x00C\x00")

    id1 = database.add_incident(
        track_id=8,
        event_type="phone_detected_review_required",
        confidence=0.78,
        screenshot_path=str(test_img),
        notes="Frame 10 test.",
    )

    id2 = database.add_incident(
        track_id=15,
        event_type="phone_detected_review_required",
        confidence=0.62,
        screenshot_path="alerts/screenshots/nonexistent.jpg",
        notes="Frame 50 test.",
    )

    with TestClient(app) as test_client:
        yield {
            "client": test_client,
            "id1": id1,
            "id2": id2,
            "test_img": test_img,
            "tmp_path": tmp_path,
        }

    # Cleanup
    if test_img.is_file():
        try:
            test_img.unlink()
        except Exception:
            pass


def test_home_endpoint(client):
    """Verify root endpoint."""
    resp = client["client"].get("/")
    assert resp.status_code == 200
    assert "ExamGuard" in resp.json()["message"]


def test_system_info_endpoint(client):
    """Verify system info endpoint."""
    resp = client["client"].get("/api/system-info")
    assert resp.status_code == 200
    data = resp.json()
    assert data["app"] == "ExamGuard"
    assert "model_exists" in data
    assert "stats" in data


def test_list_and_get_incidents(client):
    """Verify listing and retrieving specific incident."""
    resp = client["client"].get("/api/incidents")
    assert resp.status_code == 200
    incidents = resp.json()
    assert len(incidents) >= 2

    # Get single incident
    resp_single = client["client"].get(f"/api/incidents/{client['id1']}")
    assert resp_single.status_code == 200
    assert resp_single.json()["id"] == client["id1"]
    assert resp_single.json()["track_id"] == 8


def test_get_stats_endpoint(client):
    """Verify stats endpoint returns expected keys."""
    resp = client["client"].get("/api/stats")
    assert resp.status_code == 200
    stats = resp.json()
    assert "total_incidents" in stats
    assert "pending" in stats
    assert "reviewed" in stats
    assert "dismissed" in stats
    assert stats["total_incidents"] >= 2


def test_patch_incident_review(client):
    """Verify PATCH review updates status and notes."""
    inc_id = client["id1"]
    payload = {
        "status": "reviewed",
        "notes": "Reviewed by exam supervisor: suspicious phone visible on desk.",
    }
    resp = client["client"].patch(f"/api/incidents/{inc_id}/review", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["incident"]["review_status"] == "reviewed"
    assert "suspicious phone visible" in data["incident"]["notes"]


def test_get_incident_image_safe(client):
    """Verify image endpoint serves legitimate images."""
    inc_id = client["id1"]
    resp = client["client"].get(f"/api/incidents/{inc_id}/image")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("image/")


def test_get_incident_image_traversal_blocked(client):
    """Verify path traversal outside permitted folders is blocked with 403."""
    # Create incident with malicious path outside allowed folders
    malicious_id = database.add_incident(
        track_id=99,
        event_type="phone_detected_review_required",
        screenshot_path="../../../Windows/System32/drivers/etc/hosts",
    )

    resp = client["client"].get(f"/api/incidents/{malicious_id}/image")
    assert resp.status_code == 403
    assert "Invalid image path" in resp.json()["detail"]


def test_jobs_endpoints(client):
    """Verify listing and detail endpoints for jobs."""
    job_id = "api_test_job_1"
    database.create_job(job_id=job_id, source_video="exam.mp4", total_frames=100)

    resp = client["client"].get("/api/jobs")
    assert resp.status_code == 200
    jobs = resp.json()
    assert any(j["job_id"] == job_id for j in jobs)

    resp_detail = client["client"].get(f"/api/jobs/{job_id}")
    assert resp_detail.status_code == 200
    assert resp_detail.json()["source_video"] == "exam.mp4"
