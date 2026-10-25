"""
Unit and integration tests for ExamGuard PySide6 Desktop Application.
"""

from __future__ import annotations

import pytest
from PySide6.QtWidgets import QApplication

from desktop_qt.main_window import ExamGuardQtApp
from core.engine import VideoDetectionEngine
from desktop_qt.worker import VideoProcessingWorker


@pytest.fixture(scope="module")
def qapp():
    """Ensure QApplication instance exists for Qt tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def qt_main_window(qapp):
    """Instantiate ExamGuardQtApp for testing."""
    window = ExamGuardQtApp()
    yield window
    try:
        window.close()
    except Exception:
        pass


def test_qt_app_pages_initialization(qt_main_window):
    """Verify all 5 enterprise pages are registered."""
    expected_pages = ["overview", "processing", "incidents", "review", "settings"]
    for page in expected_pages:
        assert page in qt_main_window.page_indices
        assert qt_main_window.stack.widget(qt_main_window.page_indices[page]) is not None


def test_qt_navigation_switching(qt_main_window):
    """Verify switching views updates active index and sidebar button."""
    for page in ["processing", "incidents", "settings", "overview"]:
        qt_main_window.navigate_to(page)
        expected_idx = qt_main_window.page_indices[page]
        assert qt_main_window.stack.currentIndex() == expected_idx


def test_qt_notification_banner_trigger(qt_main_window):
    """Verify notification banner populates incident details and displays."""
    banner = qt_main_window.banner
    sample_incident = {
        "id": 888,
        "track_id": 9,
        "event_type": "phone_detected_review_required",
        "confidence": 0.82,
        "screenshot_path": None,
    }

    qt_main_window._on_incident_logged(sample_incident)
    assert banner.current_incident_id == 888
    assert "Phone Detected" in banner.detail_lbl.text()
    assert "Student #9" in banner.detail_lbl.text()
    assert not banner.isHidden()


def test_qt_worker_signal_setup(tmp_path):
    """Verify VideoProcessingWorker signals and stop mechanism."""
    dummy_video = tmp_path / "dummy.mp4"
    dummy_video.touch()

    engine = VideoDetectionEngine(
        model_path=tmp_path / "dummy.pt",
        alerts_dir=tmp_path / "alerts",
        outputs_dir=tmp_path / "outputs",
    )
    worker = VideoProcessingWorker(engine, dummy_video)

    assert not worker.stop_event.is_set()
    worker.stop()
    assert worker.stop_event.is_set()
