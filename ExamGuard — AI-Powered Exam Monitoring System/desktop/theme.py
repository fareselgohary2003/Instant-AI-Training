"""
Visual theme, palette, and typography configurations for ExamGuard desktop app.
Implements a sleek, modern, professional desktop interface using Tkinter and ttk.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

# Professional Color Palette
COLOR_SIDEBAR_BG = "#0F172A"       # Dark Navy / Slate 900
COLOR_SIDEBAR_HOVER = "#1E293B"    # Slate 800
COLOR_SIDEBAR_ACTIVE = "#2563EB"   # Vibrant Blue
COLOR_SIDEBAR_TEXT = "#94A3B8"     # Muted Slate 400
COLOR_SIDEBAR_TEXT_LIGHT = "#FFFFFF"

COLOR_CONTENT_BG = "#F8FAFC"       # Light Slate 50
COLOR_CARD_BG = "#FFFFFF"          # Pure White
COLOR_CARD_BORDER = "#E2E8F0"      # Light Gray / Slate 200

COLOR_PRIMARY = "#2563EB"          # Royal Blue
COLOR_PRIMARY_HOVER = "#1D4ED8"
COLOR_SUCCESS = "#16A34A"          # Forest Green
COLOR_WARNING = "#D97706"          # Warm Amber
COLOR_DANGER = "#DC2626"           # Crimson Red

COLOR_TEXT_PRIMARY = "#0F172A"     # Deep Slate
COLOR_TEXT_SECONDARY = "#475569"   # Neutral Slate
COLOR_TEXT_MUTED = "#64748B"       # Subtle Muted

FONT_FAMILY = "Segoe UI"
FONT_TITLE = (FONT_FAMILY, 16, "bold")
FONT_HEADING = (FONT_FAMILY, 12, "bold")
FONT_SUBHEADING = (FONT_FAMILY, 11, "bold")
FONT_BODY = (FONT_FAMILY, 10)
FONT_BODY_BOLD = (FONT_FAMILY, 10, "bold")
FONT_SMALL = (FONT_FAMILY, 9)
FONT_MONO = ("Consolas", 9)


def apply_theme(root: tk.Tk) -> ttk.Style:
    """Configure modern ttk styles for the application."""
    style = ttk.Style(root)

    # Use 'clam' or 'vista' if available for crisp custom borders
    available_themes = style.theme_names()
    if "clam" in available_themes:
        style.theme_use("clam")

    # General Frame styles
    style.configure("TFrame", background=COLOR_CONTENT_BG)
    style.configure("Card.TFrame", background=COLOR_CARD_BG, relief="flat")
    style.configure("Sidebar.TFrame", background=COLOR_SIDEBAR_BG)

    # Label styles
    style.configure(
        "TLabel",
        background=COLOR_CONTENT_BG,
        foreground=COLOR_TEXT_PRIMARY,
        font=FONT_BODY,
    )
    style.configure(
        "Card.TLabel",
        background=COLOR_CARD_BG,
        foreground=COLOR_TEXT_PRIMARY,
        font=FONT_BODY,
    )
    style.configure(
        "CardHeading.TLabel",
        background=COLOR_CARD_BG,
        foreground=COLOR_TEXT_PRIMARY,
        font=FONT_HEADING,
    )
    style.configure(
        "CardMuted.TLabel",
        background=COLOR_CARD_BG,
        foreground=COLOR_TEXT_MUTED,
        font=FONT_SMALL,
    )

    # Primary Action Button
    style.configure(
        "Primary.TButton",
        background=COLOR_PRIMARY,
        foreground="#FFFFFF",
        font=FONT_BODY_BOLD,
        borderwidth=0,
        focuscolor="none",
        padding=(14, 8),
    )
    style.map(
        "Primary.TButton",
        background=[("active", COLOR_PRIMARY_HOVER), ("disabled", "#94A3B8")],
        foreground=[("disabled", "#F1F5F9")],
    )

    # Success Button
    style.configure(
        "Success.TButton",
        background=COLOR_SUCCESS,
        foreground="#FFFFFF",
        font=FONT_BODY_BOLD,
        borderwidth=0,
        focuscolor="none",
        padding=(12, 7),
    )
    style.map(
        "Success.TButton",
        background=[("active", "#15803D"), ("disabled", "#94A3B8")],
    )

    # Danger Button
    style.configure(
        "Danger.TButton",
        background=COLOR_DANGER,
        foreground="#FFFFFF",
        font=FONT_BODY_BOLD,
        borderwidth=0,
        focuscolor="none",
        padding=(12, 7),
    )
    style.map(
        "Danger.TButton",
        background=[("active", "#B91C1C"), ("disabled", "#94A3B8")],
    )

    # Secondary Outline Button
    style.configure(
        "Secondary.TButton",
        background="#FFFFFF",
        foreground=COLOR_TEXT_PRIMARY,
        font=FONT_BODY,
        borderwidth=1,
        focuscolor="none",
        padding=(12, 7),
    )
    style.map(
        "Secondary.TButton",
        background=[("active", "#F8FAFC")],
    )

    # Modern Progress Bar
    style.configure(
        "ExamGuard.Horizontal.TProgressbar",
        troughcolor="#E2E8F0",
        background=COLOR_PRIMARY,
        thickness=10,
        borderwidth=0,
    )

    # Treeview (Data Table)
    style.configure(
        "Treeview",
        background="#FFFFFF",
        foreground=COLOR_TEXT_PRIMARY,
        rowheight=32,
        font=FONT_BODY,
        borderwidth=1,
        relief="solid",
    )
    style.configure(
        "Treeview.Heading",
        background="#F1F5F9",
        foreground=COLOR_TEXT_PRIMARY,
        font=FONT_BODY_BOLD,
        padding=(8, 8),
        borderwidth=1,
        relief="flat",
    )
    style.map(
        "Treeview",
        background=[("selected", "#EFF6FF")],
        foreground=[("selected", COLOR_PRIMARY)],
    )

    return style
