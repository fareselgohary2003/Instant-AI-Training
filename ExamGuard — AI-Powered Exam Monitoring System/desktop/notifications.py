"""
In-app notification system and audio alerts for ExamGuard.
Meets Requirement G:
- Displays Event Type, Timestamp, Track ID, and Screenshot verification status.
- Provides a direct 'Review Incident' action button.
- Never blocks video processing.
- Plays a non-intrusive sound alert on Windows.
"""

from __future__ import annotations

import sys
import tkinter as tk
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from desktop.theme import (
    COLOR_CARD_BORDER,
    COLOR_DANGER,
    COLOR_PRIMARY,
    COLOR_TEXT_PRIMARY,
    FONT_BODY,
    FONT_BODY_BOLD,
    FONT_SMALL,
)


class NotificationBanner(tk.Frame):
    """
    Floating top banner that alerts the proctor immediately upon incident detection.
    """

    def __init__(
        self,
        parent: tk.Widget,
        on_open_incident: Optional[Callable[[int], None]] = None,
        sound_enabled: bool = True,
        **kwargs,
    ):
        super().__init__(
            parent,
            bg="#FEF2F2",  # Light red / amber tint
            highlightthickness=1,
            highlightbackground="#FCA5A5",
            padx=16,
            pady=12,
            **kwargs,
        )
        self.on_open_incident = on_open_incident
        self.sound_enabled = sound_enabled
        self.current_incident_id: Optional[int] = None
        self._auto_dismiss_id: Optional[str] = None

        self._build_ui()
        self.hide()

    def _build_ui(self) -> None:
        # Left Accent Bar
        self.accent_bar = tk.Frame(self, bg=COLOR_DANGER, width=5)
        self.accent_bar.pack(side="left", fill="y", padx=(0, 12))

        # Content column
        content_frame = tk.Frame(self, bg="#FEF2F2")
        content_frame.pack(side="left", fill="both", expand=True)

        # Header line
        header_frame = tk.Frame(content_frame, bg="#FEF2F2")
        header_frame.pack(fill="x")

        self.title_label = tk.Label(
            header_frame,
            text="⚠️ Cheating Alert Detected",
            font=FONT_BODY_BOLD,
            fg=COLOR_DANGER,
            bg="#FEF2F2",
        )
        self.title_label.pack(side="left")

        self.time_label = tk.Label(
            header_frame,
            text="",
            font=FONT_SMALL,
            fg="#991B1B",
            bg="#FEF2F2",
        )
        self.time_label.pack(side="right", padx=(10, 0))

        # Detail description
        self.detail_label = tk.Label(
            content_frame,
            text="",
            font=FONT_BODY,
            fg=COLOR_TEXT_PRIMARY,
            bg="#FEF2F2",
            justify="left",
            anchor="w",
        )
        self.detail_label.pack(fill="x", pady=(2, 2))

        # Screenshot status line
        self.screenshot_label = tk.Label(
            content_frame,
            text="",
            font=FONT_SMALL,
            fg="#166534",  # Green text for verified save
            bg="#FEF2F2",
            justify="left",
            anchor="w",
        )
        self.screenshot_label.pack(fill="x")

        # Action Buttons frame
        actions_frame = tk.Frame(self, bg="#FEF2F2")
        actions_frame.pack(side="right", padx=(16, 0))

        self.review_btn = tk.Button(
            actions_frame,
            text="Review Incident",
            font=FONT_BODY_BOLD,
            bg=COLOR_PRIMARY,
            fg="#FFFFFF",
            activebackground="#1D4ED8",
            activeforeground="#FFFFFF",
            relief="flat",
            padx=12,
            pady=4,
            cursor="hand2",
            command=self._handle_review,
        )
        self.review_btn.pack(side="left", padx=4)

        self.close_btn = tk.Button(
            actions_frame,
            text="✕",
            font=("Segoe UI", 11, "bold"),
            bg="#FEF2F2",
            fg="#991B1B",
            relief="flat",
            bd=0,
            cursor="hand2",
            command=self.hide,
        )
        self.close_btn.pack(side="left", padx=2)

    def trigger(self, incident_data: Dict[str, Any]) -> None:
        """Pop up notification with incident metadata and play audio chime."""
        if self._auto_dismiss_id:
            try:
                self.after_cancel(self._auto_dismiss_id)
            except Exception:
                pass

        self.current_incident_id = incident_data.get("id")
        event_type = incident_data.get("event_type", "phone_detected_review_required")
        readable_event = event_type.replace("_", " ").title()
        track_id = incident_data.get("track_id")
        student_str = f"Student #{track_id}" if track_id is not None else "Unassigned (Review Required)"

        time_now = datetime.now().strftime("%I:%M:%S %p")
        self.time_label.config(text=f"Time: {time_now}")
        self.detail_label.config(
            text=f"Behavior: {readable_event} | Track: {student_str}"
        )

        screenshot_path = incident_data.get("screenshot_path")
        if screenshot_path and Path(screenshot_path).is_file():
            self.screenshot_label.config(
                text=f"✓ Screenshot saved successfully: {Path(screenshot_path).name}",
                fg="#166534",
            )
        else:
            self.screenshot_label.config(
                text="Screenshot pending or unverified.",
                fg="#991B1B",
            )

        # Show banner
        siblings = [c for c in self.master.winfo_children() if c != self]
        if siblings:
            self.pack(fill="x", padx=16, pady=(12, 0), before=siblings[0])
        else:
            self.pack(fill="x", padx=16, pady=(12, 0))

        # Sound alert on Windows
        if self.sound_enabled and sys.platform.startswith("win"):
            try:
                import winsound
                winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
            except Exception:
                pass

        # Auto-dismiss after 14 seconds
        self._auto_dismiss_id = self.after(14000, self.hide)

    def _handle_review(self) -> None:
        if self.current_incident_id and self.on_open_incident:
            self.on_open_incident(self.current_incident_id)
        self.hide()

    def hide(self) -> None:
        """Dismiss the notification banner."""
        self.pack_forget()
