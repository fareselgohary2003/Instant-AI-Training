"""
Overview Dashboard view for ExamGuard.
Presents key metrics, status distributions via pure Tkinter Canvas charts,
and a feed of recent detection events.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional

from database import get_incidents, get_stats
from desktop.theme import (
    COLOR_CARD_BG,
    COLOR_CARD_BORDER,
    COLOR_CONTENT_BG,
    COLOR_DANGER,
    COLOR_PRIMARY,
    COLOR_SUCCESS,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    COLOR_WARNING,
    FONT_BODY,
    FONT_BODY_BOLD,
    FONT_HEADING,
    FONT_SMALL,
    FONT_SUBHEADING,
    FONT_TITLE,
)


class OverviewView(tk.Frame):
    """
    Overview page with stat cards, distribution charts, and recent activity.
    """

    def __init__(
        self,
        parent: tk.Widget,
        on_navigate: Callable[[str, Optional[int]], None],
        **kwargs,
    ):
        super().__init__(parent, bg=COLOR_CONTENT_BG, **kwargs)
        self.on_navigate = on_navigate

        self._build_header()
        self._build_stats_grid()
        self._build_analytics_and_recent()
        self.refresh_data()

    def _build_header(self) -> None:
        header = tk.Frame(self, bg=COLOR_CONTENT_BG)
        header.pack(fill="x", padx=24, pady=(20, 16))

        title_frame = tk.Frame(header, bg=COLOR_CONTENT_BG)
        title_frame.pack(side="left")

        eyebrow = tk.Label(
            title_frame,
            text="EXAMGUARD / OVERVIEW",
            font=FONT_SMALL,
            fg=COLOR_PRIMARY,
            bg=COLOR_CONTENT_BG,
        )
        eyebrow.pack(anchor="w")

        title = tk.Label(
            title_frame,
            text="Proctoring Overview",
            font=FONT_TITLE,
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_CONTENT_BG,
        )
        title.pack(anchor="w")

        subtitle = tk.Label(
            title_frame,
            text="Monitor real-time detections, examine incident volumes, and track pending reviews.",
            font=FONT_BODY,
            fg=COLOR_TEXT_MUTED,
            bg=COLOR_CONTENT_BG,
        )
        subtitle.pack(anchor="w")

        refresh_btn = ttk.Button(
            header,
            text="↻ Refresh Data",
            style="Secondary.TButton",
            command=self.refresh_data,
            cursor="hand2",
        )
        refresh_btn.pack(side="right", pady=5)

    def _build_stats_grid(self) -> None:
        self.stats_container = tk.Frame(self, bg=COLOR_CONTENT_BG)
        self.stats_container.pack(fill="x", padx=24, pady=(0, 20))
        self.stats_container.columnconfigure((0, 1, 2, 3), weight=1, uniform="stat_col")

        self.card_total = self._create_stat_card(0, "Total Incidents", "—", COLOR_PRIMARY, "📊")
        self.card_pending = self._create_stat_card(1, "Pending Review", "—", COLOR_WARNING, "⏳")
        self.card_reviewed = self._create_stat_card(2, "Reviewed", "—", COLOR_SUCCESS, "✓")
        self.card_dismissed = self._create_stat_card(3, "Dismissed", "—", COLOR_DANGER, "✕")

    def _create_stat_card(self, col: int, label: str, init_val: str, tone: str, icon: str) -> tk.Label:
        card = tk.Frame(
            self.stats_container,
            bg=COLOR_CARD_BG,
            highlightthickness=1,
            highlightbackground=COLOR_CARD_BORDER,
            padx=18,
            pady=16,
        )
        card.grid(row=0, column=col, sticky="nsew", padx=6)

        # Top row: icon + title
        top = tk.Frame(card, bg=COLOR_CARD_BG)
        top.pack(fill="x")

        icon_lbl = tk.Label(
            top,
            text=icon,
            font=("Segoe UI", 12),
            fg=tone,
            bg=COLOR_CARD_BG,
        )
        icon_lbl.pack(side="left")

        lbl = tk.Label(
            top,
            text=label,
            font=FONT_BODY_BOLD,
            fg=COLOR_TEXT_MUTED,
            bg=COLOR_CARD_BG,
        )
        lbl.pack(side="left", padx=(8, 0))

        val_lbl = tk.Label(
            card,
            text=init_val,
            font=("Segoe UI", 24, "bold"),
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_CARD_BG,
        )
        val_lbl.pack(anchor="w", pady=(8, 0))

        return val_lbl

    def _build_analytics_and_recent(self) -> None:
        container = tk.Frame(self, bg=COLOR_CONTENT_BG)
        container.pack(fill="both", expand=True, padx=24, pady=(0, 20))
        container.columnconfigure(0, weight=4)  # Chart
        container.columnconfigure(1, weight=5)  # Recent feed

        # 1. Left Card: Chart
        chart_card = tk.Frame(
            container,
            bg=COLOR_CARD_BG,
            highlightthickness=1,
            highlightbackground=COLOR_CARD_BORDER,
            padx=20,
            pady=18,
        )
        chart_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        chart_title = tk.Label(
            chart_card,
            text="Review Status Distribution",
            font=FONT_HEADING,
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_CARD_BG,
        )
        chart_title.pack(anchor="w")

        chart_desc = tk.Label(
            chart_card,
            text="Proportion of detected events categorized by current review status.",
            font=FONT_SMALL,
            fg=COLOR_TEXT_MUTED,
            bg=COLOR_CARD_BG,
        )
        chart_desc.pack(anchor="w", pady=(0, 14))

        self.chart_canvas = tk.Canvas(
            chart_card,
            bg=COLOR_CARD_BG,
            highlightthickness=0,
            height=200,
        )
        self.chart_canvas.pack(fill="both", expand=True)

        # 2. Right Card: Recent Incidents
        recent_card = tk.Frame(
            container,
            bg=COLOR_CARD_BG,
            highlightthickness=1,
            highlightbackground=COLOR_CARD_BORDER,
            padx=20,
            pady=18,
        )
        recent_card.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        recent_header = tk.Frame(recent_card, bg=COLOR_CARD_BG)
        recent_header.pack(fill="x", pady=(0, 12))

        recent_title = tk.Label(
            recent_header,
            text="Recent Detections",
            font=FONT_HEADING,
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_CARD_BG,
        )
        recent_title.pack(side="left")

        view_all_btn = tk.Button(
            recent_header,
            text="View All →",
            font=FONT_SMALL,
            fg=COLOR_PRIMARY,
            bg=COLOR_CARD_BG,
            bd=0,
            cursor="hand2",
            command=lambda: self.on_navigate("incidents", None),
        )
        view_all_btn.pack(side="right")

        self.recent_list_frame = tk.Frame(recent_card, bg=COLOR_CARD_BG)
        self.recent_list_frame.pack(fill="both", expand=True)

    def refresh_data(self) -> None:
        """Fetch latest statistics and redraw charts and recent table."""
        try:
            stats = get_stats()
            total = stats.get("total_incidents", 0)
            pending = stats.get("pending", 0)
            reviewed = stats.get("reviewed", 0)
            dismissed = stats.get("dismissed", 0)

            self.card_total.config(text=str(total))
            self.card_pending.config(text=str(pending))
            self.card_reviewed.config(text=str(reviewed))
            self.card_dismissed.config(text=str(dismissed))

            self._draw_status_chart(pending, reviewed, dismissed)
            self._populate_recent_list()
        except Exception as e:
            print(f"[ExamGuard Overview] Error refreshing data: {e}")

    def _draw_status_chart(self, pending: int, reviewed: int, dismissed: int) -> None:
        """Render a clean custom bar chart on the Tkinter canvas."""
        c = self.chart_canvas
        c.delete("all")

        w = c.winfo_width()
        h = c.winfo_height()
        if w < 100:
            w = 340
        if h < 100:
            h = 200

        data = [
            ("Pending", pending, COLOR_WARNING),
            ("Reviewed", reviewed, COLOR_SUCCESS),
            ("Dismissed", dismissed, COLOR_DANGER),
        ]

        total = pending + reviewed + dismissed
        if total == 0:
            c.create_text(
                w / 2,
                h / 2,
                text="No incidents logged yet.\nUpload and process a video to see analytics.",
                font=FONT_BODY,
                fill=COLOR_TEXT_MUTED,
                justify="center",
            )
            return

        bar_h = 26
        gap = 28
        start_y = 25
        max_bar_w = w - 160

        for i, (label, count, color) in enumerate(data):
            y = start_y + i * (bar_h + gap)
            pct = (count / total) * 100 if total > 0 else 0
            bar_len = int((count / total) * max_bar_w) if total > 0 else 0
            bar_len = max(4, bar_len) if count > 0 else 0

            # Label
            c.create_text(
                10,
                y + bar_h / 2,
                text=label,
                font=FONT_BODY_BOLD,
                fill=COLOR_TEXT_PRIMARY,
                anchor="w",
            )

            # Bar background track
            c.create_rectangle(
                85,
                y,
                85 + max_bar_w,
                y + bar_h,
                fill="#F1F5F9",
                outline="",
            )

            # Filled bar
            if bar_len > 0:
                c.create_rectangle(
                    85,
                    y,
                    85 + bar_len,
                    y + bar_h,
                    fill=color,
                    outline="",
                )

            # Value and percentage
            c.create_text(
                85 + max_bar_w + 12,
                y + bar_h / 2,
                text=f"{count} ({pct:.0f}%)",
                font=FONT_SMALL,
                fill=COLOR_TEXT_SECONDARY,
                anchor="w",
            )

    def _populate_recent_list(self) -> None:
        """Render the 5 latest recorded incidents."""
        for child in self.recent_list_frame.winfo_children():
            child.destroy()

        incidents = get_incidents(limit=5)
        if not incidents:
            empty_lbl = tk.Label(
                self.recent_list_frame,
                text="No incidents recorded yet.",
                font=FONT_BODY,
                fg=COLOR_TEXT_MUTED,
                bg=COLOR_CARD_BG,
                pady=30,
            )
            empty_lbl.pack()
            return

        for inc in incidents:
            row = tk.Frame(
                self.recent_list_frame,
                bg=COLOR_CARD_BG,
                highlightthickness=1,
                highlightbackground="#F1F5F9",
                padx=12,
                pady=10,
            )
            row.pack(fill="x", pady=3)

            left = tk.Frame(row, bg=COLOR_CARD_BG)
            left.pack(side="left")

            title_txt = f"Incident #{inc['id']} — Track #{inc['track_id'] if inc['track_id'] is not None else 'Unassigned'}"
            lbl_title = tk.Label(
                left,
                text=title_txt,
                font=FONT_BODY_BOLD,
                fg=COLOR_TEXT_PRIMARY,
                bg=COLOR_CARD_BG,
            )
            lbl_title.pack(anchor="w")

            readable_time = inc["timestamp"].replace("T", " ")[:19]
            lbl_sub = tk.Label(
                left,
                text=f"{readable_time} | Conf: {inc['confidence']:.0%}" if inc['confidence'] else readable_time,
                font=FONT_SMALL,
                fg=COLOR_TEXT_MUTED,
                bg=COLOR_CARD_BG,
            )
            lbl_sub.pack(anchor="w")

            # Status pill
            status = inc["review_status"]
            status_colors = {
                "pending": (COLOR_WARNING, "#FFFBEB"),
                "reviewed": (COLOR_SUCCESS, "#F0FDF4"),
                "dismissed": (COLOR_DANGER, "#FEF2F2"),
            }
            fg_col, bg_col = status_colors.get(status, (COLOR_TEXT_MUTED, "#F1F5F9"))

            status_lbl = tk.Label(
                row,
                text=status.upper(),
                font=("Segoe UI", 8, "bold"),
                fg=fg_col,
                bg=bg_col,
                padx=8,
                pady=2,
            )
            status_lbl.pack(side="right", padx=(10, 8))

            rev_btn = tk.Button(
                row,
                text="Inspect",
                font=FONT_SMALL,
                bg="#EFF6FF",
                fg=COLOR_PRIMARY,
                relief="flat",
                padx=8,
                pady=2,
                cursor="hand2",
                command=lambda inc_id=inc["id"]: self.on_navigate("review", inc_id),
            )
            rev_btn.pack(side="right")
