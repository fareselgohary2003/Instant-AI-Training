"""
Tests for database schema initialization, migrations, CRUD operations, and job tracking.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
import pytest

import database


@pytest.fixture
def temp_db(tmp_path, monkeypatch):
    """Provide a fresh temporary SQLite database for test isolation."""
    test_db_path = tmp_path / "test_examguard.db"
    monkeypatch.setattr(database, "DB_PATH", test_db_path)
    database.init_db()
    return test_db_path


def test_init_db_creates_tables(temp_db):
    """Verify that init_db creates incidents and processing_jobs tables with all columns."""
    with database.get_connection() as conn:
        tables = [row["name"] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        assert "incidents" in tables
        assert "processing_jobs" in tables

        # Verify incidents columns
        cursor = conn.execute("PRAGMA table_info(incidents)")
        cols = {row["name"] for row in cursor.fetchall()}
        assert {"id", "timestamp", "track_id", "event_type", "confidence", "screenshot_path", "review_status", "notes", "source_video", "frame_number", "job_id"}.issubset(cols)


def test_add_and_get_incident(temp_db):
    """Verify adding an incident and retrieving it."""
    inc_id = database.add_incident(
        track_id=12,
        event_type="phone_detected_review_required",
        confidence=0.885,
        screenshot_path="alerts/screenshots/test.jpg",
        notes="Student looking down with phone.",
        source_video="exam_room_1.mp4",
        frame_number=145,
        job_id="job_test_001",
    )
    assert inc_id > 0

    inc = database.get_incident(inc_id)
    assert inc is not None
    assert inc["track_id"] == 12
    assert inc["event_type"] == "phone_detected_review_required"
    assert round(inc["confidence"], 3) == 0.885
    assert inc["review_status"] == "pending"
    assert inc["source_video"] == "exam_room_1.mp4"
    assert inc["frame_number"] == 145
    assert inc["job_id"] == "job_test_001"


def test_update_incident_review(temp_db):
    """Verify updating review status and notes."""
    inc_id = database.add_incident(
        track_id=5,
        event_type="phone_detected_review_required",
        confidence=0.75,
    )

    # Valid update
    ok = database.update_incident_review(inc_id, "reviewed", "Confirmed phone usage in lap.")
    assert ok is True

    updated = database.get_incident(inc_id)
    assert updated["review_status"] == "reviewed"
    assert updated["notes"] == "Confirmed phone usage in lap."

    # Invalid status raises ValueError
    with pytest.raises(ValueError):
        database.update_incident_review(inc_id, "invalid_status", "test notes")


def test_get_incidents_filtering_and_search(temp_db):
    """Verify filtering by status and text searching."""
    database.add_incident(track_id=1, event_type="phone_detected_review_required", notes="Alpha test")
    id2 = database.add_incident(track_id=2, event_type="phone_detected_review_required", notes="Beta review")
    database.update_incident_review(id2, "dismissed", "False alert")

    # Filter all
    all_rows = database.get_incidents()
    assert len(all_rows) == 2

    # Filter pending
    pending_rows = database.get_incidents(status="pending")
    assert len(pending_rows) == 1
    assert pending_rows[0]["track_id"] == 1

    # Filter dismissed
    dismissed_rows = database.get_incidents(status="dismissed")
    assert len(dismissed_rows) == 1
    assert dismissed_rows[0]["track_id"] == 2

    # Search by text
    search_rows = database.get_incidents(search="Alpha")
    assert len(search_rows) == 1
    assert search_rows[0]["track_id"] == 1

    search_dismissed = database.get_incidents(search="False alert")
    assert len(search_dismissed) == 1
    assert search_dismissed[0]["id"] == id2


def test_get_stats(temp_db):
    """Verify aggregate statistics calculation."""
    database.add_incident(track_id=1, event_type="phone_detected_review_required")
    id2 = database.add_incident(track_id=2, event_type="phone_detected_review_required")
    id3 = database.add_incident(track_id=3, event_type="phone_detected_review_required")

    database.update_incident_review(id2, "reviewed", "Notes")
    database.update_incident_review(id3, "dismissed", "Notes")

    stats = database.get_stats()
    assert stats["total_incidents"] == 3
    assert stats["pending"] == 1
    assert stats["reviewed"] == 1
    assert stats["dismissed"] == 1


def test_job_lifecycle(temp_db):
    """Verify creating and updating processing jobs."""
    job_id = "test_job_123"
    database.create_job(
        job_id=job_id,
        source_video="sample.mp4",
        output_video="outputs/processed_sample.mp4",
        total_frames=300,
        fps=30.0,
    )

    job = database.get_job(job_id)
    assert job is not None
    assert job["status"] == "processing"
    assert job["total_frames"] == 300

    database.update_job(
        job_id=job_id,
        status="completed",
        processed_frames=300,
        incident_count=2,
        people_count=4,
    )

    completed_job = database.get_job(job_id)
    assert completed_job["status"] == "completed"
    assert completed_job["processed_frames"] == 300
    assert completed_job["incident_count"] == 2
    assert completed_job["people_count"] == 4
    assert completed_job["end_time"] is not None
