"""
In-app notification banner component for ExamGuard PySide6.
Displays immediate visual and audio alerts when a suspicious event is logged.
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from desktop_qt.theme import (
    COLOR_DANGER,
    COLOR_DANGER_BG,
    COLOR_PRIMARY,
    COLOR_SUCCESS,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
)


class NotificationBanner(QFrame):
    """
    Floating alert banner that slides into view upon qualifying incident detection.
    """
    review_requested = Signal(int)

    def __init__(self, parent: Optional[QWidget] = None, sound_enabled: bool = True):
        super().__init__(parent)
        self.sound_enabled = sound_enabled
        self.current_incident_id: Optional[int] = None

        self.setStyleSheet(f"""
            QFrame#NotificationBanner {{
                background-color: #450A0A;
                border: 1px solid #991B1B;
                border-left: 5px solid {COLOR_DANGER};
                border-radius: 6px;
                padding: 10px 14px;
            }}
            QLabel#AlertTitle {{
                font-weight: bold;
                font-size: 13px;
                color: #FCA5A5;
            }}
            QLabel#AlertSub {{
                color: #F8FAFC;
                font-size: 12px;
            }}
            QLabel#AlertTime {{
                color: #FCA5A5;
                font-size: 11px;
            }}
            QLabel#AlertPath {{
                color: #86EFAC;
                font-size: 11px;
            }}
            QPushButton#ReviewBtn {{
                background-color: {COLOR_PRIMARY};
                border: none;
                border-radius: 4px;
                color: #FFFFFF;
                font-weight: bold;
                font-size: 12px;
                padding: 6px 14px;
            }}
            QPushButton#ReviewBtn:hover {{
                background-color: #2563EB;
            }}
            QPushButton#CloseBtn {{
                background: transparent;
                border: none;
                color: #FCA5A5;
                font-size: 14px;
                font-weight: bold;
                padding: 2px 6px;
            }}
            QPushButton#CloseBtn:hover {{
                color: #FFFFFF;
            }}
        """)
        self.setObjectName("NotificationBanner")
        self._build_ui()
        self.hide()

    def _build_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)

        icon_lbl = QLabel("⚠️")
        icon_lbl.setStyleSheet("font-size: 20px;")
        layout.addWidget(icon_lbl)

        content_box = QWidget()
        content_layout = QVBoxLayout(content_box)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(2)

        top_row = QWidget()
        top_layout = QHBoxLayout(top_row)
        top_layout.setContentsMargins(0, 0, 0, 0)

        self.title_lbl = QLabel("Cheating Alert Detected")
        self.title_lbl.setObjectName("AlertTitle")
        top_layout.addWidget(self.title_lbl)

        top_layout.addStretch()

        self.time_lbl = QLabel("")
        self.time_lbl.setObjectName("AlertTime")
        top_layout.addWidget(self.time_lbl)
        content_layout.addWidget(top_row)

        self.detail_lbl = QLabel("")
        self.detail_lbl.setObjectName("AlertSub")
        content_layout.addWidget(self.detail_lbl)

        self.screenshot_lbl = QLabel("")
        self.screenshot_lbl.setObjectName("AlertPath")
        content_layout.addWidget(self.screenshot_lbl)

        layout.addWidget(content_box, stretch=1)

        # Action Buttons
        self.review_btn = QPushButton("Review Incident")
        self.review_btn.setObjectName("ReviewBtn")
        self.review_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.review_btn.clicked.connect(self._on_review_clicked)
        layout.addWidget(self.review_btn)

        close_btn = QPushButton("✕")
        close_btn.setObjectName("CloseBtn")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.hide)
        layout.addWidget(close_btn)

    def trigger(self, incident_data: Dict[str, Any]) -> None:
        """Display alert notification and play audio chime."""
        self.current_incident_id = incident_data.get("id")
        event_type = incident_data.get("event_type", "phone_detected_review_required")
        readable_event = event_type.replace("_", " ").title()
        track_id = incident_data.get("track_id")
        student_str = f"Student #{track_id}" if track_id is not None else "Unassigned (Review Required)"

        time_now = datetime.now().strftime("%I:%M:%S %p")
        self.time_lbl.setText(f"Time: {time_now}")
        self.detail_lbl.setText(f"Behavior: {readable_event} | Assigned to: {student_str}")

        screenshot_path = incident_data.get("screenshot_path")
        if screenshot_path and Path(screenshot_path).is_file():
            self.screenshot_lbl.setText(f"✓ Screenshot saved successfully: {Path(screenshot_path).name}")
            self.screenshot_lbl.setStyleSheet("color: #86EFAC; font-size: 11px;")
        else:
            self.screenshot_lbl.setText("Screenshot unverified or pending.")
            self.screenshot_lbl.setStyleSheet("color: #FCA5A5; font-size: 11px;")

        self.show()

        if self.sound_enabled and sys.platform.startswith("win"):
            try:
                import winsound
                winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
            except Exception:
                pass

        # Auto-dismiss after 14 seconds
        QTimer.singleShot(14000, self.hide)

    def _on_review_clicked(self) -> None:
        if self.current_incident_id:
            self.review_requested.emit(self.current_incident_id)
        self.hide()
