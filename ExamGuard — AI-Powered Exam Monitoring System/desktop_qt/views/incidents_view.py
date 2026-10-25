"""
Incident History view for ExamGuard PySide6 Application.
Provides real-time search, status filtering, table sorting, and review navigation.
"""

from __future__ import annotations

from typing import Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from database import get_incidents
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


class IncidentsView(QWidget):
    """
    Searchable incident audit log view.
    """
    open_incident_requested = Signal(int)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.current_filter = "all"
        self.search_term = ""

        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        # Header
        header = QWidget()
        h_layout = QVBoxLayout(header)
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(2)

        eyebrow = QLabel("EXAMGUARD / INCIDENT AUDIT TRAIL")
        eyebrow.setStyleSheet(f"font-size: 11px; font-weight: bold; color: {COLOR_PRIMARY};")
        title = QLabel("Recorded Incident History")
        title.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {COLOR_TEXT_PRIMARY};")
        subtitle = QLabel("Search, filter, and inspect AI-flagged candidate events for human disciplinary review.")
        subtitle.setStyleSheet(f"font-size: 12px; color: {COLOR_TEXT_MUTED};")

        h_layout.addWidget(eyebrow)
        h_layout.addWidget(title)
        h_layout.addWidget(subtitle)
        layout.addWidget(header)

        # Filter & Search Toolbar
        bar = QFrame()
        bar.setProperty("class", "card")
        bar_layout = QHBoxLayout(bar)
        bar_layout.setContentsMargins(16, 12, 16, 12)
        bar_layout.setSpacing(12)

        search_icon = QLabel("🔍")
        bar_layout.addWidget(search_icon)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by Incident ID, Student Track #, or notes...")
        self.search_input.textChanged.connect(self._on_search_changed)
        bar_layout.addWidget(self.search_input, stretch=2)

        status_lbl = QLabel("Filter:")
        status_lbl.setStyleSheet(f"font-weight: bold; color: {COLOR_TEXT_SECONDARY};")
        bar_layout.addWidget(status_lbl)

        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["All Incidents", "Pending", "Reviewed", "Dismissed"])
        self.filter_combo.currentTextChanged.connect(self._on_filter_changed)
        bar_layout.addWidget(self.filter_combo, stretch=1)

        refresh_btn = QPushButton("↻ Refresh")
        refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh_btn.clicked.connect(self.refresh)
        bar_layout.addWidget(refresh_btn)

        layout.addWidget(bar)

        # Table
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels([
            "ID", "Timestamp", "Track ID", "Behavior Detected", "Confidence", "Status", "Reviewer Notes"
        ])
        header_view = self.table.horizontalHeader()
        header_view.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header_view.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header_view.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header_view.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header_view.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header_view.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)

        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.cellDoubleClicked.connect(self._on_cell_double_clicked)
        layout.addWidget(self.table, stretch=1)

        # Footer
        self.footer_lbl = QLabel("Showing 0 incidents")
        self.footer_lbl.setStyleSheet(f"font-size: 11px; color: {COLOR_TEXT_MUTED};")
        layout.addWidget(self.footer_lbl)

    def _on_search_changed(self, text: str) -> None:
        self.search_term = text.strip()
        self.refresh()

    def _on_filter_changed(self, text: str) -> None:
        mapping = {
            "All Incidents": "all",
            "Pending": "pending",
            "Reviewed": "reviewed",
            "Dismissed": "dismissed",
        }
        self.current_filter = mapping.get(text, "all")
        self.refresh()

    def refresh(self) -> None:
        incidents = get_incidents(
            status=self.current_filter if self.current_filter != "all" else None,
            search=self.search_term if self.search_term else None,
        )

        self.table.setRowCount(len(incidents))

        for row_idx, inc in enumerate(incidents):
            inc_id = inc["id"]
            time_str = inc["timestamp"].replace("T", " ")[:19]
            track_str = f"Student #{inc['track_id']}" if inc["track_id"] is not None else "Unassigned"
            event_str = inc["event_type"].replace("_", " ").title()
            conf_str = f"{inc['confidence']:.1%}" if inc["confidence"] is not None else "—"
            status = inc["review_status"]
            notes_str = inc["notes"] or ""

            item_id = QTableWidgetItem(f"#{inc_id}")
            item_id.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row_idx, 0, item_id)
            self.table.setItem(row_idx, 1, QTableWidgetItem(time_str))
            self.table.setItem(row_idx, 2, QTableWidgetItem(track_str))
            self.table.setItem(row_idx, 3, QTableWidgetItem(event_str))

            item_conf = QTableWidgetItem(conf_str)
            item_conf.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row_idx, 4, item_conf)

            # Status pill
            item_status = QTableWidgetItem(status.upper())
            item_status.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if status == "pending":
                item_status.setForeground(QColor(COLOR_WARNING))
            elif status == "reviewed":
                item_status.setForeground(QColor(COLOR_SUCCESS))
            else:
                item_status.setForeground(QColor(COLOR_DANGER))
            self.table.setItem(row_idx, 5, item_status)

            self.table.setItem(row_idx, 6, QTableWidgetItem(notes_str))

        self.footer_lbl.setText(f"Showing {len(incidents)} incidents")

    def _on_cell_double_clicked(self, row: int, col: int) -> None:
        item = self.table.item(row, 0)
        if item:
            inc_id_str = item.text().replace("#", "")
            try:
                self.open_incident_requested.emit(int(inc_id_str))
            except ValueError:
                pass
