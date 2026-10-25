"""
Incident Detail and Review view for ExamGuard PySide6 Application.
Enables proctors to examine high-resolution evidence screenshots,
inspect detection metadata, and record disciplinary determinations with notes.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtGui import QColor, QDesktopServices, QPixmap
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from config import BASE_DIR
from database import get_incident, update_incident_review
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


class ReviewView(QWidget):
    """
    Evidence review and decision panel.
    """
    back_requested = Signal()
    review_saved = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.current_incident_id: Optional[int] = None
        self.current_incident_data: Optional[dict] = None

        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(18)

        # Header with Back Button
        header = QWidget()
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(14)

        back_btn = QPushButton("←  Back to List")
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.clicked.connect(self.back_requested.emit)
        h_layout.addWidget(back_btn)

        title_box = QWidget()
        tb_layout = QVBoxLayout(title_box)
        tb_layout.setContentsMargins(0, 0, 0, 0)
        tb_layout.setSpacing(2)

        self.title_lbl = QLabel("Incident Evidence Review")
        self.title_lbl.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {COLOR_TEXT_PRIMARY};")
        sub = QLabel("Verify captured video evidence and record proctoring observations.")
        sub.setStyleSheet(f"font-size: 12px; color: {COLOR_TEXT_MUTED};")
        tb_layout.addWidget(self.title_lbl)
        tb_layout.addWidget(sub)
        h_layout.addWidget(title_box)

        h_layout.addStretch()
        layout.addWidget(header)

        # Two-column split container
        split = QWidget()
        s_layout = QHBoxLayout(split)
        s_layout.setContentsMargins(0, 0, 0, 0)
        s_layout.setSpacing(16)

        # 1. Left: Evidence Screenshot Card
        evidence_card = QFrame()
        evidence_card.setProperty("class", "card")
        ec_layout = QVBoxLayout(evidence_card)
        ec_layout.setContentsMargins(18, 16, 18, 16)
        ec_layout.setSpacing(12)

        ec_top = QWidget()
        ect_layout = QHBoxLayout(ec_top)
        ect_layout.setContentsMargins(0, 0, 0, 0)

        lbl_ev = QLabel("Captured Evidence Frame")
        lbl_ev.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {COLOR_TEXT_PRIMARY};")
        ect_layout.addWidget(lbl_ev)

        ect_layout.addStretch()

        open_ext_btn = QPushButton("🔍  Open Full Image")
        open_ext_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        open_ext_btn.clicked.connect(self._open_external_viewer)
        ect_layout.addWidget(open_ext_btn)
        ec_layout.addWidget(ec_top)

        # Image Label Display
        self.image_label = QLabel("No incident selected")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMinimumSize(460, 360)
        self.image_label.setStyleSheet("background-color: #050811; border: 1px solid #334155; border-radius: 6px; color: #64748B;")
        ec_layout.addWidget(self.image_label, stretch=1)

        s_layout.addWidget(evidence_card, stretch=6)

        # 2. Right: Decision & Metadata Card
        form_card = QFrame()
        form_card.setProperty("class", "card")
        fc_layout = QVBoxLayout(form_card)
        fc_layout.setContentsMargins(20, 18, 20, 18)
        fc_layout.setSpacing(12)

        fc_title = QLabel("Incident Details & Determination")
        fc_title.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {COLOR_TEXT_PRIMARY};")
        fc_layout.addWidget(fc_title)

        # Metadata Grid
        meta_grid = QFrame()
        meta_grid.setStyleSheet(f"background-color: {COLOR_SURFACE_ALT}; border: 1px solid {COLOR_BORDER}; border-radius: 6px; padding: 6px;")
        mg_layout = QGridLayout(meta_grid)
        mg_layout.setContentsMargins(10, 8, 10, 8)
        mg_layout.setVerticalSpacing(6)

        self.lbl_id = self._add_grid_row(mg_layout, 0, "Incident ID", "—")
        self.lbl_track = self._add_grid_row(mg_layout, 1, "Student Track ID", "—")
        self.lbl_conf = self._add_grid_row(mg_layout, 2, "Model Confidence", "—")
        self.lbl_time = self._add_grid_row(mg_layout, 3, "Captured At", "—")
        self.lbl_video = self._add_grid_row(mg_layout, 4, "Source Video", "—")
        self.lbl_frame = self._add_grid_row(mg_layout, 5, "Frame Index", "—")
        fc_layout.addWidget(meta_grid)

        # Status Radio Group
        status_lbl = QLabel("Proctor Determination:")
        status_lbl.setStyleSheet(f"font-weight: bold; color: {COLOR_TEXT_SECONDARY}; margin-top: 4px;")
        fc_layout.addWidget(status_lbl)

        self.btn_group = QButtonGroup(self)
        self.rb_pending = QRadioButton("⏳  Pending Review")
        self.rb_reviewed = QRadioButton("✓  Reviewed (Confirmed Misconduct)")
        self.rb_dismissed = QRadioButton("✕  Dismissed (False Positive)")

        self.btn_group.addButton(self.rb_pending, 1)
        self.btn_group.addButton(self.rb_reviewed, 2)
        self.btn_group.addButton(self.rb_dismissed, 3)

        fc_layout.addWidget(self.rb_pending)
        fc_layout.addWidget(self.rb_reviewed)
        fc_layout.addWidget(self.rb_dismissed)

        # Notes Area
        notes_lbl = QLabel("Supervisor Notes / Disciplinary Rationale:")
        notes_lbl.setStyleSheet(f"font-weight: bold; color: {COLOR_TEXT_SECONDARY}; margin-top: 4px;")
        fc_layout.addWidget(notes_lbl)

        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("Describe observations, context, and actions taken...")
        self.notes_edit.setMaximumHeight(100)
        fc_layout.addWidget(self.notes_edit)

        disclaimer = QLabel("⚠ AI detections are review signals, not proof of cheating. Final decisions must be made by a human reviewer.")
        disclaimer.setWordWrap(True)
        disclaimer.setStyleSheet(f"font-size: 11px; color: {COLOR_TEXT_MUTED};")
        fc_layout.addWidget(disclaimer)

        # Save Button
        save_btn = QPushButton("💾  Save Review Determination")
        save_btn.setProperty("class", "primary")
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.clicked.connect(self._save_review)
        fc_layout.addWidget(save_btn)

        s_layout.addWidget(form_card, stretch=5)
        layout.addWidget(split, stretch=1)

    def _add_grid_row(self, layout: QGridLayout, row: int, key: str, val: str) -> QLabel:
        k_lbl = QLabel(key + ":")
        k_lbl.setStyleSheet(f"font-size: 11px; color: {COLOR_TEXT_MUTED};")
        v_lbl = QLabel(val)
        v_lbl.setStyleSheet(f"font-size: 12px; font-weight: bold; color: {COLOR_TEXT_PRIMARY};")
        layout.addWidget(k_lbl, row, 0)
        layout.addWidget(v_lbl, row, 1)
        return v_lbl

    def load_incident(self, incident_id: int) -> None:
        self.current_incident_id = incident_id
        row = get_incident(incident_id)
        if not row:
            QMessageBox.critical(self, "Error", f"Incident #{incident_id} not found in database.")
            return

        self.current_incident_data = dict(row)
        data = self.current_incident_data

        self.title_lbl.setText(f"Incident #{data['id']} Evidence Review")
        self.lbl_id.setText(f"#{data['id']}")
        self.lbl_track.setText(f"Student #{data['track_id']}" if data["track_id"] is not None else "Unassigned")
        self.lbl_conf.setText(f"{data['confidence']:.1%}" if data["confidence"] is not None else "—")
        self.lbl_time.setText(data["timestamp"].replace("T", " ")[:19])
        self.lbl_video.setText(str(data.get("source_video") or "—"))
        self.lbl_frame.setText(str(data.get("frame_number") or "—"))

        status = data.get("review_status", "pending")
        if status == "reviewed":
            self.rb_reviewed.setChecked(True)
        elif status == "dismissed":
            self.rb_dismissed.setChecked(True)
        else:
            self.rb_pending.setChecked(True)

        self.notes_edit.setText(data.get("notes") or "")

        # Display image
        self._load_screenshot(data.get("screenshot_path"))

    def _load_screenshot(self, raw_path: Optional[str]) -> None:
        if not raw_path:
            self.image_label.setText("No screenshot file recorded for this incident.")
            return

        path = Path(raw_path)
        if not path.is_absolute():
            path = BASE_DIR / path

        if not path.is_file():
            self.image_label.setText(f"Screenshot file missing on disk:\n{path.name}")
            return

        pix = QPixmap(str(path))
        if pix.isNull():
            self.image_label.setText("Failed to decode screenshot image.")
            return

        lbl_w = max(100, self.image_label.width())
        lbl_h = max(100, self.image_label.height())
        scaled = pix.scaled(
            lbl_w,
            lbl_h,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.image_label.setPixmap(scaled)

    def _save_review(self) -> None:
        if not self.current_incident_id:
            return

        if self.rb_reviewed.isChecked():
            status = "reviewed"
        elif self.rb_dismissed.isChecked():
            status = "dismissed"
        else:
            status = "pending"

        notes = self.notes_edit.toPlainText().strip()

        try:
            ok = update_incident_review(self.current_incident_id, status, notes)
            if ok:
                QMessageBox.information(
                    self,
                    "Saved",
                    f"Review determination for Incident #{self.current_incident_id} saved successfully.",
                )
                self.review_saved.emit()
            else:
                QMessageBox.critical(self, "Error", "Could not update incident record.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save review: {e}")

    def _open_external_viewer(self) -> None:
        if not self.current_incident_data:
            return
        raw_path = self.current_incident_data.get("screenshot_path")
        if not raw_path:
            return
        path = Path(raw_path)
        if not path.is_absolute():
            path = (BASE_DIR / path).resolve()
        if path.is_file():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))
