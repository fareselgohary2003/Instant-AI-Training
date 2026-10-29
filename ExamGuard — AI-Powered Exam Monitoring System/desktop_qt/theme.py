"""
Enterprise Dark Theme and Design System for ExamGuard PySide6 Desktop Application.
Inspired by mission-critical security and monitoring software.
"""

from __future__ import annotations

# Palette Constants
COLOR_BG_DARK = "#0B1120"          # Deep Navy 950
COLOR_SURFACE = "#1E293B"          # Slate 800
COLOR_SURFACE_ALT = "#162032"      # Slate 850
COLOR_SIDEBAR = "#0F172A"          # Slate 900
COLOR_SIDEBAR_HOVER = "#1E293B"
COLOR_SIDEBAR_ACTIVE = "#1E3A8A"   # Dark Blue Accent
COLOR_BORDER = "#334155"           # Slate 700
COLOR_BORDER_LIGHT = "#475569"     # Slate 600

COLOR_PRIMARY = "#3B82F6"          # Electric Blue 500
COLOR_PRIMARY_HOVER = "#2563EB"    # Blue 600
COLOR_PRIMARY_BG = "#1D3B6F"

COLOR_SUCCESS = "#10B981"          # Emerald 500 (Normal / Reviewed)
COLOR_SUCCESS_BG = "#064E3B"
COLOR_WARNING = "#F59E0B"          # Amber 500 (Pending Review)
COLOR_WARNING_BG = "#78350F"
COLOR_DANGER = "#EF4444"           # Crimson 500 (Suspicious / Review Required / Dismissed)
COLOR_DANGER_BG = "#7F1D1D"

COLOR_TEXT_PRIMARY = "#F8FAFC"     # Slate 50
COLOR_TEXT_SECONDARY = "#94A3B8"   # Slate 400
COLOR_TEXT_MUTED = "#64748B"       # Slate 500

