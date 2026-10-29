"""
Settings view for ExamGuard PySide6 Application.
Manages model weights path, confidence thresholds, hardware acceleration,
and directory preferences.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from config import DEFAULT_CONFIG, load_config, save_config
from core.engine import torch_cuda_available
from desktop_qt.theme import (
    COLOR_BORDER,
    COLOR_PRIMARY,
    COLOR_SUCCESS,
    COLOR_SURFACE,
    COLOR_SURFACE_ALT,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
)


class SettingsView(QWidget):
    """
    Application settings and preference manager.
    """

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.config_data: Dict[str, Any] = load_config()

        self._build_ui()
        self._load_config_values()

    def _build_ui(self) -> None:
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        scroll.setWidget(content)

        layout = QVBoxLayout(content)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(18)

        # Header
        header = QWidget()
        h_layout = QVBoxLayout(header)
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(2)

        eyebrow = QLabel("EXAMGUARD / SYSTEM CONFIGURATION")
        eyebrow.setStyleSheet(f"font-size: 11px; font-weight: bold; color: {COLOR_PRIMARY};")
        title = QLabel("System Settings & Thresholds")
        title.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {COLOR_TEXT_PRIMARY};")
        subtitle = QLabel("Configure AI detection sensitivities, tracking parameters, hardware device, and storage directories.")
        subtitle.setStyleSheet(f"font-size: 12px; color: {COLOR_TEXT_MUTED};")

        h_layout.addWidget(eyebrow)
        h_layout.addWidget(title)
        h_layout.addWidget(subtitle)
        layout.addWidget(header)

        # 1. Model & Hardware Card
        card_model = self._create_card("AI Model & Inference Hardware")
        cm_layout = QVBoxLayout(card_model)
        cm_layout.setContentsMargins(20, 18, 20, 18)
        cm_layout.setSpacing(10)

        lbl_weights = QLabel("YOLO Model Weights Path (.pt):")
        lbl_weights.setStyleSheet(f"font-weight: bold; color: {COLOR_TEXT_PRIMARY};")
        cm_layout.addWidget(lbl_weights)

        row_w = QWidget()
        rw_layout = QHBoxLayout(row_w)
        rw_layout.setContentsMargins(0, 0, 0, 0)

        self.model_path_edit = QLineEdit()
        rw_layout.addWidget(self.model_path_edit, stretch=1)

        browse_model_btn = QPushButton("Browse...")
        browse_model_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        browse_model_btn.clicked.connect(self._browse_model_path)
        rw_layout.addWidget(browse_model_btn)
        cm_layout.addWidget(row_w)

        test_row = QWidget()
        tr_layout = QHBoxLayout(test_row)
        tr_layout.setContentsMargins(0, 0, 0, 0)

        verify_btn = QPushButton("⚡  Verify Model Weights")
        verify_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        verify_btn.clicked.connect(self._verify_model)
        tr_layout.addWidget(verify_btn)
        tr_layout.addStretch()
        cm_layout.addWidget(test_row)

        cuda_avail = torch_cuda_available()
        cuda_txt = "CUDA GPU Acceleration Available" if cuda_avail else "No CUDA GPU Detected (CPU Mode Active)"
        lbl_dev = QLabel(f"Hardware Compute Device ({cuda_txt}):")
        lbl_dev.setStyleSheet(f"font-weight: bold; color: {COLOR_TEXT_PRIMARY}; margin-top: 6px;")
        cm_layout.addWidget(lbl_dev)

        dev_row = QWidget()
        dr_layout = QHBoxLayout(dev_row)
        dr_layout.setContentsMargins(0, 0, 0, 0)

        self.rb_cpu = QRadioButton("CPU (Cross-platform standard)")
        self.rb_cuda = QRadioButton("CUDA GPU (NVIDIA Acceleration)")
        self.rb_cuda.setEnabled(cuda_avail)
        dr_layout.addWidget(self.rb_cpu)
        dr_layout.addWidget(self.rb_cuda)
        dr_layout.addStretch()
        cm_layout.addWidget(dev_row)

        layout.addWidget(card_model)

        # 2. Thresholds Card
        card_thresh = self._create_card("Detection & Spatial Tracking Parameters")
        ct_layout = QVBoxLayout(card_thresh)
        ct_layout.setContentsMargins(20, 18, 20, 18)
        ct_layout.setSpacing(14)

        # Confidence slider
        self.slider_conf, self.lbl_conf_val = self._add_slider_component(
            ct_layout,
            "Detection Confidence Threshold:",
            "Lower values increase phone detection sensitivity; higher values decrease false flags.",
            10, 90, 25,
            lambda v: f"{v / 100:.2f} ({v}%)",
        )

        # Cooldown slider
        self.slider_cooldown, self.lbl_cooldown_val = self._add_slider_component(
            ct_layout,
            "Event Alert Cooldown (Seconds):",
            "Suppresses repeated duplicate incident captures for continuous detections within this interval.",
            1, 30, 5,
            lambda v: f"{v:.1f} seconds",
        )

        # Proximity slider
        self.slider_prox, self.lbl_prox_val = self._add_slider_component(
            ct_layout,
            "Spatial Association Proximity Ratio:",
            "Ratio of student bounding box size used to associate nearby phones with student tracks.",
            20, 150, 60,
            lambda v: f"{v / 100:.2f}x",
        )

        layout.addWidget(card_thresh)

        # 3. Directories & Alerts Card
        card_dirs = self._create_card("Storage Directories & Alert Notification Preferences")
        cd_layout = QVBoxLayout(card_dirs)
        cd_layout.setContentsMargins(20, 18, 20, 18)
        cd_layout.setSpacing(12)

        self.alerts_dir_edit = self._add_dir_row(cd_layout, "Evidence Screenshots Output Directory:")
        self.outputs_dir_edit = self._add_dir_row(cd_layout, "Annotated Processed Videos Directory:")

        self.cb_sound = QCheckBox("Play non-blocking audio alert chime when an incident is logged")
        cd_layout.addWidget(self.cb_sound)

        layout.addWidget(card_dirs)

        # Action Buttons
        btn_bar = QWidget()
        bb_layout = QHBoxLayout(btn_bar)
        bb_layout.setContentsMargins(0, 0, 0, 0)
        bb_layout.setSpacing(12)

        save_btn = QPushButton("💾  Save Application Settings")
        save_btn.setProperty("class", "primary")
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.clicked.connect(self._save_settings)
        bb_layout.addWidget(save_btn)

        reset_btn = QPushButton("Reset to Defaults")
        reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        reset_btn.clicked.connect(self._reset_defaults)
        bb_layout.addWidget(reset_btn)

        bb_layout.addStretch()
        layout.addWidget(btn_bar)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def _create_card(self, title: str) -> QFrame:
        card = QFrame()
        card.setProperty("class", "card")
        card_lbl = QLabel(title)
        card_lbl.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {COLOR_TEXT_PRIMARY}; padding: 16px 20px 0 20px;")
        return card

    def _add_slider_component(self, parent_layout: QVBoxLayout, label: str, desc: str, min_v: int, max_v: int, init_v: int, fmt_fn: Any) -> tuple[QSlider, QLabel]:
        top = QWidget()
        t_layout = QHBoxLayout(top)
        t_layout.setContentsMargins(0, 0, 0, 0)

        lbl = QLabel(label)
        lbl.setStyleSheet(f"font-weight: bold; color: {COLOR_TEXT_PRIMARY};")
        val_lbl = QLabel(fmt_fn(init_v))
        val_lbl.setStyleSheet(f"font-weight: bold; color: {COLOR_PRIMARY};")
        t_layout.addWidget(lbl)
        t_layout.addStretch()
        t_layout.addWidget(val_lbl)
        parent_layout.addWidget(top)

        sub = QLabel(desc)
        sub.setStyleSheet(f"font-size: 11px; color: {COLOR_TEXT_MUTED};")
        parent_layout.addWidget(sub)

        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(min_v, max_v)
        slider.setValue(init_v)
        slider.valueChanged.connect(lambda val: val_lbl.setText(fmt_fn(val)))
        parent_layout.addWidget(slider)

        return slider, val_lbl

    def _add_dir_row(self, parent_layout: QVBoxLayout, label: str) -> QLineEdit:
        lbl = QLabel(label)
        lbl.setStyleSheet(f"font-weight: bold; color: {COLOR_TEXT_PRIMARY};")
        parent_layout.addWidget(lbl)

        row = QWidget()
        r_layout = QHBoxLayout(row)
        r_layout.setContentsMargins(0, 0, 0, 0)

        edit = QLineEdit()
        r_layout.addWidget(edit, stretch=1)

        btn = QPushButton("Browse...")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(lambda: self._browse_dir(edit))
        r_layout.addWidget(btn)

        parent_layout.addWidget(row)
        return edit

    def _browse_dir(self, edit: QLineEdit) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Select Directory", edit.text())
        if folder:
            edit.setText(folder)

    def _browse_model_path(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Select YOLO Model Weights", "", "PyTorch Weights (*.pt);;All Files (*.*)")
        if path:
            self.model_path_edit.setText(path)

    def _load_config_values(self) -> None:
        cfg = self.config_data
        self.model_path_edit.setText(cfg.get("model_path", ""))
        dev = cfg.get("device", "cpu")
        if dev == "cuda" and torch_cuda_available():
            self.rb_cuda.setChecked(True)
        else:
            self.rb_cpu.setChecked(True)

        conf_pct = int(cfg.get("confidence_threshold", 0.25) * 100)
        self.slider_conf.setValue(conf_pct)

        cooldown = int(cfg.get("cooldown_seconds", 5.0))
        self.slider_cooldown.setValue(cooldown)

        prox = int(cfg.get("proximity_threshold_ratio", 0.6) * 100)
        self.slider_prox.setValue(prox)

        self.alerts_dir_edit.setText(cfg.get("alerts_dir", ""))
        self.outputs_dir_edit.setText(cfg.get("outputs_dir", ""))
        self.cb_sound.setChecked(cfg.get("sound_alerts", True))

    def _verify_model(self) -> None:
        p = Path(self.model_path_edit.text())
        if not p.is_file():
            QMessageBox.critical(self, "Missing Model", f"Model weights file not found on disk at:\n{p}")
            return

        try:
            from ultralytics import YOLO
            m = YOLO(str(p))
            class_count = len(m.names) if hasattr(m, "names") else "Unknown"
            QMessageBox.information(
                self,
                "Model Verified",
                f"Successfully loaded YOLO weights from:\n{p.name}\n\nClasses recognized: {class_count}",
            )
        except Exception as e:
            QMessageBox.critical(self, "Load Error", f"Failed to load weights:\n{e}")

    def _save_settings(self) -> None:
        new_cfg = {
            "model_path": self.model_path_edit.text().strip(),
            "device": "cuda" if self.rb_cuda.isChecked() else "cpu",
            "confidence_threshold": round(self.slider_conf.value() / 100.0, 2),
            "cooldown_seconds": round(float(self.slider_cooldown.value()), 1),
            "proximity_threshold_ratio": round(self.slider_prox.value() / 100.0, 2),
            "alerts_dir": self.alerts_dir_edit.text().strip(),
            "outputs_dir": self.outputs_dir_edit.text().strip(),
            "sound_alerts": self.cb_sound.isChecked(),
        }

        if save_config(new_cfg):
            self.config_data = load_config()
            QMessageBox.information(self, "Saved", "Settings successfully written to config.json.")
        else:
            QMessageBox.critical(self, "Error", "Could not write configuration file.")

    def _reset_defaults(self) -> None:
        reply = QMessageBox.question(self, "Reset", "Reset all settings to factory default values?")
        if reply == QMessageBox.StandardButton.Yes:
            self.config_data = dict(DEFAULT_CONFIG)
            self._load_config_values()
