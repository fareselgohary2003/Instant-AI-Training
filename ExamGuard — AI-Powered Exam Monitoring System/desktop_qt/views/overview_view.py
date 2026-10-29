"""
Overview Dashboard view for ExamGuard PySide6 Application.
Presents enterprise KPI cards, a custom painted review-status distribution chart,
and a live feed of recent detection events.
"""

from __future__ import annotations

from typing import Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPaintEvent
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from database import get_incidents, get_stats
from desktop_qt.theme import (
    COLOR_BORDER,
    COLOR_DANGER,
    COLOR_DANGER_BG,
    COLOR_PRIMARY,
    COLOR_SUCCESS,
    COLOR_SUCCESS_BG,
    COLOR_SURFACE,
    COLOR_SURFACE_ALT,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    COLOR_WARNING,
    COLOR_WARNING_BG,
)


class StatusChartWidget(QWidget):
    """Custom painted distribution bar chart."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.pending = 0
        self.reviewed = 0
        self.dismissed = 0
        self.setMinimumHeight(180)

    def set_data(self, pending: int, reviewed: int, dismissed: int) -> None:
        self.pending = pending
        self.reviewed = reviewed
        self.dismissed = dismissed
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        total = self.pending + self.reviewed + self.dismissed

        if total == 0:
            painter.setPen(QColor(COLOR_TEXT_MUTED))
            painter.setFont(QFont("Segoe UI", 11))
            painter.drawText(
                0, 0, w, h,
                Qt.AlignmentFlag.AlignCenter,
                "No incidents recorded yet.\nUpload and process an exam video to populate analytics.",
            )
            return

        items = [
            ("Pending", self.pending, QColor(COLOR_WARNING)),
            ("Reviewed", self.reviewed, QColor(COLOR_SUCCESS)),
            ("Dismissed", self.dismissed, QColor(COLOR_DANGER)),
        ]

        bar_h = 24
        spacing = 30
        start_y = 20
        max_bar_w = max(100, w - 180)

        for i, (label, count, color) in enumerate(items):
            y = start_y + i * (bar_h + spacing)
            pct = (count / total) * 100 if total > 0 else 0
            bar_len = int((count / total) * max_bar_w) if total > 0 else 0
            if count > 0:
                bar_len = max(6, bar_len)

            # Draw Label
            painter.setPen(QColor(COLOR_TEXT_PRIMARY))
            painter.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            painter.drawText(10, y + 17, label)

            # Draw Track Background
            painter.setBrush(QColor(COLOR_SURFACE_ALT))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(95, y, max_bar_w, bar_h, 4, 4)

            # Draw Filled Bar
            if bar_len > 0:
                painter.setBrush(color)
                painter.drawRoundedRect(95, y, bar_len, bar_h, 4, 4)

            # Draw Count & Pct
            painter.setPen(QColor(COLOR_TEXT_SECONDARY))
            painter.setFont(QFont("Segoe UI", 9))
            painter.drawText(95 + max_bar_w + 12, y + 17, f"{count} ({pct:.0f}%)")


class OverviewView(QWidget):
    """Overview dashboard page."""
    navigate_requested = Signal(str, int)  # target_page, incident_id

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._build_ui()
        self.refresh_data()

    def _build_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(28, 24, 28, 24)
        main_layout.setSpacing(20)

        # Header
        header = QWidget()
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(0, 0, 0, 0)

        title_box = QWidget()
        tb_layout = QVBoxLayout(title_box)
        tb_layout.setContentsMargins(0, 0, 0, 0)
        tb_layout.setSpacing(2)

        eyebrow = QLabel("EXAMGUARD / ENTERPRISE OVERVIEW")
        eyebrow.setStyleSheet(f"font-size: 11px; font-weight: bold; color: {COLOR_PRIMARY};")
        title = QLabel("Proctoring Operations Dashboard")
        title.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {COLOR_TEXT_PRIMARY};")
        subtitle = QLabel("Live overview of automated AI detections, review queue, and proctor determinations.")
        subtitle.setStyleSheet(f"font-size: 12px; color: {COLOR_TEXT_MUTED};")

        tb_layout.addWidget(eyebrow)
        tb_layout.addWidget(title)
        tb_layout.addWidget(subtitle)
        h_layout.addWidget(title_box)

        h_layout.addStretch()

        refresh_btn = QPushButton("↻  Refresh Data")
        refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh_btn.clicked.connect(self.refresh_data)
        h_layout.addWidget(refresh_btn)

        main_layout.addWidget(header)

        # KPI Cards Grid
        grid_widget = QWidget()
        grid_layout = QGridLayout(grid_widget)
        grid_layout.setContentsMargins(0, 0, 0, 0)
        grid_layout.setSpacing(14)

        self.kpi_total = self._create_kpi_card("Total Incidents", "—", "📊", COLOR_PRIMARY)
        self.kpi_pending = self._create_kpi_card("Pending Review", "—", "⏳", COLOR_WARNING)
        self.kpi_reviewed = self._create_kpi_card("Reviewed (Flagged)", "—", "✓", COLOR_SUCCESS)
        self.kpi_dismissed = self._create_kpi_card("Dismissed (False Positive)", "—", "✕", COLOR_DANGER)

        grid_layout.addWidget(self.kpi_total[0], 0, 0)
        grid_layout.addWidget(self.kpi_pending[0], 0, 1)
        grid_layout.addWidget(self.kpi_reviewed[0], 0, 2)
        grid_layout.addWidget(self.kpi_dismissed[0], 0, 3)

        main_layout.addWidget(grid_widget)

        # Analytics & Recent Section (Split horizontal)
        split_widget = QWidget()
        split_layout = QHBoxLayout(split_widget)
        split_layout.setContentsMargins(0, 0, 0, 0)
        split_layout.setSpacing(16)

        # Left: Chart Card
        chart_card = QFrame()
        chart_card.setProperty("class", "card")
        cc_layout = QVBoxLayout(chart_card)
        cc_layout.setContentsMargins(18, 16, 18, 16)
        cc_layout.setSpacing(6)

        chart_title = QLabel("Review Decision Distribution")
        chart_title.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {COLOR_TEXT_PRIMARY};")
        chart_sub = QLabel("Proportion of candidate events categorized by review determination.")
        chart_sub.setStyleSheet(f"font-size: 11px; color: {COLOR_TEXT_MUTED};")
        cc_layout.addWidget(chart_title)
        cc_layout.addWidget(chart_sub)

        self.chart_widget = StatusChartWidget()
        cc_layout.addWidget(self.chart_widget, stretch=1)
        split_layout.addWidget(chart_card, stretch=4)

        # Right: Recent Incidents Card
        recent_card = QFrame()
        recent_card.setProperty("class", "card")
        rc_layout = QVBoxLayout(recent_card)
        rc_layout.setContentsMargins(18, 16, 18, 16)
        rc_layout.setSpacing(10)

        rc_header = QWidget()
        rch_layout = QHBoxLayout(rc_header)
        rch_layout.setContentsMargins(0, 0, 0, 0)

        rc_title = QLabel("Recent Candidate Incidents")
        rc_title.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {COLOR_TEXT_PRIMARY};")
        rch_layout.addWidget(rc_title)

        rch_layout.addStretch()

        view_all_btn = QPushButton("View All →")
        view_all_btn.setStyleSheet(f"background: transparent; border: none; color: {COLOR_PRIMARY}; font-weight: bold;")
        view_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        view_all_btn.clicked.connect(lambda: self.navigate_requested.emit("incidents", -1))
        rch_layout.addWidget(view_all_btn)

        rc_layout.addWidget(rc_header)

        # Recent Table
        self.recent_table = QTableWidget(0, 5)
        self.recent_table.setHorizontalHeaderLabels(["ID", "Track ID", "Time", "Status", "Action"])
        self.recent_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.recent_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.recent_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.recent_table.verticalHeader().setVisible(False)
        self.recent_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.recent_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        rc_layout.addWidget(self.recent_table, stretch=1)

        split_layout.addWidget(recent_card, stretch=6)
        main_layout.addWidget(split_widget, stretch=1)

    def _create_kpi_card(self, title: str, init_val: str, icon: str, tone_color: str) -> tuple[QFrame, QLabel]:
        card = QFrame()
        card.setProperty("class", "card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)

        top_row = QWidget()
        tr_layout = QHBoxLayout(top_row)
        tr_layout.setContentsMargins(0, 0, 0, 0)

        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet("font-size: 14px;")
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet(f"font-size: 12px; font-weight: bold; color: {COLOR_TEXT_SECONDARY};")
        tr_layout.addWidget(icon_lbl)
        tr_layout.addWidget(lbl_title)
        tr_layout.addStretch()
        layout.addWidget(top_row)

        val_lbl = QLabel(init_val)
        val_lbl.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {COLOR_TEXT_PRIMARY};")
        layout.addWidget(val_lbl)

        return card, val_lbl

    def refresh_data(self) -> None:
        """Fetch statistics and populate cards and recent table."""
        try:
            stats = get_stats()
            total = stats.get("total_incidents", 0)
            pending = stats.get("pending", 0)
            reviewed = stats.get("reviewed", 0)
            dismissed = stats.get("dismissed", 0)

            self.kpi_total[1].setText(str(total))
            self.kpi_pending[1].setText(str(pending))
            self.kpi_reviewed[1].setText(str(reviewed))
            self.kpi_dismissed[1].setText(str(dismissed))

            self.chart_widget.set_data(pending, reviewed, dismissed)
            self._populate_recent_table()
        except Exception as e:
            print(f"[ExamGuard Qt Overview] Error refreshing data: {e}")

    def _populate_recent_table(self) -> None:
        incidents = get_incidents(limit=5)
        self.recent_table.setRowCount(len(incidents))

        for row_idx, inc in enumerate(incidents):
            inc_id = inc["id"]
            track_str = f"Student #{inc['track_id']}" if inc["track_id"] is not None else "Unassigned"
            time_str = inc["timestamp"].replace("T", " ")[:19]
            status = inc["review_status"]

            self.recent_table.setItem(row_idx, 0, QTableWidgetItem(f"#{inc_id}"))
            self.recent_table.setItem(row_idx, 1, QTableWidgetItem(track_str))
            self.recent_table.setItem(row_idx, 2, QTableWidgetItem(time_str))

            # Status item
            status_item = QTableWidgetItem(status.upper())
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if status == "pending":
                status_item.setForeground(QColor(COLOR_WARNING))
            elif status == "reviewed":
                status_item.setForeground(QColor(COLOR_SUCCESS))
            else:
                status_item.setForeground(QColor(COLOR_DANGER))
            self.recent_table.setItem(row_idx, 3, status_item)

            # Inspect Button
            btn = QPushButton("Inspect")
            btn.setProperty("class", "primary")
            btn.setStyleSheet("padding: 4px 10px; font-size: 11px;")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked=False, i_id=inc_id: self.navigate_requested.emit("review", i_id))
            self.recent_table.setCellWidget(row_idx, 4, btn)
