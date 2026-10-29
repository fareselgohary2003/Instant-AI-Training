"""
Incident History view for ExamGuard.
Provides search, status filtering, tabular listing, and quick triage actions.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Optional

from database import get_incidents, update_incident_review
from desktop.theme import (
    COLOR_CARD_BG,
    COLOR_CARD_BORDER,
    COLOR_CONTENT_BG,
    COLOR_DANGER,
    COLOR_PRIMARY,
    COLOR_SUCCESS,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    COLOR_WARNING,
    FONT_BODY,
    FONT_BODY_BOLD,
    FONT_HEADING,
    FONT_SMALL,
    FONT_TITLE,
)


class IncidentsView(tk.Frame):
    """
    Incident history and search table view.
    """

    def __init__(
        self,
        parent: tk.Widget,
        on_open_incident: Callable[[int], None],
        **kwargs,
    ):
        super().__init__(parent, bg=COLOR_CONTENT_BG, **kwargs)
        self.on_open_incident = on_open_incident

        self.current_filter = "all"
        self.search_term = ""

        self._build_header()
        self._build_filter_bar()
        self._build_table()
        self.refresh()

    def _build_header(self) -> None:
        header = tk.Frame(self, bg=COLOR_CONTENT_BG)
        header.pack(fill="x", padx=24, pady=(20, 14))

        eyebrow = tk.Label(
            header,
            text="EXAMGUARD / INCIDENT LOGS",
            font=FONT_SMALL,
            fg=COLOR_PRIMARY,
            bg=COLOR_CONTENT_BG,
        )
        eyebrow.pack(anchor="w")

        title = tk.Label(
            header,
            text="Incident History",
            font=FONT_TITLE,
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_CONTENT_BG,
        )
        title.pack(anchor="w")

        subtitle = tk.Label(
            header,
            text="Search and inspect all AI-flagged examination events. Every observation requires human verification.",
            font=FONT_BODY,
            fg=COLOR_TEXT_MUTED,
            bg=COLOR_CONTENT_BG,
        )
        subtitle.pack(anchor="w")

    def _build_filter_bar(self) -> None:
        bar = tk.Frame(
            self,
            bg=COLOR_CARD_BG,
            highlightthickness=1,
            highlightbackground=COLOR_CARD_BORDER,
            padx=16,
            pady=12,
        )
        bar.pack(fill="x", padx=24, pady=(0, 14))

        # Search box
        search_lbl = tk.Label(
            bar,
            text="🔍 Search:",
            font=FONT_BODY_BOLD,
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_CARD_BG,
        )
        search_lbl.pack(side="left", padx=(0, 6))

        self.search_entry = tk.Entry(
            bar,
            font=FONT_BODY,
            width=28,
            relief="solid",
            bd=1,
        )
        self.search_entry.pack(side="left", padx=(0, 16))
        self.search_entry.bind("<KeyRelease>", self._on_search_change)

        # Status filter
        filter_lbl = tk.Label(
            bar,
            text="Status:",
            font=FONT_BODY_BOLD,
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_CARD_BG,
        )
        filter_lbl.pack(side="left", padx=(0, 6))

        self.status_var = tk.StringVar(value="all")
        self.status_combo = ttk.Combobox(
            bar,
            textvariable=self.status_var,
            values=["all", "pending", "reviewed", "dismissed"],
            state="readonly",
            width=14,
        )
        self.status_combo.pack(side="left", padx=(0, 16))
        self.status_combo.bind("<<ComboboxSelected>>", self._on_filter_change)

        # Refresh
        refresh_btn = ttk.Button(
            bar,
            text="↻ Refresh",
            style="Secondary.TButton",
            command=self.refresh,
            cursor="hand2",
        )
        refresh_btn.pack(side="left")

        # Action Buttons on right
        inspect_btn = tk.Button(
            bar,
            text="Open Review →",
            font=FONT_BODY_BOLD,
            bg=COLOR_PRIMARY,
            fg="#FFFFFF",
            relief="flat",
            padx=12,
            pady=4,
            cursor="hand2",
            command=self._open_selected,
        )
        inspect_btn.pack(side="right")

    def _build_table(self) -> None:
        table_container = tk.Frame(
            self,
            bg=COLOR_CARD_BG,
            highlightthickness=1,
            highlightbackground=COLOR_CARD_BORDER,
        )
        table_container.pack(fill="both", expand=True, padx=24, pady=(0, 14))

        columns = ("id", "time", "track", "event", "confidence", "status", "notes")
        self.tree = ttk.Treeview(
            table_container,
            columns=columns,
            show="headings",
            selectmode="browse",
        )

        self.tree.heading("id", text="ID")
        self.tree.heading("time", text="Timestamp")
        self.tree.heading("track", text="Track ID")
        self.tree.heading("event", text="Detected Event")
        self.tree.heading("confidence", text="Confidence")
        self.tree.heading("status", text="Review Status")
        self.tree.heading("notes", text="Reviewer Notes / Frame")

        self.tree.column("id", width=60, anchor="center")
        self.tree.column("time", width=160, anchor="w")
        self.tree.column("track", width=110, anchor="center")
        self.tree.column("event", width=220, anchor="w")
        self.tree.column("confidence", width=95, anchor="center")
        self.tree.column("status", width=110, anchor="center")
        self.tree.column("notes", width=260, anchor="w")

        scroll_y = ttk.Scrollbar(table_container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll_y.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scroll_y.pack(side="right", fill="y")

        self.tree.bind("<Double-1>", lambda e: self._open_selected())

        # Footer count
        self.footer_lbl = tk.Label(
            self,
            text="Showing 0 incidents",
            font=FONT_SMALL,
            fg=COLOR_TEXT_MUTED,
            bg=COLOR_CONTENT_BG,
            anchor="w",
        )
        self.footer_lbl.pack(fill="x", padx=26, pady=(0, 16))

    def _on_search_change(self, event=None) -> None:
        self.search_term = self.search_entry.get().strip()
        self.refresh()

    def _on_filter_change(self, event=None) -> None:
        self.current_filter = self.status_var.get()
        self.refresh()

    def refresh(self) -> None:
        """Query database with active search and filter parameters."""
        for item in self.tree.get_children():
            self.tree.delete(item)

        incidents = get_incidents(
            status=self.current_filter if self.current_filter != "all" else None,
            search=self.search_term if self.search_term else None,
        )

        for inc in incidents:
            conf_str = f"{inc['confidence']:.1%}" if inc["confidence"] is not None else "—"
            time_str = inc["timestamp"].replace("T", " ")[:19]
            track_str = f"Student #{inc['track_id']}" if inc["track_id"] is not None else "Unassigned"
            event_str = inc["event_type"].replace("_", " ").title()

            self.tree.insert(
                "",
                "end",
                iid=str(inc["id"]),
                values=(
                    f"#{inc['id']}",
                    time_str,
                    track_str,
                    event_str,
                    conf_str,
                    inc["review_status"].upper(),
                    inc["notes"] or "",
                ),
            )

        self.footer_lbl.config(text=f"Showing {len(incidents)} incidents")

    def _open_selected(self) -> None:
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("No Selection", "Please click on an incident in the table to review.")
            return

        incident_id = int(selected[0])
        self.on_open_incident(incident_id)
