"""
SQLite database management for ExamGuard.
Maintains backward compatibility with cheating_system.db and performs safe schema upgrades.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Database is stored inside the project folder
DB_PATH = Path(__file__).resolve().parent / "cheating_system.db"


def get_connection(timeout: float = 30.0) -> sqlite3.Connection:
    """Get a SQLite connection configured with Row factory and busy timeout."""
    conn = sqlite3.connect(DB_PATH, timeout=timeout)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """
    Initialize database tables and run safe schema migrations.
    Never deletes or drops existing incident records.
    """
    with get_connection() as conn:
        cursor = conn.cursor()

        # 1. Ensure incidents table exists with base schema
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS incidents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                track_id INTEGER,
                event_type TEXT NOT NULL,
                confidence REAL,
                screenshot_path TEXT,
                review_status TEXT NOT NULL DEFAULT 'pending',
                notes TEXT
            )
        """)

        # 2. Check for missing columns in incidents and safely add them
        cursor.execute("PRAGMA table_info(incidents)")
        existing_cols = {row["name"] for row in cursor.fetchall()}

        if "source_video" not in existing_cols:
            cursor.execute("ALTER TABLE incidents ADD COLUMN source_video TEXT")
        if "frame_number" not in existing_cols:
            cursor.execute("ALTER TABLE incidents ADD COLUMN frame_number INTEGER")
        if "job_id" not in existing_cols:
            cursor.execute("ALTER TABLE incidents ADD COLUMN job_id TEXT")

        # 3. Create processing_jobs table to track video analysis history
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS processing_jobs (
                job_id TEXT PRIMARY KEY,
                source_video TEXT NOT NULL,
                output_video TEXT,
                status TEXT NOT NULL DEFAULT 'queued',
                start_time TEXT,
                end_time TEXT,
                total_frames INTEGER DEFAULT 0,
                processed_frames INTEGER DEFAULT 0,
                fps REAL DEFAULT 0,
                incident_count INTEGER DEFAULT 0,
                people_count INTEGER DEFAULT 0,
                error_message TEXT
            )
        """)

        # 4. Create performance indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_incidents_status ON incidents(review_status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_incidents_timestamp ON incidents(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_incidents_track ON incidents(track_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_incidents_job ON incidents(job_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_status ON processing_jobs(status)")

    print(f"Database ready: {DB_PATH}")


def add_incident(
    track_id: Optional[int],
    event_type: str,
    confidence: Optional[float] = None,
    screenshot_path: Optional[str | Path] = None,
    notes: Optional[str] = None,
    source_video: Optional[str] = None,
    frame_number: Optional[int] = None,
    job_id: Optional[str] = None,
) -> int:
    """
    Insert a newly detected suspicious incident.
    Validates confidence score and stores ISO 8601 timestamp.
    """
    timestamp = datetime.now().astimezone().isoformat(timespec="seconds")

    if confidence is not None:
        confidence = float(max(0.0, min(1.0, confidence)))

    with get_connection() as conn:
        cursor = conn.execute("""
            INSERT INTO incidents (
                timestamp,
                track_id,
                event_type,
                confidence,
                screenshot_path,
                review_status,
                notes,
                source_video,
                frame_number,
                job_id
            )
            VALUES (?, ?, ?, ?, ?, 'pending', ?, ?, ?, ?)
        """, (
            timestamp,
            track_id,
            event_type,
            confidence,
            str(screenshot_path) if screenshot_path else None,
            notes,
            source_video,
            frame_number,
            job_id,
        ))

        return cursor.lastrowid


def get_incidents(
    status: Optional[str] = None,
    event_type: Optional[str] = None,
    search: Optional[str] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> List[sqlite3.Row]:
    """
    Retrieve incident records with optional status, event_type, and text search filtering.
    Preserves backward compatibility when called without arguments.
    """
    query = "SELECT * FROM incidents"
    params: List[Any] = []
    conditions: List[str] = []

    if status and status != "all":
        conditions.append("review_status = ?")
        params.append(status)

    if event_type:
        conditions.append("event_type = ?")
        params.append(event_type)

    if search and search.strip():
        term = f"%{search.strip()}%"
        conditions.append(
            "(CAST(id AS TEXT) LIKE ? OR CAST(track_id AS TEXT) LIKE ? OR event_type LIKE ? OR notes LIKE ?)"
        )
        params.extend([term, term, term, term])

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY id DESC"

    if limit is not None:
        query += f" LIMIT {int(limit)}"
        if offset is not None:
            query += f" OFFSET {int(offset)}"

    with get_connection() as conn:
        return conn.execute(query, params).fetchall()


def get_incident(incident_id: int) -> Optional[sqlite3.Row]:
    """Retrieve a single incident by its ID."""
    with get_connection() as conn:
        return conn.execute("""
            SELECT *
            FROM incidents
            WHERE id = ?
        """, (incident_id,)).fetchone()


def update_incident_review(
    incident_id: int,
    review_status: str,
    notes: Optional[str],
) -> bool:
    """Update review status and reviewer notes for an incident."""
    allowed_statuses = {"pending", "reviewed", "dismissed"}

    if review_status not in allowed_statuses:
        raise ValueError(f"Invalid review status: '{review_status}'. Must be one of {allowed_statuses}")

    with get_connection() as conn:
        cursor = conn.execute("""
            UPDATE incidents
            SET review_status = ?,
                notes = ?
            WHERE id = ?
        """, (
            review_status,
            notes.strip() if notes else None,
            incident_id,
        ))

        return cursor.rowcount > 0


def get_stats() -> Dict[str, int]:
    """Calculate aggregate incident statistics for dashboards."""
    with get_connection() as conn:
        total = conn.execute("SELECT COUNT(*) FROM incidents").fetchone()[0]
        pending = conn.execute("SELECT COUNT(*) FROM incidents WHERE review_status = 'pending'").fetchone()[0]
        reviewed = conn.execute("SELECT COUNT(*) FROM incidents WHERE review_status = 'reviewed'").fetchone()[0]
        dismissed = conn.execute("SELECT COUNT(*) FROM incidents WHERE review_status = 'dismissed'").fetchone()[0]

    return {
        "total_incidents": total,
        "pending": pending,
        "reviewed": reviewed,
        "dismissed": dismissed,
    }


def create_job(
    job_id: str,
    source_video: str,
    output_video: Optional[str] = None,
    total_frames: int = 0,
    fps: float = 0.0,
) -> None:
    """Create a new record in processing_jobs."""
    start_time = datetime.now().astimezone().isoformat(timespec="seconds")
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO processing_jobs (
                job_id, source_video, output_video, status,
                start_time, total_frames, processed_frames, fps,
                incident_count, people_count
            )
            VALUES (?, ?, ?, 'processing', ?, ?, 0, ?, 0, 0)
        """, (job_id, source_video, output_video, start_time, total_frames, fps))


