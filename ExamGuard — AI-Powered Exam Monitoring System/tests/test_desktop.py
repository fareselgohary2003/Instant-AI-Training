"""
Tests for Tkinter Desktop Application components and headless initialization.
"""

from __future__ import annotations

import os
import sys

# Ensure Tcl/Tk libraries are located correctly when running inside a Windows virtualenv
if sys.platform.startswith("win"):
    if "TCL_LIBRARY" not in os.environ:
        tcl_candidate = os.path.join(sys.base_prefix, "tcl", "tcl8.6")
        if os.path.exists(tcl_candidate):
            os.environ["TCL_LIBRARY"] = tcl_candidate
    if "TK_LIBRARY" not in os.environ:
        tk_candidate = os.path.join(sys.base_prefix, "tcl", "tk8.6")
        if os.path.exists(tk_candidate):
            os.environ["TK_LIBRARY"] = tk_candidate

import pytest
from desktop_app import ExamGuardDesktopApp
from desktop.notifications import NotificationBanner


@pytest.fixture(scope="module")
def desktop_app():
    """Instantiate a single headless ExamGuard Desktop Application for the test module."""
    app = ExamGuardDesktopApp()
    app.withdraw()  # Do not display window during headless tests
    yield app
    try:
        app.destroy()
    except Exception:
        pass


def test_app_initialization_and_views(desktop_app):
    """Verify that all views are instantiated properly."""
    assert "overview" in desktop_app.views
    assert "processing" in desktop_app.views
    assert "incidents" in desktop_app.views
    assert "review" in desktop_app.views
    assert "settings" in desktop_app.views


def test_navigation_switching(desktop_app):
    """Verify switching views updates active page and visibility."""
    desktop_app._navigate("processing")
    assert desktop_app.current_page == "processing"

    desktop_app._navigate("incidents")
    assert desktop_app.current_page == "incidents"

    desktop_app._navigate("settings")
    assert desktop_app.current_page == "settings"

    desktop_app._navigate("overview")
    assert desktop_app.current_page == "overview"


def test_notification_banner_trigger(desktop_app):
    """Verify that triggering an incident displays the banner with verified details."""
    banner = desktop_app.banner

    incident_payload = {
        "id": 999,
        "track_id": 4,
        "event_type": "phone_detected_review_required",
        "confidence": 0.85,
        "screenshot_path": None,
    }

    desktop_app._on_incident_logged(incident_payload)
    assert banner.current_incident_id == 999
    assert "Phone Detected" in banner.detail_label.cget("text")
    assert "Student #4" in banner.detail_label.cget("text")
