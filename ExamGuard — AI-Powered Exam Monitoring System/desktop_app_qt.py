"""
ExamGuard — Cheating Tracking & Alert System
Enterprise PySide6 (Qt for Python) Desktop Application Entry Point.

Run with:
    python desktop_app_qt.py
"""

from __future__ import annotations

import sys
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from config import ensure_directories
from database import init_db
from desktop_qt.main_window import ExamGuardQtApp


def main():
    """Main PySide6 application entry point."""
    ensure_directories()
    init_db()

    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName("ExamGuard")
    app.setOrganizationName("ExamGuard Security")

    window = ExamGuardQtApp()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
