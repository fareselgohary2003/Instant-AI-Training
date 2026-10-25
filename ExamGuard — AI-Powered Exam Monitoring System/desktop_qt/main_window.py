"""
Main Window Shell for ExamGuard PySide6 Desktop Application.
Coordinates the collapsible sidebar, stacked page views, and floating notification banner.
"""

from __future__ import annotations

from typing import Dict, Optional
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from config import load_config
from desktop_qt.components.notification import NotificationBanner
from desktop_qt.components.sidebar import CollapsibleSidebar
from desktop_qt.theme import COLOR_BG_DARK, GLOBAL_DARK_STYLESHEET
from desktop_qt.views.incidents_view import IncidentsView
from desktop_qt.views.overview_view import OverviewView
from desktop_qt.views.processing_view import ProcessingView
from desktop_qt.views.review_view import ReviewView
from desktop_qt.views.settings_view import SettingsView


class ExamGuardQtApp(QMainWindow):
    """
    Enterprise PySide6 MainWindow for ExamGuard.
    """

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("ExamGuard — AI Cheating Tracking & Alert System")
        self.resize(1260, 820)
        self.setMinimumSize(1040, 680)

        # Apply dark theme QSS
        self.setStyleSheet(GLOBAL_DARK_STYLESHEET)

        self._build_shell()
        self.navigate_to("overview")

    def _build_shell(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Left Collapsible Sidebar
        self.sidebar = CollapsibleSidebar(self)
        self.sidebar.page_changed.connect(self.navigate_to)
        main_layout.addWidget(self.sidebar)

        # 2. Right Content Area
        right_container = QWidget()
        rc_layout = QVBoxLayout(right_container)
        rc_layout.setContentsMargins(0, 0, 0, 0)
        rc_layout.setSpacing(0)

        # Top Notification Banner
        cfg = load_config()
        self.banner = NotificationBanner(right_container, sound_enabled=cfg.get("sound_alerts", True))
        self.banner.review_requested.connect(self._open_incident_review)
        rc_layout.addWidget(self.banner)

        # Stacked Views Container
        self.stack = QStackedWidget()

        self.view_overview = OverviewView()
        self.view_overview.navigate_requested.connect(self._on_overview_navigate)

        self.view_processing = ProcessingView()
        self.view_processing.incident_logged.connect(self._on_incident_logged)
        self.view_processing.review_requested.connect(self._open_incident_review)

        self.view_incidents = IncidentsView()
        self.view_incidents.open_incident_requested.connect(self._open_incident_review)

        self.view_review = ReviewView()
        self.view_review.back_requested.connect(lambda: self.navigate_to("incidents"))
        self.view_review.review_saved.connect(self._on_review_saved)

        self.view_settings = SettingsView()

        self.page_indices: Dict[str, int] = {
            "overview": self.stack.addWidget(self.view_overview),
            "processing": self.stack.addWidget(self.view_processing),
            "incidents": self.stack.addWidget(self.view_incidents),
            "review": self.stack.addWidget(self.view_review),
            "settings": self.stack.addWidget(self.view_settings),
        }

        rc_layout.addWidget(self.stack, stretch=1)
        main_layout.addWidget(right_container, stretch=1)

    def navigate_to(self, page_id: str) -> None:
        """Switch active stacked view."""
        if page_id in self.page_indices:
            self.stack.setCurrentIndex(self.page_indices[page_id])
            self.sidebar.set_active(page_id)

            active_widget = self.stack.currentWidget()
            if hasattr(active_widget, "refresh"):
                active_widget.refresh()
            elif hasattr(active_widget, "refresh_data"):
                active_widget.refresh_data()

    def _open_incident_review(self, incident_id: int) -> None:
        """Navigate to Review view and load specific incident data."""
        self.view_review.load_incident(incident_id)
        self.navigate_to("review")

    def _on_overview_navigate(self, target_page: str, incident_id: int) -> None:
        if target_page == "review" and incident_id > 0:
            self._open_incident_review(incident_id)
        else:
            self.navigate_to(target_page)

    def _on_incident_logged(self, incident_data: dict) -> None:
        """Handle real-time incident event triggered during processing."""
        self.banner.trigger(incident_data)
        self.view_overview.refresh_data()
        self.view_incidents.refresh()

    def _on_review_saved(self) -> None:
        """Refresh logs and charts after reviewer saves decision."""
        self.view_overview.refresh_data()
        self.view_incidents.refresh()
