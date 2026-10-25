"""
Video Processing view for ExamGuard PySide6 Application.
Integrates native file dialog, codec validation, background QThread execution,
live metrics display, real-time video frame preview, and output player launcher.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import cv2
import numpy as np
from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtGui import QColor, QDesktopServices, QImage, QPixmap
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from config import load_config
from core.engine import VideoDetectionEngine, VideoProcessingResult
from desktop_qt.theme import (
    COLOR_BORDER,
    COLOR_DANGER,
    COLOR_PRIMARY,
    COLOR_SUCCESS,
    COLOR_SURFACE,
    COLOR_SURFACE_ALT,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    COLOR_WARNING,
)
from desktop_qt.worker import VideoProcessingWorker


class ProcessingView(QWidget):
    """
    Video processing monitor and controller.
    """
    incident_logged = Signal(dict)
    review_requested = Signal(int)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.selected_video_path: Optional[Path] = None
        self.video_metadata: Dict[str, Any] = {}
        self.worker: Optional[VideoProcessingWorker] = None
        self.last_result: Optional[VideoProcessingResult] = None

        self._build_ui()

    def _build_ui(self) -> None:
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        scroll.setWidget(content)

        layout = QVBoxLayout(content)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(18)

        # Header
        header = QWidget()
        h_layout = QVBoxLayout(header)
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(2)

        eyebrow = QLabel("EXAMGUARD / VIDEO ANALYSIS PIPELINE")
        eyebrow.setStyleSheet(f"font-size: 11px; font-weight: bold; color: {COLOR_PRIMARY};")
        title = QLabel("Upload & Process Examination Video")
        title.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {COLOR_TEXT_PRIMARY};")
        subtitle = QLabel("Execute real-time multi-student ByteTrack tracking and cell phone detection.")
        subtitle.setStyleSheet(f"font-size: 12px; color: {COLOR_TEXT_MUTED};")

        h_layout.addWidget(eyebrow)
        h_layout.addWidget(title)
        h_layout.addWidget(subtitle)
        layout.addWidget(header)

        # 1. Video Selection Card
        sel_card = QFrame()
        sel_card.setProperty("class", "card")
        sc_layout = QVBoxLayout(sel_card)
        sc_layout.setContentsMargins(20, 18, 20, 18)
        sc_layout.setSpacing(12)

        sc_title = QLabel("Video File Selection & Codec Verification")
        sc_title.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {COLOR_TEXT_PRIMARY};")
        sc_desc = QLabel("Supported containers: MP4, AVI, MOV. Codec accessibility is validated before inference commences.")
        sc_desc.setStyleSheet(f"font-size: 11px; color: {COLOR_TEXT_MUTED};")
        sc_layout.addWidget(sc_title)
        sc_layout.addWidget(sc_desc)

        action_row = QWidget()
        ar_layout = QHBoxLayout(action_row)
        ar_layout.setContentsMargins(0, 0, 0, 0)
        ar_layout.setSpacing(10)

        self.select_btn = QPushButton("📁  Select Exam Video...")
        self.select_btn.setProperty("class", "primary")
        self.select_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.select_btn.clicked.connect(self._choose_video_file)
        ar_layout.addWidget(self.select_btn)

        self.start_btn = QPushButton("▶  Start AI Processing")
        self.start_btn.setProperty("class", "success")
        self.start_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.start_btn.setEnabled(False)
        self.start_btn.clicked.connect(self._start_processing)
        ar_layout.addWidget(self.start_btn)

        self.stop_btn = QPushButton("⏹  Cancel / Stop")
        self.stop_btn.setProperty("class", "danger")
        self.stop_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self._stop_processing)
        ar_layout.addWidget(self.stop_btn)

        ar_layout.addStretch()
        sc_layout.addWidget(action_row)

        self.meta_label = QLabel("No video selected yet. Click 'Select Exam Video...' to begin.")
        self.meta_label.setStyleSheet(f"background-color: {COLOR_SURFACE_ALT}; border: 1px solid {COLOR_BORDER}; border-radius: 6px; padding: 10px; color: {COLOR_TEXT_MUTED}; font-size: 12px;")
        sc_layout.addWidget(self.meta_label)

        layout.addWidget(sel_card)

        # 2. Live Monitoring & Preview Card
        mon_card = QFrame()
        mon_card.setProperty("class", "card")
        mc_layout = QVBoxLayout(mon_card)
        mc_layout.setContentsMargins(20, 18, 20, 18)
        mc_layout.setSpacing(14)

        mc_top = QWidget()
        mct_layout = QHBoxLayout(mc_top)
        mct_layout.setContentsMargins(0, 0, 0, 0)

        mc_title = QLabel("Live Detection & Tracking Monitor")
        mc_title.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {COLOR_TEXT_PRIMARY};")
        mct_layout.addWidget(mc_title)

        mct_layout.addStretch()

        self.status_badge = QLabel("IDLE")
        self.status_badge.setStyleSheet(f"background-color: {COLOR_SURFACE_ALT}; border: 1px solid {COLOR_BORDER}; border-radius: 4px; padding: 4px 10px; font-weight: bold; font-size: 11px; color: {COLOR_TEXT_MUTED};")
        mct_layout.addWidget(self.status_badge)
        mc_layout.addWidget(mc_top)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        mc_layout.addWidget(self.progress_bar)

        # Metrics Badges Grid
        metrics_grid = QWidget()
        mg_layout = QGridLayout(metrics_grid)
        mg_layout.setContentsMargins(0, 0, 0, 0)
        mg_layout.setSpacing(10)

        self.metric_frames = self._create_metric_pill("Progress", "0 / 0 (0%)")
        self.metric_speed = self._create_metric_pill("Processing Speed", "0.0 FPS")
        self.metric_people = self._create_metric_pill("Students Tracked", "0")
        self.metric_incidents = self._create_metric_pill("Incidents Flagged", "0")

        mg_layout.addWidget(self.metric_frames[0], 0, 0)
        mg_layout.addWidget(self.metric_speed[0], 0, 1)
        mg_layout.addWidget(self.metric_people[0], 0, 2)
        mg_layout.addWidget(self.metric_incidents[0], 0, 3)
        mc_layout.addWidget(metrics_grid)

        # Video Preview Display Label
        preview_box = QFrame()
        preview_box.setStyleSheet(f"background-color: #050811; border: 1px solid {COLOR_BORDER}; border-radius: 6px;")
        pb_layout = QVBoxLayout(preview_box)
        pb_layout.setContentsMargins(4, 4, 4, 4)

        self.preview_label = QLabel("Video preview will appear here during processing")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setMinimumHeight(320)
        self.preview_label.setStyleSheet("color: #475569; font-size: 13px;")
        pb_layout.addWidget(self.preview_label)
        mc_layout.addWidget(preview_box)

        layout.addWidget(mon_card)

        # 3. Summary Card (Hidden initially)
        self.summary_card = QFrame()
        self.summary_card.setProperty("class", "card")
        self.summary_card.setStyleSheet(f"background-color: #064E3B; border: 1px solid {COLOR_SUCCESS}; border-radius: 8px;")
        sum_layout = QVBoxLayout(self.summary_card)
        sum_layout.setContentsMargins(20, 18, 20, 18)
        sum_layout.setSpacing(10)

        self.summary_title = QLabel("✓  Processing Finished Successfully")
        self.summary_title.setStyleSheet("font-size: 15px; font-weight: bold; color: #6EE7B7;")
        sum_layout.addWidget(self.summary_title)

        self.summary_text = QLabel("")
        self.summary_text.setStyleSheet("color: #ECFDF5; font-size: 12px; line-height: 1.5;")
        sum_layout.addWidget(self.summary_text)

        sum_actions = QWidget()
        sa_layout = QHBoxLayout(sum_actions)
        sa_layout.setContentsMargins(0, 0, 0, 0)
        sa_layout.setSpacing(10)

        self.open_video_btn = QPushButton("▶  Play Output Video")
        self.open_video_btn.setProperty("class", "primary")
        self.open_video_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.open_video_btn.clicked.connect(self._open_output_video)
        sa_layout.addWidget(self.open_video_btn)

        self.open_folder_btn = QPushButton("📂  Open Output Folder")
        self.open_folder_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.open_folder_btn.clicked.connect(self._open_output_folder)
        sa_layout.addWidget(self.open_folder_btn)

        sa_layout.addStretch()
        sum_layout.addWidget(sum_actions)

        self.summary_card.hide()
        layout.addWidget(self.summary_card)

        # Outer layout
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def _create_metric_pill(self, label: str, init_val: str) -> tuple[QFrame, QLabel]:
        card = QFrame()
        card.setStyleSheet(f"background-color: {COLOR_SURFACE_ALT}; border: 1px solid {COLOR_BORDER}; border-radius: 6px;")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(2)

        lbl = QLabel(label)
        lbl.setStyleSheet(f"font-size: 10px; font-weight: bold; color: {COLOR_TEXT_MUTED};")
        val = QLabel(init_val)
        val.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {COLOR_TEXT_PRIMARY};")
        layout.addWidget(lbl)
        layout.addWidget(val)
        return card, val

    def _choose_video_file(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Exam Video",
            "",
            "Video Files (*.mp4 *.avi *.mov *.mkv);;All Files (*.*)",
        )
        if not file_path:
            return

        path = Path(file_path).resolve()
        cap = cv2.VideoCapture(str(path))
        if not cap.isOpened():
            QMessageBox.critical(
                self,
                "Unsupported Video",
                f"Cannot decode video '{path.name}'. Ensure a supported codec (H.264/MP4) is installed.",
            )
            return

        frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()

        size_mb = path.stat().st_size / (1024 * 1024)
        duration_sec = frames / fps if fps > 0 else 0

        self.selected_video_path = path
        self.video_metadata = {
            "name": path.name,
            "path": str(path),
            "size_mb": size_mb,
            "frames": frames,
            "fps": fps,
            "resolution": f"{w}x{h}",
            "duration": duration_sec,
        }

        self.meta_label.setText(
            f"Selected: {path.name} ({size_mb:.1f} MB) | Resolution: {w}x{h} | Frames: {frames} | FPS: {fps:.1f} | Duration: {duration_sec:.1f}s"
        )
        self.meta_label.setStyleSheet(f"background-color: {COLOR_SURFACE_ALT}; border: 1px solid {COLOR_PRIMARY}; border-radius: 6px; padding: 10px; color: {COLOR_TEXT_PRIMARY}; font-size: 12px;")
        self.start_btn.setEnabled(True)
        self.status_badge.setText("READY TO PROCESS")
        self.status_badge.setStyleSheet(f"background-color: #1E3A8A; border: 1px solid {COLOR_PRIMARY}; border-radius: 4px; padding: 4px 10px; font-weight: bold; font-size: 11px; color: #93C5FD;")
        self.summary_card.hide()

    def _start_processing(self) -> None:
        if not self.selected_video_path:
            return

        config = load_config()
        engine = VideoDetectionEngine(
            model_path=config.get("model_path"),
            confidence_threshold=config.get("confidence_threshold", 0.25),
            cooldown_seconds=config.get("cooldown_seconds", 5.0),
            proximity_threshold_ratio=config.get("proximity_threshold_ratio", 0.6),
            device=config.get("device", "cpu"),
            alerts_dir=Path(config.get("alerts_dir")),
            outputs_dir=Path(config.get("outputs_dir")),
        )

        self.select_btn.setEnabled(False)
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.summary_card.hide()

        self.status_badge.setText("PROCESSING...")
        self.status_badge.setStyleSheet(f"background-color: #78350F; border: 1px solid {COLOR_WARNING}; border-radius: 4px; padding: 4px 10px; font-weight: bold; font-size: 11px; color: #FCD34D;")

        total = self.video_metadata.get("frames", 100)
        self.progress_bar.setRange(0, total)
        self.progress_bar.setValue(0)

        # Create and launch background QThread worker
        self.worker = VideoProcessingWorker(engine, self.selected_video_path, self)
        self.worker.progress_updated.connect(self._on_worker_progress)
        self.worker.incident_detected.connect(self._on_worker_incident)
        self.worker.processing_finished.connect(self._on_worker_finished)
        self.worker.processing_error.connect(self._on_worker_error)
        self.worker.start()

    def _stop_processing(self) -> None:
        reply = QMessageBox.question(
            self,
            "Confirm Cancellation",
            "Are you sure you want to stop the video processing job early?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes and self.worker:
            self.worker.stop()
            self.status_badge.setText("CANCELLING...")
            self.status_badge.setStyleSheet(f"background-color: #7F1D1D; border: 1px solid {COLOR_DANGER}; border-radius: 4px; padding: 4px 10px; font-weight: bold; font-size: 11px; color: #FCA5A5;")

    def _on_worker_progress(
        self,
        frame_idx: int,
        total_frames: int,
        fps: float,
        incident_count: int,
        people_count: int,
        preview_frame: Optional[np.ndarray],
    ) -> None:
        pct = (frame_idx / total_frames * 100) if total_frames > 0 else 0
        self.progress_bar.setValue(frame_idx)
        self.metric_frames[1].setText(f"{frame_idx} / {total_frames} ({pct:.1f}%)")
        self.metric_speed[1].setText(f"{fps:.1f} FPS")
        self.metric_people[1].setText(str(people_count))
        self.metric_incidents[1].setText(str(incident_count))

        if preview_frame is not None:
            self._render_frame_preview(preview_frame)

    def _render_frame_preview(self, bgr_frame: np.ndarray) -> None:
        lbl_w = max(100, self.preview_label.width())
        lbl_h = max(100, self.preview_label.height())

        h, w = bgr_frame.shape[:2]
        scale = min(lbl_w / w, lbl_h / h)
        new_w, new_h = max(1, int(w * scale)), max(1, int(h * scale))

        rgb = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)
        resized = cv2.resize(rgb, (new_w, new_h), interpolation=cv2.INTER_AREA)

        q_img = QImage(
            resized.data,
            new_w,
            new_h,
            3 * new_w,
            QImage.Format.Format_RGB888,
        )
        self.preview_label.setPixmap(QPixmap.fromImage(q_img))

    def _on_worker_incident(self, incident_data: Dict[str, Any]) -> None:
        self.incident_logged.emit(incident_data)

    def _on_worker_finished(self, result: VideoProcessingResult) -> None:
        self.last_result = result
        self.select_btn.setEnabled(True)
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

        if result.status == "completed":
            self.status_badge.setText("COMPLETED")
            self.status_badge.setStyleSheet(f"background-color: #064E3B; border: 1px solid {COLOR_SUCCESS}; border-radius: 4px; padding: 4px 10px; font-weight: bold; font-size: 11px; color: #6EE7B7;")
            self.summary_card.setStyleSheet("background-color: #064E3B; border: 1px solid #10B981; border-radius: 8px;")
            self.summary_title.setText("✓  Processing Finished Successfully")
            self.summary_title.setStyleSheet("font-size: 15px; font-weight: bold; color: #6EE7B7;")
        elif result.status == "cancelled":
            self.status_badge.setText("CANCELLED")
            self.status_badge.setStyleSheet(f"background-color: #78350F; border: 1px solid {COLOR_WARNING}; border-radius: 4px; padding: 4px 10px; font-weight: bold; font-size: 11px; color: #FCD34D;")
            self.summary_card.setStyleSheet("background-color: #78350F; border: 1px solid #F59E0B; border-radius: 8px;")
            self.summary_title.setText("⚠  Processing Cancelled by User")
            self.summary_title.setStyleSheet("font-size: 15px; font-weight: bold; color: #FDE68A;")
        else:
            self.status_badge.setText("FAILED")
            self.status_badge.setStyleSheet(f"background-color: #7F1D1D; border: 1px solid {COLOR_DANGER}; border-radius: 4px; padding: 4px 10px; font-weight: bold; font-size: 11px; color: #FCA5A5;")
            self.summary_card.setStyleSheet("background-color: #7F1D1D; border: 1px solid #EF4444; border-radius: 8px;")
            self.summary_title.setText("✕  Processing Job Failed")
            self.summary_title.setStyleSheet("font-size: 15px; font-weight: bold; color: #FCA5A5;")

        summary_msg = (
            f"• Source Video: {result.source_video}\n"
            f"• Frames Processed: {result.processed_frames} of {result.total_frames} (Average Speed: {result.fps:.1f} FPS)\n"
            f"• Students Tracked: {result.people_count}\n"
            f"• Incidents Requiring Review: {result.incident_count}\n"
            f"• Verified Evidence Screenshots Saved: {result.screenshots_saved}\n"
            f"• Output Video: {result.output_video or 'None'}"
        )
        if result.error_message:
            summary_msg += f"\n• Error Message: {result.error_message}"

        self.summary_text.setText(summary_msg)
        self.summary_card.show()

    def _on_worker_error(self, err_msg: str) -> None:
        self.select_btn.setEnabled(True)
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_badge.setText("ERROR")
        QMessageBox.critical(self, "Processing Error", f"Video processing encountered an error:\n\n{err_msg}")

    def _open_output_video(self) -> None:
        if self.last_result and self.last_result.output_video and Path(self.last_result.output_video).is_file():
            QDesktopServices.openUrl(QUrl.fromLocalFile(self.last_result.output_video))
        else:
            QMessageBox.information(self, "Output Video", "Output video file does not exist or was not generated.")

    def _open_output_folder(self) -> None:
        if self.last_result and self.last_result.output_video:
            folder = Path(self.last_result.output_video).parent
            if folder.is_dir():
                QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder)))
