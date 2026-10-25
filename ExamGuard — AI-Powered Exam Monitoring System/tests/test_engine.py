"""
Tests for VideoDetectionEngine (Requirements B, C, D, E, H).
"""

from __future__ import annotations

import threading
from pathlib import Path
import cv2
import numpy as np
import pytest

import database
from config import BASE_DIR
from core.engine import VideoDetectionEngine, VideoProcessingResult


@pytest.fixture
def temp_env(tmp_path, monkeypatch):
    """Setup isolated test environment with temporary database and folders."""
    db_file = tmp_path / "test_engine.db"
    alerts_dir = tmp_path / "alerts"
    outputs_dir = tmp_path / "outputs"
    alerts_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(database, "DB_PATH", db_file)
    database.init_db()

    return {
        "db": db_file,
        "alerts_dir": alerts_dir,
        "outputs_dir": outputs_dir,
        "tmp_path": tmp_path,
    }


def create_synthetic_video(path: Path, frame_count: int = 20, width: int = 320, height: int = 240) -> Path:
    """Create a minimal synthetic video file for test execution."""
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(path), fourcc, 10.0, (width, height))
    for i in range(frame_count):
        frame = np.full((height, width, 3), (i * 10) % 255, dtype=np.uint8)
        # Draw a small rectangle simulating a person
        cv2.rectangle(frame, (50, 50), (120, 180), (100, 100, 100), -1)
        writer.write(frame)
    writer.release()
    return path


def test_missing_model_weights_raises_filenotfound(temp_env):
    """Engine should report missing model file with clear instructions."""
    engine = VideoDetectionEngine(
        model_path=temp_env["tmp_path"] / "nonexistent_model.pt",
        alerts_dir=temp_env["alerts_dir"],
        outputs_dir=temp_env["outputs_dir"],
    )

    with pytest.raises(FileNotFoundError) as exc_info:
        engine.get_model()

    assert "YOLO model weights file not found" in str(exc_info.value)


def test_missing_video_raises_filenotfound(temp_env):
    """Engine should raise FileNotFoundError for missing video file."""
    engine = VideoDetectionEngine(
        model_path=BASE_DIR / "yolov8n.pt",
        alerts_dir=temp_env["alerts_dir"],
        outputs_dir=temp_env["outputs_dir"],
    )

    with pytest.raises(FileNotFoundError):
        engine.process_video(temp_env["tmp_path"] / "missing_video.mp4")


def test_invalid_video_corrupt_file(temp_env):
    """Engine should raise ValueError when an unreadable video is provided."""
    corrupt_video = temp_env["tmp_path"] / "corrupt.mp4"
    corrupt_video.write_text("not a real video file content")

    engine = VideoDetectionEngine(
        model_path=BASE_DIR / "yolov8n.pt",
        alerts_dir=temp_env["alerts_dir"],
        outputs_dir=temp_env["outputs_dir"],
    )

    with pytest.raises(ValueError) as exc:
        engine.process_video(corrupt_video)

    assert "Cannot open video file" in str(exc.value)


def test_synthetic_video_processing(temp_env):
    """Process a real synthetic video end-to-end through the engine."""
    model_path = BASE_DIR / "yolov8n.pt"
    if not model_path.is_file():
        pytest.skip("yolov8n.pt not found for inference test.")

    test_video = temp_env["tmp_path"] / "synthetic.mp4"
    create_synthetic_video(test_video, frame_count=15)

    engine = VideoDetectionEngine(
        model_path=model_path,
        confidence_threshold=0.25,
        cooldown_seconds=3.0,
        alerts_dir=temp_env["alerts_dir"],
        outputs_dir=temp_env["outputs_dir"],
    )

    progress_events = []

    def on_progress(frame_idx, total, fps, inc_count, people_count, preview):
        progress_events.append(frame_idx)

    result = engine.process_video(
        video_path=test_video,
        on_progress=on_progress,
    )

    assert isinstance(result, VideoProcessingResult)
    assert result.status == "completed"
    assert result.processed_frames == 15
    assert result.total_frames == 15
    assert len(progress_events) == 15
    assert result.output_video is not None
    assert Path(result.output_video).is_file()

    # Verify job record in database
    job = database.get_job(result.job_id)
    assert job is not None
    assert job["status"] == "completed"
    assert job["processed_frames"] == 15


def test_safe_cancellation(temp_env):
    """Verify that stopping early via stop_event cleanly exits and marks job as cancelled."""
    model_path = BASE_DIR / "yolov8n.pt"
    if not model_path.is_file():
        pytest.skip("yolov8n.pt not found for cancellation test.")

    test_video = temp_env["tmp_path"] / "long_synthetic.mp4"
    create_synthetic_video(test_video, frame_count=50)

    stop_event = threading.Event()

    engine = VideoDetectionEngine(
        model_path=model_path,
        alerts_dir=temp_env["alerts_dir"],
        outputs_dir=temp_env["outputs_dir"],
    )

    def on_progress(frame_idx, total, fps, inc, ppl, prev):
        if frame_idx >= 5:
            stop_event.set()

    result = engine.process_video(
        video_path=test_video,
        stop_event=stop_event,
        on_progress=on_progress,
    )

    assert result.status == "cancelled"
    assert result.processed_frames < 50