def update_job(
    job_id: str,
    status: Optional[str] = None,
    output_video: Optional[str] = None,
    processed_frames: Optional[int] = None,
    incident_count: Optional[int] = None,
    people_count: Optional[int] = None,
    error_message: Optional[str] = None,
) -> bool:
    """Update status and metrics for an existing processing job."""
    updates: List[str] = []
    params: List[Any] = []

    if status is not None:
        updates.append("status = ?")
        params.append(status)
        if status in {"completed", "failed", "cancelled"}:
            updates.append("end_time = ?")
            params.append(datetime.now().astimezone().isoformat(timespec="seconds"))

    if output_video is not None:
        updates.append("output_video = ?")
        params.append(output_video)
    if processed_frames is not None:
        updates.append("processed_frames = ?")
        params.append(processed_frames)
    if incident_count is not None:
        updates.append("incident_count = ?")
        params.append(incident_count)
    if people_count is not None:
        updates.append("people_count = ?")
        params.append(people_count)
    if error_message is not None:
        updates.append("error_message = ?")
        params.append(error_message)

    if not updates:
        return False

    params.append(job_id)
    query = f"UPDATE processing_jobs SET {', '.join(updates)} WHERE job_id = ?"

    with get_connection() as conn:
        cursor = conn.execute(query, params)
        return cursor.rowcount > 0


def get_jobs(limit: int = 50) -> List[sqlite3.Row]:
    """Retrieve list of recent processing jobs."""
    with get_connection() as conn:
        return conn.execute("""
            SELECT * FROM processing_jobs
            ORDER BY rowid DESC
            LIMIT ?
        """, (limit,)).fetchall()


def get_job(job_id: str) -> Optional[sqlite3.Row]:
    """Retrieve details for a specific processing job."""
    with get_connection() as conn:
        return conn.execute("SELECT * FROM processing_jobs WHERE job_id = ?", (job_id,)).fetchone()


if __name__ == "__main__":
    init_db()
