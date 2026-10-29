"""
Collapsible Navigation Sidebar for ExamGuard PySide6 Desktop Application.
"""

from __future__ import annotations

from typing import Dict, Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from desktop_qt.theme import (
    COLOR_BORDER,
    COLOR_PRIMARY,
    COLOR_SIDEBAR,
    COLOR_SIDEBAR_ACTIVE,
    COLOR_SIDEBAR_HOVER,
    COLOR_SUCCESS,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
)


class SidebarButton(QPushButton):
    """Custom navigation button with active accent styling."""

    def __init__(self, page_id: str, label: str, icon_str: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.page_id = page_id
        self.full_label = label
        self.icon_str = icon_str
        self.is_collapsed = False

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setCheckable(True)
        self.update_display()

    def update_display(self) -> None:
        if self.is_collapsed:
            self.setText(self.icon_str)
            self.setToolTip(self.full_label)
        else:
            self.setText(f"  {self.icon_str}   {self.full_label}")
            self.setToolTip("")

    def set_collapsed(self, collapsed: bool) -> None:
        self.is_collapsed = collapsed
        self.update_display()


class CollapsibleSidebar(QFrame):
    """
    Enterprise collapsible navigation sidebar with animated or toggleable width.
    """
    page_changed = Signal(str)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.is_collapsed = False
        self.buttons: Dict[str, SidebarButton] = {}

        self.setStyleSheet(f"""
            QFrame#SidebarFrame {{
                background-color: {COLOR_SIDEBAR};
                border-right: 1px solid {COLOR_BORDER};
            }}
            QPushButton.nav_btn {{
                background-color: transparent;
                border: none;
                border-radius: 6px;
                color: {COLOR_TEXT_SECONDARY};
                font-size: 13px;
                font-weight: 600;
                text-align: left;
                padding: 12px 14px;
                margin: 2px 8px;
            }}
            QPushButton.nav_btn:hover {{
                background-color: {COLOR_SIDEBAR_HOVER};
                color: {COLOR_TEXT_PRIMARY};
            }}
            QPushButton.nav_btn:checked {{
                background-color: {COLOR_SIDEBAR_ACTIVE};
                color: #FFFFFF;
                border-left: 3px solid {COLOR_PRIMARY};
            }}
            QPushButton#ToggleBtn {{
                background-color: transparent;
                border: none;
                color: {COLOR_TEXT_SECONDARY};
                font-size: 16px;
                font-weight: bold;
                padding: 6px;
            }}
            QPushButton#ToggleBtn:hover {{
                color: {COLOR_TEXT_PRIMARY};
            }}
        """)
        self.setObjectName("SidebarFrame")
        self.setFixedWidth(240)

        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 16, 0, 16)
        layout.setSpacing(4)

        # Header with Logo & Collapse Toggle
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(16, 0, 12, 12)

        self.logo_lbl = QLabel("🛡️")
        self.logo_lbl.setStyleSheet("font-size: 20px;")
        header_layout.addWidget(self.logo_lbl)

        self.brand_box = QWidget()
        brand_layout = QVBoxLayout(self.brand_box)
        brand_layout.setContentsMargins(8, 0, 0, 0)
        brand_layout.setSpacing(0)

        brand_name = QLabel("ExamGuard")
        brand_name.setStyleSheet(f"font-size: 15px; font-weight: bold; color: {COLOR_TEXT_PRIMARY};")
        brand_desc = QLabel("Security Suite")
        brand_desc.setStyleSheet(f"font-size: 10px; color: {COLOR_TEXT_MUTED};")
        brand_layout.addWidget(brand_name)
        brand_layout.addWidget(brand_desc)
        header_layout.addWidget(self.brand_box)

        header_layout.addStretch()

        self.toggle_btn = QPushButton("≡")
        self.toggle_btn.setObjectName("ToggleBtn")
        self.toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_btn.setToolTip("Collapse / Expand Sidebar")
        self.toggle_btn.clicked.connect(self.toggle_collapse)
        header_layout.addWidget(self.toggle_btn)

        layout.addWidget(header_widget)

        # Section Label
        self.section_lbl = QLabel("WORKSPACE")
        self.section_lbl.setStyleSheet(f"font-size: 9px; font-weight: bold; color: {COLOR_TEXT_MUTED}; padding-left: 20px; padding-top: 10px;")
        layout.addWidget(self.section_lbl)

        # Navigation items
        nav_items = [
            ("overview", "Overview Dashboard", "📊"),
            ("processing", "Video Processing", "🎥"),
            ("incidents", "Incident History", "📋"),
            ("settings", "Settings", "⚙️"),
        ]

        for pid, label, icon in nav_items:
            btn = SidebarButton(pid, label, icon, self)
            btn.setProperty("class", "nav_btn")
            btn.clicked.connect(lambda checked, p=pid: self._on_btn_clicked(p))
            layout.addWidget(btn)
            self.buttons[pid] = btn

        layout.addStretch()

        # Footer Status Card
        self.footer_widget = QWidget()
        footer_layout = QHBoxLayout(self.footer_widget)
        footer_layout.setContentsMargins(16, 10, 16, 0)

        dot = QLabel("●")
        dot.setStyleSheet(f"color: {COLOR_SUCCESS}; font-size: 12px;")
        footer_layout.addWidget(dot)

        self.footer_text_box = QWidget()
        ft_layout = QVBoxLayout(self.footer_text_box)
        ft_layout.setContentsMargins(6, 0, 0, 0)
        ft_layout.setSpacing(0)

        status_lbl = QLabel("Active SQLite DB")
        status_lbl.setStyleSheet(f"font-size: 11px; font-weight: bold; color: {COLOR_TEXT_PRIMARY};")
        db_lbl = QLabel("cheating_system.db")
        db_lbl.setStyleSheet(f"font-size: 9px; color: {COLOR_TEXT_MUTED};")
        ft_layout.addWidget(status_lbl)
        ft_layout.addWidget(db_lbl)
        footer_layout.addWidget(self.footer_text_box)

        layout.addWidget(self.footer_widget)

    def toggle_collapse(self) -> None:
        """Toggle between full 240px and compact 64px width."""
        self.is_collapsed = not self.is_collapsed
        if self.is_collapsed:
            self.setFixedWidth(64)
            self.brand_box.hide()
            self.section_lbl.hide()
            self.footer_text_box.hide()
        else:
            self.setFixedWidth(240)
            self.brand_box.show()
            self.section_lbl.show()
            self.footer_text_box.show()

        for btn in self.buttons.values():
            btn.set_collapsed(self.is_collapsed)

    def set_active(self, page_id: str) -> None:
        """Set the active page button highlight."""
        for pid, btn in self.buttons.items():
            btn.setChecked(pid == page_id)

    def _on_btn_clicked(self, page_id: str) -> None:
        self.set_active(page_id)
        self.page_changed.emit(page_id)
