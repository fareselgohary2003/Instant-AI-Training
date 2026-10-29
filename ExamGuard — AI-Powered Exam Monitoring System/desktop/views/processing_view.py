"""
Video Processing view for ExamGuard.
Handles video file selection, codec validation, background AI execution,
live progress metrics, real-time visual frame preview, and completion reporting.
"""

from __future__ import annotations

import os
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Any, Callable, Dict, Optional

import cv2
import numpy as np
from PIL import Image, ImageTk

from config import load_config
from core.engine import VideoDetectionEngine, VideoProcessingResult
from desktop.theme import (
    COLOR_CARD_BG,
    COLOR_CARD_BORDER,
    COLOR_CONTENT_BG,
    COLOR_DANGER,
    COLOR_PRIMARY,
    COLOR_SUCCESS,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    COLOR_WARNING,
    FONT_BODY,
    FONT_BODY_BOLD,
    FONT_HEADING,
    FONT_MONO,
    FONT_SMALL,
    FONT_SUBHEADING,
    FONT_TITLE,
)


class ProcessingView(tk.Frame):
    """
    Video upload and processing interface with live tracking metrics.
    """

    def __init__(
        self,
        parent: tk.Widget,
        on_incident_logged: Optional[Callable[[Dict[str, Any]], None]] = None,
        on_navigate_review: Optional[Callable[[int], None]] = None,
        **kwargs,
    ):
        super().__init__(parent, bg=COLOR_CONTENT_BG, **kwargs)
        self.on_incident_logged = on_incident_logged
        self.on_navigate_review = on_navigate_review

        self.selected_video_path: Optional[Path] = None
        self.video_metadata: Dict[str, Any] = {}
        self.stop_event = threading.Event()
        self.worker_thread: Optional[threading.Thread] = None
        self.engine: Optional[VideoDetectionEngine] = None
        self.last_result: Optional[VideoProcessingResult] = None
        self._current_photo: Optional[ImageTk.PhotoImage] = None

        self._build_ui()

    def _build_ui(self) -> None:
        # Scrollable Canvas container for responsive layout
        canvas = tk.Canvas(self, bg=COLOR_CONTENT_BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.scroll_content = tk.Frame(canvas, bg=COLOR_CONTENT_BG)

        self.scroll_content.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas_window = canvas.create_window((0, 0), window=self.scroll_content, anchor="nw")
        canvas.bind(
            "<Configure>",
            lambda e: canvas.itemconfig(canvas_window, width=e.width),
        )
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Top Header
        self._build_header()

        # Upload Card
        self._build_upload_card()

        # Live Processing & Preview Card
        self._build_live_monitor_card()

        # Summary Result Card (initially hidden)
        self._build_summary_card()

    def _build_header(self) -> None:
        header = tk.Frame(self.scroll_content, bg=COLOR_CONTENT_BG)
        header.pack(fill="x", padx=24, pady=(20, 16))

        eyebrow = tk.Label(
            header,
            text="EXAMGUARD / VIDEO ANALYSIS",
            font=FONT_SMALL,
            fg=COLOR_PRIMARY,
            bg=COLOR_CONTENT_BG,
        )
        eyebrow.pack(anchor="w")

        title = tk.Label(
            header,
            text="Upload & Process Exam Footage",
            font=FONT_TITLE,
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_CONTENT_BG,
        )
        title.pack(anchor="w")

        subtitle = tk.Label(
            header,
            text="Run real-time person tracking and phone detection to flag potential academic misconduct for review.",
            font=FONT_BODY,
            fg=COLOR_TEXT_MUTED,
            bg=COLOR_CONTENT_BG,
        )
        subtitle.pack(anchor="w")

    def _build_upload_card(self) -> None:
        card = tk.Frame(
            self.scroll_content,
            bg=COLOR_CARD_BG,
            highlightthickness=1,
            highlightbackground=COLOR_CARD_BORDER,
            padx=20,
            pady=18,
        )
        card.pack(fill="x", padx=24, pady=(0, 16))

        card_title = tk.Label(
            card,
            text="Video File Selection",
            font=FONT_HEADING,
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_CARD_BG,
        )
        card_title.pack(anchor="w")

        card_desc = tk.Label(
            card,
            text="Select an exam recording (MP4, AVI, or MOV). Video codecs will be verified before processing starts.",
            font=FONT_SMALL,
            fg=COLOR_TEXT_MUTED,
            bg=COLOR_CARD_BG,
        )
        card_desc.pack(anchor="w", pady=(2, 12))

        # Action row
        action_row = tk.Frame(card, bg=COLOR_CARD_BG)
        action_row.pack(fill="x")

        self.select_btn = tk.Button(
            action_row,
            text="📁 Select Exam Video...",
            font=FONT_BODY_BOLD,
            bg="#EFF6FF",
            fg=COLOR_PRIMARY,
            activebackground="#DBEAFE",
            activeforeground=COLOR_PRIMARY,
            relief="flat",
            padx=14,
            pady=8,
            cursor="hand2",
            command=self._choose_video_file,
        )
        self.select_btn.pack(side="left")

        self.start_btn = tk.Button(
            action_row,
            text="▶ Start AI Processing",
            font=FONT_BODY_BOLD,
            bg=COLOR_SUCCESS,
            fg="#FFFFFF",
            activebackground="#15803D",
            activeforeground="#FFFFFF",
            relief="flat",
            padx=16,
            pady=8,
            cursor="hand2",
            state="disabled",
            command=self._start_processing,
        )
        self.start_btn.pack(side="left", padx=10)

        self.stop_btn = tk.Button(
            action_row,
            text="⏹ Cancel / Stop",
            font=FONT_BODY_BOLD,
            bg=COLOR_DANGER,
            fg="#FFFFFF",
            activebackground="#B91C1C",
            activeforeground="#FFFFFF",
            relief="flat",
            padx=14,
            pady=8,
            cursor="hand2",
            state="disabled",
            command=self._stop_processing,
        )
        self.stop_btn.pack(side="left")

        # Metadata display area
        self.meta_frame = tk.Frame(card, bg="#F8FAFC", padx=12, pady=10)
        self.meta_frame.pack(fill="x", pady=(14, 0))

        self.meta_label = tk.Label(
            self.meta_frame,
            text="No video selected yet. Click 'Select Exam Video' to begin.",
            font=FONT_BODY,
            fg=COLOR_TEXT_MUTED,
            bg="#F8FAFC",
            anchor="w",
        )
        self.meta_label.pack(fill="x")

    def _build_live_monitor_card(self) -> None:
        self.monitor_card = tk.Frame(
            self.scroll_content,
            bg=COLOR_CARD_BG,
            highlightthickness=1,
            highlightbackground=COLOR_CARD_BORDER,
            padx=20,
            pady=18,
        )
        self.monitor_card.pack(fill="x", padx=24, pady=(0, 16))

        top_row = tk.Frame(self.monitor_card, bg=COLOR_CARD_BG)
        top_row.pack(fill="x", pady=(0, 10))

        self.status_title = tk.Label(
            top_row,
            text="Live Processing Monitor",
            font=FONT_HEADING,
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_CARD_BG,
        )
        self.status_title.pack(side="left")

        self.status_badge = tk.Label(
            top_row,
            text="IDLE",
            font=("Segoe UI", 9, "bold"),
            fg=COLOR_TEXT_MUTED,
            bg="#F1F5F9",
            padx=8,
            pady=3,
        )
        self.status_badge.pack(side="right")

        # Progress bar
        self.progress_bar = ttk.Progressbar(
            self.monitor_card,
            orient="horizontal",
            mode="determinate",
            style="ExamGuard.Horizontal.TProgressbar",
        )
        self.progress_bar.pack(fill="x", pady=(4, 10))

        # Metrics Row
        metrics_row = tk.Frame(self.monitor_card, bg=COLOR_CARD_BG)
        metrics_row.pack(fill="x", pady=(0, 14))
        metrics_row.columnconfigure((0, 1, 2, 3), weight=1)

        self.metric_frames = self._create_metric_pill(metrics_row, 0, "Progress", "0 / 0 (0%)")
        self.metric_speed = self._create_metric_pill(metrics_row, 1, "Speed", "0.0 FPS")
        self.metric_people = self._create_metric_pill(metrics_row, 2, "Students Tracked", "0")
        self.metric_incidents = self._create_metric_pill(metrics_row, 3, "Incidents Flagged", "0")

        # Video Preview Canvas
        preview_container = tk.Frame(self.monitor_card, bg="#0F172A", height=280)
        preview_container.pack(fill="x", pady=(4, 0))
        preview_container.pack_propagate(False)

        self.preview_canvas = tk.Canvas(
            preview_container,
            bg="#0F172A",
            highlightthickness=0,
        )
        self.preview_canvas.pack(fill="both", expand=True)

        self.preview_placeholder = self.preview_canvas.create_text(
            340,
            140,
            text="Video preview will appear here during processing",
            font=FONT_BODY,
            fill="#64748B",
        )

    def _create_metric_pill(self, parent: tk.Widget, col: int, label: str, init_val: str) -> tk.Label:
        pill = tk.Frame(
            parent,
            bg="#F8FAFC",
            highlightthickness=1,
            highlightbackground="#E2E8F0",
            padx=12,
            pady=8,
        )
        pill.grid(row=0, column=col, sticky="nsew", padx=4)

        lbl = tk.Label(
            pill,
            text=label,
            font=FONT_SMALL,
            fg=COLOR_TEXT_MUTED,
            bg="#F8FAFC",
        )
        lbl.pack(anchor="w")

        val = tk.Label(
            pill,
            text=init_val,
            font=FONT_BODY_BOLD,
            fg=COLOR_TEXT_PRIMARY,
            bg="#F8FAFC",
        )
        val.pack(anchor="w")
        return val

    def _build_summary_card(self) -> None:
        self.summary_card = tk.Frame(
            self.scroll_content,
            bg="#F0FDF4",  # Light green card
            highlightthickness=1,
            highlightbackground="#86EFAC",
            padx=20,
            pady=18,
        )
        # Initially not packed

        self.summary_title = tk.Label(
            self.summary_card,
            text="✓ Processing Finished Successfully",
            font=FONT_HEADING,
            fg=COLOR_SUCCESS,
            bg="#F0FDF4",
        )
        self.summary_title.pack(anchor="w")

        self.summary_text = tk.Label(
            self.summary_card,
            text="",
            font=FONT_BODY,
            fg=COLOR_TEXT_PRIMARY,
            bg="#F0FDF4",
            justify="left",
            anchor="w",
        )
        self.summary_text.pack(fill="x", pady=(6, 12))

        # Button actions
        btn_row = tk.Frame(self.summary_card, bg="#F0FDF4")
        btn_row.pack(fill="x")

        self.open_video_btn = tk.Button(
            btn_row,
            text="▶ Play Output Video",
            font=FONT_BODY_BOLD,
            bg=COLOR_PRIMARY,
            fg="#FFFFFF",
            relief="flat",
            padx=14,
            pady=6,
            cursor="hand2",
            command=self._open_output_video,
        )
        self.open_video_btn.pack(side="left")

        self.open_folder_btn = tk.Button(
            btn_row,
            text="📂 Open Output Folder",
            font=FONT_BODY,
            bg="#FFFFFF",
            fg=COLOR_TEXT_PRIMARY,
            relief="flat",
            padx=12,
            pady=6,
            cursor="hand2",
            command=self._open_output_folder,
        )
        self.open_folder_btn.pack(side="left", padx=10)

    def _choose_video_file(self) -> None:
        """Open native file dialog and validate selected video."""
        file_path = filedialog.askopenfilename(
            title="Select Exam Video",
            filetypes=[
                ("Video Files", "*.mp4 *.avi *.mov *.mkv"),
                ("All Files", "*.*"),
            ],
        )

        if not file_path:
            return

        path = Path(file_path).resolve()
        if not path.is_file():
            messagebox.showerror("Invalid File", f"File not found: {path}")
            return

        # Validate with OpenCV
        cap = cv2.VideoCapture(str(path))
        if not cap.isOpened():
            messagebox.showerror(
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

        # Update UI
        self.meta_label.config(
            text=(
                f"Selected: {path.name} ({size_mb:.1f} MB) | "
                f"Resolution: {w}x{h} | Frames: {frames} | "
                f"FPS: {fps:.1f} | Duration: {duration_sec:.1f}s"
            ),
            fg=COLOR_TEXT_PRIMARY,
        )
        self.start_btn.config(state="normal")
        self.status_badge.config(text="READY TO PROCESS", fg=COLOR_PRIMARY, bg="#EFF6FF")
        self.summary_card.pack_forget()

    def _start_processing(self) -> None:
        """Initiate background video processing thread."""
        if not self.selected_video_path:
            messagebox.showwarning("No Video", "Please select a video file first.")
            return

        config = load_config()
        self.engine = VideoDetectionEngine(
            model_path=config.get("model_path"),
            confidence_threshold=config.get("confidence_threshold", 0.25),
            cooldown_seconds=config.get("cooldown_seconds", 5.0),
            proximity_threshold_ratio=config.get("proximity_threshold_ratio", 0.6),
            device=config.get("device", "cpu"),
            alerts_dir=Path(config.get("alerts_dir")),
            outputs_dir=Path(config.get("outputs_dir")),
        )

        self.stop_event.clear()
        self.select_btn.config(state="disabled")
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.summary_card.pack_forget()

        self.status_badge.config(text="PROCESSING IN PROGRESS", fg=COLOR_WARNING, bg="#FFFBEB")
        total = self.video_metadata.get("frames", 100)
        self.progress_bar.config(maximum=total, value=0)

        # Launch in background worker thread
        self.worker_thread = threading.Thread(
            target=self._run_engine_worker,
            args=(self.selected_video_path,),
            daemon=True,
        )
        self.worker_thread.start()

    def _run_engine_worker(self, video_path: Path) -> None:
        """Worker function running in separate thread."""
        try:
            result = self.engine.process_video(
                video_path=video_path,
                stop_event=self.stop_event,
                on_progress=self._dispatch_progress,
                on_incident=self._dispatch_incident,
            )
            self.after(0, self._on_processing_complete, result)
        except Exception as e:
            self.after(0, self._on_processing_error, str(e))

    def _dispatch_progress(
        self,
        frame_idx: int,
        total_frames: int,
        fps: float,
        incident_count: int,
        people_count: int,
        preview_frame: Optional[np.ndarray],
    ) -> None:
        """Post progress payload to main UI thread."""
        self.after(
            0,
            self._update_progress_ui,
            frame_idx,
            total_frames,
            fps,
            incident_count,
            people_count,
            preview_frame,
        )

    def _update_progress_ui(
        self,
        frame_idx: int,
        total_frames: int,
        fps: float,
        incident_count: int,
        people_count: int,
        preview_frame: Optional[np.ndarray],
    ) -> None:
        pct = (frame_idx / total_frames * 100) if total_frames > 0 else 0
        self.progress_bar["value"] = frame_idx
        self.metric_frames.config(text=f"{frame_idx} / {total_frames} ({pct:.1f}%)")
        self.metric_speed.config(text=f"{fps:.1f} FPS")
        self.metric_people.config(text=str(people_count))
        self.metric_incidents.config(text=str(incident_count))

        # Render preview image
        if preview_frame is not None:
            self._render_preview(preview_frame)

    def _render_preview(self, bgr_frame: np.ndarray) -> None:
        """Scale and render BGR frame onto the preview canvas."""
        canvas_w = self.preview_canvas.winfo_width()
        canvas_h = self.preview_canvas.winfo_height()
        if canvas_w < 50 or canvas_h < 50:
            canvas_w, canvas_h = 680, 280

        h, w = bgr_frame.shape[:2]
        scale = min(canvas_w / w, canvas_h / h)
        new_w, new_h = max(1, int(w * scale)), max(1, int(h * scale))

        rgb = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)
        resized = cv2.resize(rgb, (new_w, new_h), interpolation=cv2.INTER_AREA)
        img = Image.fromarray(resized)
        self._current_photo = ImageTk.PhotoImage(img)

        self.preview_canvas.delete("all")
        cx = canvas_w / 2
        cy = canvas_h / 2
        self.preview_canvas.create_image(cx, cy, image=self._current_photo, anchor="center")

    def _dispatch_incident(self, incident: Dict[str, Any]) -> None:
        """Trigger parent notification handler."""
        if self.on_incident_logged:
            self.after(0, self.on_incident_logged, incident)

    def _stop_processing(self) -> None:
        """User clicked stop button."""
        if messagebox.askyesno("Confirm Stop", "Do you want to stop video processing early?"):
            self.stop_event.set()
            self.status_badge.config(text="CANCELLING...", fg=COLOR_DANGER, bg="#FEF2F2")

    def _on_processing_complete(self, result: VideoProcessingResult) -> None:
        """Called on main thread when processing finishes."""
        self.last_result = result
        self.select_btn.config(state="normal")
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")

        if result.status == "completed":
            self.status_badge.config(text="COMPLETED", fg=COLOR_SUCCESS, bg="#F0FDF4")
            self.summary_card.config(bg="#F0FDF4", highlightbackground="#86EFAC")
            self.summary_title.config(text="✓ Processing Finished Successfully", fg=COLOR_SUCCESS, bg="#F0FDF4")
        elif result.status == "cancelled":
            self.status_badge.config(text="CANCELLED", fg=COLOR_WARNING, bg="#FFFBEB")
            self.summary_card.config(bg="#FFFBEB", highlightbackground="#FDE68A")
            self.summary_title.config(text="⚠ Processing Stopped by User", fg=COLOR_WARNING, bg="#FFFBEB")
        else:
            self.status_badge.config(text="FAILED", fg=COLOR_DANGER, bg="#FEF2F2")
            self.summary_card.config(bg="#FEF2F2", highlightbackground="#FCA5A5")
            self.summary_title.config(text="✕ Processing Failed", fg=COLOR_DANGER, bg="#FEF2F2")

        summary_msg = (
            f"• Source Video: {result.source_video}\n"
            f"• Frames Processed: {result.processed_frames} of {result.total_frames} (Average speed: {result.fps:.1f} FPS)\n"
            f"• Students Tracked: {result.people_count}\n"
            f"• Incidents Requiring Review: {result.incident_count}\n"
            f"• Evidence Screenshots Saved: {result.screenshots_saved}\n"
            f"• Output Video: {result.output_video or 'None'}"
        )
        if result.error_message:
            summary_msg += f"\n• Error Detail: {result.error_message}"

        self.summary_text.config(text=summary_msg, bg=self.summary_card["bg"])
        self.summary_card.pack(fill="x", padx=24, pady=(0, 24))

    def _on_processing_error(self, err_msg: str) -> None:
        self.select_btn.config(state="normal")
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.status_badge.config(text="ERROR", fg=COLOR_DANGER, bg="#FEF2F2")
        messagebox.showerror("Processing Failed", f"An error occurred while processing video:\n\n{err_msg}")

    def _open_output_video(self) -> None:
        if self.last_result and self.last_result.output_video and Path(self.last_result.output_video).is_file():
            if sys.platform.startswith("win"):
                os.startfile(self.last_result.output_video)
            else:
                subprocess.Popen(["xdg-open", self.last_result.output_video])
        else:
            messagebox.showinfo("Video Unavailable", "Output video file does not exist or was not created.")

    def _open_output_folder(self) -> None:
        if self.last_result and self.last_result.output_video:
            folder = Path(self.last_result.output_video).parent
            if folder.is_dir():
                if sys.platform.startswith("win"):
                    os.startfile(str(folder))
                else:
                    subprocess.Popen(["xdg-open", str(folder)])