GLOBAL_DARK_STYLESHEET = f"""
QMainWindow {{
    background-color: {COLOR_BG_DARK};
    color: {COLOR_TEXT_PRIMARY};
}}

QWidget {{
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
    font-size: 13px;
    color: {COLOR_TEXT_PRIMARY};
    background-color: transparent;
}}

/* ScrollBars */
QScrollBar:vertical {{
    background: {COLOR_BG_DARK};
    width: 8px;
    margin: 0;
    border-radius: 4px;
}}
QScrollBar::handle:vertical {{
    background: {COLOR_BORDER};
    min-height: 24px;
    border-radius: 4px;
}}
QScrollBar::handle:vertical:hover {{
    background: {COLOR_PRIMARY};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

/* Generic Cards / Panels */
QFrame.card {{
    background-color: {COLOR_SURFACE};
    border: 1px solid {COLOR_BORDER};
    border-radius: 8px;
}}

/* PushButtons */
QPushButton {{
    font-weight: 600;
    font-size: 13px;
    padding: 8px 16px;
    border-radius: 6px;
    background-color: {COLOR_SURFACE};
    border: 1px solid {COLOR_BORDER};
    color: {COLOR_TEXT_PRIMARY};
}}
QPushButton:hover {{
    background-color: {COLOR_BORDER};
    border-color: {COLOR_BORDER_LIGHT};
}}
QPushButton:pressed {{
    background-color: {COLOR_BG_DARK};
}}
QPushButton:disabled {{
    background-color: {COLOR_SURFACE_ALT};
    border-color: {COLOR_BORDER};
    color: {COLOR_TEXT_MUTED};
}}

QPushButton.primary {{
    background-color: {COLOR_PRIMARY};
    border: 1px solid {COLOR_PRIMARY_HOVER};
    color: #FFFFFF;
}}
QPushButton.primary:hover {{
    background-color: {COLOR_PRIMARY_HOVER};
}}
QPushButton.primary:disabled {{
    background-color: #1E293B;
    border-color: #334155;
    color: #64748B;
}}

QPushButton.success {{
    background-color: {COLOR_SUCCESS};
    border: 1px solid #059669;
    color: #FFFFFF;
}}
QPushButton.success:hover {{
    background-color: #059669;
}}

QPushButton.danger {{
    background-color: {COLOR_DANGER};
    border: 1px solid #DC2626;
    color: #FFFFFF;
}}
QPushButton.danger:hover {{
    background-color: #DC2626;
}}

/* Input Fields */
QLineEdit, QTextEdit, QPlainTextEdit {{
    background-color: {COLOR_SURFACE_ALT};
    border: 1px solid {COLOR_BORDER};
    border-radius: 6px;
    padding: 8px 12px;
    color: {COLOR_TEXT_PRIMARY};
    font-size: 13px;
    selection-background-color: {COLOR_PRIMARY};
}}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
    border: 1px solid {COLOR_PRIMARY};
}}

/* ComboBox */
QComboBox {{
    background-color: {COLOR_SURFACE_ALT};
    border: 1px solid {COLOR_BORDER};
    border-radius: 6px;
    padding: 6px 12px;
    color: {COLOR_TEXT_PRIMARY};
}}
QComboBox:focus {{
    border: 1px solid {COLOR_PRIMARY};
}}
QComboBox::drop-down {{
    border: none;
    width: 24px;
}}
QComboBox QAbstractItemView {{
    background-color: {COLOR_SURFACE};
    border: 1px solid {COLOR_BORDER};
    color: {COLOR_TEXT_PRIMARY};
    selection-background-color: {COLOR_PRIMARY};
    selection-color: #FFFFFF;
    outline: none;
}}

/* Progress Bar */
QProgressBar {{
    background-color: {COLOR_SURFACE_ALT};
    border: 1px solid {COLOR_BORDER};
    border-radius: 5px;
    height: 10px;
    text-align: center;
    font-size: 11px;
    color: {COLOR_TEXT_PRIMARY};
}}
QProgressBar::chunk {{
    background-color: {COLOR_PRIMARY};
    border-radius: 4px;
}}

/* Table Widget */
QTableWidget {{
    background-color: {COLOR_SURFACE};
    border: 1px solid {COLOR_BORDER};
    border-radius: 8px;
    gridline-color: #1E293B;
    selection-background-color: #1E3A8A;
    selection-color: #FFFFFF;
}}
QHeaderView::section {{
    background-color: {COLOR_SIDEBAR};
    color: {COLOR_TEXT_SECONDARY};
    font-weight: 600;
    font-size: 12px;
    padding: 10px 8px;
    border: none;
    border-bottom: 2px solid {COLOR_BORDER};
}}
QTableWidget QTableCornerButton::section {{
    background-color: {COLOR_SIDEBAR};
    border: none;
}}

/* RadioButton & CheckBox */
QRadioButton, QCheckBox {{
    color: {COLOR_TEXT_PRIMARY};
    spacing: 8px;
}}
QRadioButton::indicator, QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border: 1px solid {COLOR_BORDER};
    border-radius: 4px;
    background-color: {COLOR_SURFACE_ALT};
}}
QRadioButton::indicator {{
    border-radius: 8px;
}}
QRadioButton::indicator:checked, QCheckBox::indicator:checked {{
    background-color: {COLOR_PRIMARY};
    border-color: {COLOR_PRIMARY};
}}

/* Slider */
QSlider::groove:horizontal {{
    height: 6px;
    background: {COLOR_BORDER};
    border-radius: 3px;
}}
QSlider::sub-page:horizontal {{
    background: {COLOR_PRIMARY};
    border-radius: 3px;
}}
QSlider::handle:horizontal {{
    background: #FFFFFF;
    border: 2px solid {COLOR_PRIMARY};
    width: 16px;
    height: 16px;
    margin: -5px 0;
    border-radius: 8px;
}}
"""
