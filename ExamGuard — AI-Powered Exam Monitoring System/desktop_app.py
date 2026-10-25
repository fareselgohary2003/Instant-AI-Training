"""
ExamGuard — Cheating Tracking and Alert System
Native Desktop Application Entry Point.

Run with:
    python desktop_app.py
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

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any, Dict, Optional

from config import DB_PATH, ensure_directories, load_config
from database import get_stats, init_db
from desktop.notifications import NotificationBanner
from desktop.theme import (
    COLOR_CONTENT_BG,
    COLOR_PRIMARY,
    COLOR_SIDEBAR_ACTIVE,
    COLOR_SIDEBAR_BG,
    COLOR_SIDEBAR_HOVER,
    COLOR_SIDEBAR_TEXT,
    COLOR_SIDEBAR_TEXT_LIGHT,
    FONT_BODY,
    FONT_BODY_BOLD,
    FONT_HEADING,
    FONT_SMALL,
    FONT_TITLE,
    apply_theme,
)
from desktop.views.incidents_view import IncidentsView
from desktop.views.overview_view import OverviewView
from desktop.views.processing_view import ProcessingView
from desktop.views.review_view import ReviewView
from desktop.views.settings_view import SettingsView


class ExamGuardDesktopApp(tk.Tk):
    """
    Main application shell and navigation controller for ExamGuard.
    """

    def __init__(self):
        super().__init__()
        self.title("ExamGuard — Cheating Tracking & Alert System")
        self.geometry("1240x800")
        self.minsize(1050, 680)

        # Initialize folders & database safely
        ensure_directories()
        init_db()

        # Apply global theme
        self.style = apply_theme(self)
        self.configure(bg=COLOR_CONTENT_BG)

        self.current_page = "overview"
        self.views: Dict[str, tk.Widget] = {}

        self._build_shell()
        self._navigate("overview")

    def _build_shell(self) -> None:
        # Root layout: Left Sidebar + Right Main Area
        self.columnconfigure(0, weight=0, minsize=240)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        # 1. Left Navigation Sidebar
        self.sidebar = tk.Frame(self, bg=COLOR_SIDEBAR_BG, width=240)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.pack_propagate(False)

        # Brand header
        brand_frame = tk.Frame(self.sidebar, bg=COLOR_SIDEBAR_BG, padx=20, pady=24)
        brand_frame.pack(fill="x")

        brand_icon = tk.Label(
            brand_frame,
            text="🛡️",
            font=("Segoe UI", 20),
            bg=COLOR_SIDEBAR_BG,
        )
        brand_icon.pack(side="left")

        brand_text_box = tk.Frame(brand_frame, bg=COLOR_SIDEBAR_BG)
        brand_text_box.pack(side="left", padx=(10, 0))

        brand_name = tk.Label(
            brand_text_box,
            text="ExamGuard",
            font=("Segoe UI", 14, "bold"),
            fg="#FFFFFF",
            bg=COLOR_SIDEBAR_BG,
        )
        brand_name.pack(anchor="w")

        brand_sub = tk.Label(
            brand_text_box,
            text="Proctoring System",
            font=("Segoe UI", 9),
            fg="#94A3B8",
            bg=COLOR_SIDEBAR_BG,
        )
        brand_sub.pack(anchor="w")

        # Sidebar navigation label
        nav_label = tk.Label(
            self.sidebar,
            text="NAVIGATION",
            font=("Segoe UI", 8, "bold"),
            fg="#64748B",
            bg=COLOR_SIDEBAR_BG,
            padx=20,
            pady=8,
            anchor="w",
        )
        nav_label.pack(fill="x")

        # Navigation Buttons
        self.nav_buttons: Dict[str, tk.Button] = {}
        nav_items = [
            ("overview", "📊 Dashboard Overview"),
            ("processing", "🎥 Video Analysis"),
            ("incidents", "📋 Incident History"),
            ("settings", "⚙️ Settings"),
        ]

        for page_id, text in nav_items:
            btn = tk.Button(
                self.sidebar,
                text=text,
                font=FONT_BODY_BOLD,
                fg=COLOR_SIDEBAR_TEXT,
                bg=COLOR_SIDEBAR_BG,
                activebackground=COLOR_SIDEBAR_HOVER,
                activeforeground=COLOR_SIDEBAR_TEXT_LIGHT,
                relief="flat",
                anchor="w",
                padx=20,
                pady=12,
                cursor="hand2",
                command=lambda p=page_id: self._navigate(p),
            )
            btn.pack(fill="x")
            self.nav_buttons[page_id] = btn

        # Sidebar Footer
        footer_frame = tk.Frame(self.sidebar, bg=COLOR_SIDEBAR_BG, padx=20, pady=20)
        footer_frame.pack(side="bottom", fill="x")

        status_dot = tk.Label(
            footer_frame,
            text="●",
            font=("Segoe UI", 12),
            fg="#22C55E",  # Green online dot
            bg=COLOR_SIDEBAR_BG,
        )
        status_dot.pack(side="left")

        footer_text = tk.Frame(footer_frame, bg=COLOR_SIDEBAR_BG)
        footer_text.pack(side="left", padx=(8, 0))

        db_status = tk.Label(
            footer_text,
            text="Database Connected",
            font=("Segoe UI", 9, "bold"),
            fg="#F8FAFC",
            bg=COLOR_SIDEBAR_BG,
        )
        db_status.pack(anchor="w")

        db_name = tk.Label(
            footer_text,
            text="cheating_system.db",
            font=("Segoe UI", 8),
            fg="#94A3B8",
            bg=COLOR_SIDEBAR_BG,
        )
        db_name.pack(anchor="w")

        # 2. Right Content Area
        self.main_container = tk.Frame(self, bg=COLOR_CONTENT_BG)
        self.main_container.grid(row=0, column=1, sticky="nsew")

        # Top in-app notification banner
        cfg = load_config()
        self.banner = NotificationBanner(
            self.main_container,
            on_open_incident=self._open_incident_detail,
            sound_enabled=cfg.get("sound_alerts", True),
        )

        # Content frame holding current active view
        self.view_container = tk.Frame(self.main_container, bg=COLOR_CONTENT_BG)
        self.view_container.pack(fill="both", expand=True)

        # Initialize subviews
        self.views["overview"] = OverviewView(
            self.view_container,
            on_navigate=self._navigate_with_target,
        )
        self.views["processing"] = ProcessingView(
            self.view_container,
            on_incident_logged=self._on_incident_logged,
            on_navigate_review=self._open_incident_detail,
        )
        self.views["incidents"] = IncidentsView(
            self.view_container,
            on_open_incident=self._open_incident_detail,
        )
        self.views["review"] = ReviewView(
            self.view_container,
            on_back=lambda: self._navigate("incidents"),
            on_review_saved=self._on_review_saved,
        )
        self.views["settings"] = SettingsView(self.view_container)

    def _navigate(self, page_id: str) -> None:
        """Switch current view page."""
        self.current_page = page_id

        # Update button highlights
        for pid, btn in self.nav_buttons.items():
            if pid == page_id:
                btn.config(bg=COLOR_SIDEBAR_ACTIVE, fg=COLOR_SIDEBAR_TEXT_LIGHT)
            else:
                btn.config(bg=COLOR_SIDEBAR_BG, fg=COLOR_SIDEBAR_TEXT)

        # Pack active view
        for pid, view in self.views.items():
            if pid == page_id:
                view.pack(fill="both", expand=True)
                if hasattr(view, "refresh"):
                    view.refresh()
                elif hasattr(view, "refresh_data"):
                    view.refresh_data()
            else:
                view.pack_forget()

    def _navigate_with_target(self, page_id: str, target_id: Optional[int] = None) -> None:
        """Navigate to a page, optionally loading a specific incident."""
        if page_id == "review" and target_id is not None:
            self._open_incident_detail(target_id)
        else:
            self._navigate(page_id)

    def _open_incident_detail(self, incident_id: int) -> None:
        """Open detailed review view for a specific incident."""
        review_view: ReviewView = self.views["review"]
        review_view.load_incident(incident_id)
        self._navigate("review")

    def _on_incident_logged(self, incident_data: Dict[str, Any]) -> None:
        """Handle real-time incident event triggered during video processing."""
        # 1. Pop up notification banner with action button
        self.banner.trigger(incident_data)

        # 2. Refresh Overview & Incidents view if they exist
        if "overview" in self.views and hasattr(self.views["overview"], "refresh_data"):
            self.views["overview"].refresh_data()
        if "incidents" in self.views and hasattr(self.views["incidents"], "refresh"):
            self.views["incidents"].refresh()

    def _on_review_saved(self) -> None:
        """Notify views when reviewer saves a decision."""
        if "overview" in self.views and hasattr(self.views["overview"], "refresh_data"):
            self.views["overview"].refresh_data()
        if "incidents" in self.views and hasattr(self.views["incidents"], "refresh"):
            self.views["incidents"].refresh()


def main():
    """Main desktop application entry point."""
    try:
        app = ExamGuardDesktopApp()
        app.mainloop()
    except Exception as e:
        print(f"[ExamGuard Desktop] Fatal error: {e}")
        try:
            messagebox.showerror("Fatal Error", f"Failed to start ExamGuard Desktop:\n\n{e}")
        except Exception:
            pass
        sys.exit(1)


if __name__ == "__main__":
    main()
