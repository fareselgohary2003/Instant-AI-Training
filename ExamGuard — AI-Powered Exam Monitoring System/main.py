"""
FastAPI backend for ExamGuard — Cheating Tracking and Alert System.
Maintains full backward compatibility with the React + Vite frontend dashboard
while providing safe multi-directory image serving, job tracking, and search filtering.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from fastapi import BackgroundTasks, FastAPI, File, HTTPException, Query, UploadFile, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field

from config import (
    ALERTS_DIR,
    BASE_DIR,
    DEFAULT_MODEL_PATH,
    INCIDENTS_DIR,
    OUTPUTS_DIR,
    ensure_directories,
    load_config,
)
from core.engine import VideoDetectionEngine, torch_cuda_available
from core.live_proctor import live_proctor_instance
from database import (
    get_connection,
    get_incident as db_get_incident,
    get_incidents as db_get_incidents,
    get_job as db_get_job,
    get_jobs as db_get_jobs,
    get_stats as db_get_stats,
    init_db,
    update_job,
)

UPLOADS_DIR = BASE_DIR / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

# Ensure database and folders are initialized on startup
init_db()
ensure_directories()

app = FastAPI(
    title="ExamGuard API",
    description="Proctoring, AI detection review, and incident tracking API for ExamGuard.",
    version="2.0.0",
)

# Allow React + Vite frontend and local requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ReviewUpdate(BaseModel):
    status: Literal["pending", "reviewed", "dismissed"]
    notes: Optional[str] = Field(default=None, max_length=2000)


class ProcessVideoRequest(BaseModel):
    video_path: str
    confidence_threshold: Optional[float] = Field(default=0.25, ge=0.05, le=1.0)
    cooldown_seconds: Optional[float] = Field(default=5.0, ge=0.5, le=60.0)


@app.get("/")
def home() -> Dict[str, str]:
    """API health and documentation link."""
    return {
        "message": "ExamGuard Tracking & Alert System API is operational.",
        "version": "2.0.0",
        "docs": "/docs",
    }


@app.get("/api/system-info")
def system_info() -> Dict[str, Any]:
    """Provide system environment, device, and model status."""
    cfg = load_config()
    model_file = Path(cfg.get("model_path", DEFAULT_MODEL_PATH))
    cuda_avail = torch_cuda_available()

    return {
        "app": "ExamGuard",
        "version": "2.0.0",
        "model_path": str(model_file),
        "model_exists": model_file.is_file(),
        "cuda_available": cuda_avail,
        "device": "cuda" if cuda_avail else "cpu",
        "stats": db_get_stats(),
    }


@app.get("/api/incidents")
def list_incidents(
    status: Optional[str] = Query(default=None, description="Filter by status: pending, reviewed, dismissed"),
    event_type: Optional[str] = Query(default=None, description="Filter by event type"),
    search: Optional[str] = Query(default=None, description="Search by ID, track_id, notes, or event_type"),
    limit: Optional[int] = Query(default=None, ge=1, le=500),
    offset: Optional[int] = Query(default=None, ge=0),
) -> List[Dict[str, Any]]:
    """
    List recorded incidents with optional status, event_type, and text search filtering.
    Fully compatible with previous parameterless calls.
    """
    incidents = db_get_incidents(
        status=status,
        event_type=event_type,
        search=search,
        limit=limit,
        offset=offset,
    )
    return [dict(inc) for inc in incidents]


@app.get("/api/incidents/{incident_id}")
def get_incident(incident_id: int) -> Dict[str, Any]:
    """Retrieve detailed metadata for a single incident."""
    incident = db_get_incident(incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return dict(incident)


@app.get("/api/incidents/{incident_id}/image")
def get_incident_image(incident_id: int):
    """
    Serve evidence screenshot securely for an incident.
    Supports both legacy incidents/ and alerts/screenshots/ directories
    while strictly preventing path traversal attacks.
    """
    incident = db_get_incident(incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")

    raw_path_str = incident["screenshot_path"]
    if not raw_path_str:
        raise HTTPException(status_code=404, detail="Incident has no image")

    image_path = Path(raw_path_str)
    if not image_path.is_absolute():
        image_path = (BASE_DIR / image_path).resolve()
    else:
        image_path = image_path.resolve()

    # Security check: must reside inside INCIDENTS_DIR or ALERTS_DIR
    resolved_incidents_dir = INCIDENTS_DIR.resolve()
    resolved_alerts_dir = ALERTS_DIR.resolve()

    is_safe = (
        image_path.is_relative_to(resolved_incidents_dir)
        or image_path.is_relative_to(resolved_alerts_dir)
    )

    if not is_safe:
        raise HTTPException(status_code=403, detail="Invalid image path (access denied)")

    if not image_path.is_file():
        raise HTTPException(status_code=404, detail="Image file not found on disk")

    media_type = "image/png" if image_path.suffix.lower() == ".png" else "image/jpeg"
    return FileResponse(image_path, media_type=media_type)


@app.patch("/api/incidents/{incident_id}/status")
def update_incident_status(
    incident_id: int,
    status: Literal["pending", "reviewed", "dismissed"],
) -> Dict[str, Any]:
    """Quick update of incident review status."""
    with get_connection() as conn:
        cursor = conn.execute(
            "UPDATE incidents SET review_status = ? WHERE id = ?",
            (status, incident_id),
        )
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Incident not found")

    return {
        "incident_id": incident_id,
        "review_status": status,
        "message": "Incident status updated successfully",
    }


@app.patch("/api/incidents/{incident_id}/review")
def update_incident_review(
    incident_id: int,
    review: ReviewUpdate,
) -> Dict[str, Any]:
    """Update reviewer decision and notes for an incident."""
    with get_connection() as conn:
        cursor = conn.execute(
            """
            UPDATE incidents
            SET review_status = ?,
                notes = ?
            WHERE id = ?
            """,
            (
                review.status,
                review.notes.strip() if review.notes else None,
                incident_id,
            ),
        )

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Incident not found")

        updated_incident = conn.execute(
            "SELECT * FROM incidents WHERE id = ?",
            (incident_id,),
        ).fetchone()

    return {
        "message": "Incident review saved successfully",
        "incident": dict(updated_incident),
    }


@app.get("/api/stats")
def get_stats() -> Dict[str, int]:
    """Return dashboard summary stats."""
    return db_get_stats()


@app.get("/api/jobs")
def list_jobs(limit: int = Query(default=50, ge=1, le=100)) -> List[Dict[str, Any]]:
    """List recent video processing jobs."""
    jobs = db_get_jobs(limit=limit)
    return [dict(job) for job in jobs]


@app.get("/api/jobs/{job_id}")
def get_job_detail(job_id: str) -> Dict[str, Any]:
    """Retrieve details for a specific video processing job."""
    job = db_get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return dict(job)


# Active background job tracking state
active_job_state: Dict[str, Any] = {
    "is_running": False,
    "job_id": None,
    "source_video": None,
    "output_video": None,
    "processed_frames": 0,
    "total_frames": 0,
    "fps": 0.0,
    "incident_count": 0,
    "people_count": 0,
    "status": "idle",
    "error_message": None,
}

_global_engine: Optional[VideoDetectionEngine] = None


@app.get("/api/active-job")
def get_active_job() -> Dict[str, Any]:
    """Return live status and progress of the active or most recent video processing job."""
    return dict(active_job_state)


@app.get("/api/sample-videos")
def list_sample_videos() -> List[Dict[str, Any]]:
    """Scan and return available exam video files in project root, Downloads, and uploads."""
    candidates = []
    search_dirs = [BASE_DIR, UPLOADS_DIR, BASE_DIR.parent]

    seen = set()
    for s_dir in search_dirs:
        if not s_dir.is_dir():
            continue
        for ext in ("*.mp4", "*.avi", "*.mov"):
            for vfile in s_dir.glob(ext):
                if vfile.name.startswith("processed_"):
                    continue
                if vfile.name in seen:
                    continue
                seen.add(vfile.name)
                try:
                    size_mb = round(vfile.stat().st_size / (1024 * 1024), 2)
                except Exception:
                    size_mb = 0.0
                candidates.append({
                    "filename": vfile.name,
                    "path": str(vfile.resolve()),
                    "size_mb": size_mb,
                    "is_sample": "WhatsApp" in vfile.name or s_dir == BASE_DIR,
                })

    return candidates


@app.post("/api/upload-video")
async def upload_video_file(file: UploadFile = File(...)) -> Dict[str, Any]:
    """Upload a new exam video file for AI proctoring."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    safe_name = Path(file.filename).name.replace(" ", "_")
    target_path = UPLOADS_DIR / safe_name

    with open(target_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    size_mb = round(target_path.stat().st_size / (1024 * 1024), 2)

    return {
        "message": "Video uploaded successfully",
        "filename": safe_name,
        "path": str(target_path),
        "size_mb": size_mb,
    }


def _run_engine_job(engine: VideoDetectionEngine, video_path: Path, job_id: str):
    global active_job_state
    try:
        def on_prog(frame_idx, total, fps, inc, ppl, prev):
            active_job_state["processed_frames"] = frame_idx
            active_job_state["total_frames"] = total
            active_job_state["fps"] = round(fps, 1)
            active_job_state["incident_count"] = inc
            active_job_state["people_count"] = ppl

            if frame_idx % 10 == 0 or frame_idx == total:
                try:
                    update_job(
                        job_id=job_id,
                        processed_frames=frame_idx,
                        incident_count=inc,
                        people_count=ppl,
                    )
                except Exception:
                    pass

        res = engine.process_video(
            video_path=video_path,
            on_progress=on_prog,
            job_id=job_id,
        )

        active_job_state["status"] = res.status
        active_job_state["output_video"] = res.output_video
        active_job_state["incident_count"] = res.incident_count
        active_job_state["processed_frames"] = res.processed_frames
        active_job_state["total_frames"] = res.total_frames
    except Exception as e:
        active_job_state["status"] = "failed"
        active_job_state["error_message"] = str(e)
    finally:
        active_job_state["is_running"] = False


@app.post("/api/process-video")
def trigger_video_processing(
    req: ProcessVideoRequest,
    background_tasks: BackgroundTasks,
) -> Dict[str, Any]:
    """Trigger video processing as an asynchronous background job with live progress."""
    global active_job_state, _global_engine

    video_path = Path(req.video_path)
    if not video_path.is_absolute():
        video_path = (BASE_DIR / video_path).resolve()
        if not video_path.is_file():
            video_path = (UPLOADS_DIR / req.video_path).resolve()
        if not video_path.is_file():
            video_path = (BASE_DIR.parent / req.video_path).resolve()

    if not video_path.is_file():
        raise HTTPException(status_code=400, detail=f"Video file not found: {req.video_path}")

    if active_job_state["is_running"]:
        raise HTTPException(status_code=409, detail="A video processing job is already running.")

    job_id = f"job_web_{video_path.stem[:12]}_{uuid_now()}"

    _global_engine = VideoDetectionEngine(
        confidence_threshold=req.confidence_threshold or 0.15,
        cooldown_seconds=req.cooldown_seconds or 4.0,
    )

    active_job_state = {
        "is_running": True,
        "job_id": job_id,
        "source_video": video_path.name,
        "output_video": None,
        "processed_frames": 0,
        "total_frames": 0,
        "fps": 0.0,
        "incident_count": 0,
        "people_count": 0,
        "status": "processing",
        "error_message": None,
    }

    background_tasks.add_task(_run_engine_job, _global_engine, video_path, job_id)

    return {
        "message": "Video processing started successfully",
        "job_id": job_id,
        "video_path": str(video_path),
        "status": "processing",
    }


def uuid_now() -> str:
    from datetime import datetime
    return datetime.now().strftime("%Y%m%d_%H%M%S")


@app.get("/api/videos/{filename}")
def stream_video(filename: str):
    """Serve processed exam video for HTML5 playback in the dashboard."""
    # Check outputs directory first
    target = OUTPUTS_DIR / filename
    if not target.is_file():
        target = BASE_DIR / filename
    if not target.is_file():
        target = UPLOADS_DIR / filename

    if not target.is_file():
        raise HTTPException(status_code=404, detail="Video file not found")

    return FileResponse(target, media_type="video/mp4")


class LiveStreamStartRequest(BaseModel):
    camera_index: Optional[int] = Field(default=0, ge=0, le=10)
    confidence_threshold: Optional[float] = Field(default=0.10, ge=0.05, le=1.0)
    cooldown_seconds: Optional[float] = Field(default=1.2, ge=0.5, le=60.0)


@app.post("/api/live-stream/start")
def start_live_stream(req: Optional[LiveStreamStartRequest] = None):
    """Start real-time proctoring from laptop webcam with live green/red tracking."""
    camera_idx = req.camera_index if req else 0
    conf = req.confidence_threshold if req else 0.10
    cooldown = req.cooldown_seconds if req else 1.2
    res = live_proctor_instance.start(
        camera_index=camera_idx,
        conf_threshold=conf,
        cooldown_seconds=cooldown,
    )
    return res


@app.post("/api/live-stream/stop")
def stop_live_stream():
    """Stop real-time webcam proctoring session."""
    return live_proctor_instance.stop()


@app.get("/api/live-stream/status")
def get_live_stream_status():
    """Retrieve live camera telemetry, FPS, and incident count."""
    return live_proctor_instance.get_status()


@app.get("/api/live-stream/feed")
def live_stream_feed():
    """Stream live annotated webcam feed via MJPEG multipart stream."""
    return StreamingResponse(
        live_proctor_instance.generate_mjpeg_stream(),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


@app.get("/api/live-stream/frame")
def live_stream_single_frame():
    """Get the latest processed frame snapshot as JPEG."""
    jpeg = live_proctor_instance.get_latest_frame()
    if jpeg is None:
        raise HTTPException(status_code=404, detail="No live camera frame currently available")
    return Response(content=jpeg, media_type="image/jpeg")


