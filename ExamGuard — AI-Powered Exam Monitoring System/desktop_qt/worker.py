"""
Qt QThread Worker for video processing and AI inference.
Safely communicates video progress and detection events to the Qt UI
via thread-safe Qt Signals and Slots.
"""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np
from PySide6.QtCore import QThread, Signal

from core.engine import VideoDetectionEngine, VideoProcessingResult


class VideoProcessingWorker(QThread):
    """
    Background worker thread running YOLO and ByteTrack video inference.
    """
    # Signals emitted to UI main thread
    progress_updated = Signal(int, int, float, int, int, object)  # frame, total, fps, incidents, people, frame_np
    incident_detected = Signal(dict)                              # incident data dict
    processing_finished = Signal(object)                          # VideoProcessingResult
    processing_error = Signal(str)                                # error message string

    def __init__(
        self,
        engine: VideoDetectionEngine,
        video_path: str | Path,
        parent: Optional[Any] = None,
    ):
        super().__init__(parent)
        self.engine = engine
        self.video_path = Path(video_path)
        self.stop_event = threading.Event()

    def run(self) -> None:
        """Execute video processing inside the background thread."""
        try:
            result = self.engine.process_video(
                video_path=self.video_path,
                stop_event=self.stop_event,
                on_progress=self._on_engine_progress,
                on_incident=self._on_engine_incident,
            )
            self.processing_finished.emit(result)
        except Exception as e:
            self.processing_error.emit(str(e))

    def stop(self) -> None:
        """Signal the engine to halt processing safely."""
        self.stop_event.set()

    def _on_engine_progress(
        self,
        frame_idx: int,
        total_frames: int,
        fps: float,
        incident_count: int,
        people_count: int,
        preview_frame: Optional[np.ndarray],
    ) -> None:
        """Forward engine progress to Qt Signal."""
        self.progress_updated.emit(
            frame_idx,
            total_frames,
            fps,
            incident_count,
            people_count,
            preview_frame,
        )

    def _on_engine_incident(self, incident_data: Dict[str, Any]) -> None:
        """Forward incident notification to Qt Signal."""
        self.incident_detected.emit(incident_data)
