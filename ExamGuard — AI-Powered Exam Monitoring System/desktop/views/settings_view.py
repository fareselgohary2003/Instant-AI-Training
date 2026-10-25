"""
Settings view for ExamGuard.
Allows configuring model paths, inference thresholds, hardware acceleration,
output directories, and alert preferences.
"""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Any, Dict

from config import DEFAULT_CONFIG, load_config, save_config
from core.engine import torch_cuda_available
from desktop.theme import (
    COLOR_CARD_BG,
    COLOR_CARD_BORDER,
    COLOR_CONTENT_BG,
    COLOR_PRIMARY,
    COLOR_SUCCESS,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    FONT_BODY,
    FONT_BODY_BOLD,
    FONT_HEADING,
    FONT_MONO,
    FONT_SMALL,
    FONT_TITLE,
)


class SettingsView(tk.Frame):
    """
    Settings and system preferences view.
    """

    def __init__(self, parent: tk.Widget, **kwargs):
        super().__init__(parent, bg=COLOR_CONTENT_BG, **kwargs)
        self.config_data: Dict[str, Any] = load_config()

        self._build_ui()
        self._load_values()

    def _build_ui(self) -> None:
        header = tk.Frame(self, bg=COLOR_CONTENT_BG)
        header.pack(fill="x", padx=24, pady=(20, 16))

        eyebrow = tk.Label(
            header,
            text="EXAMGUARD / CONFIGURATION",
            font=FONT_SMALL,
            fg=COLOR_PRIMARY,
            bg=COLOR_CONTENT_BG,
        )
        eyebrow.pack(anchor="w")

        title = tk.Label(
            header,
            text="Application Settings",
            font=FONT_TITLE,
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_CONTENT_BG,
        )
        title.pack(anchor="w")

        subtitle = tk.Label(
            header,
            text="Configure AI detection thresholds, tracking parameters, storage directories, and alerts.",
            font=FONT_BODY,
            fg=COLOR_TEXT_MUTED,
            bg=COLOR_CONTENT_BG,
        )
        subtitle.pack(anchor="w")

        # Scrollable settings container
        canvas = tk.Canvas(self, bg=COLOR_CONTENT_BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        scroll_content = tk.Frame(canvas, bg=COLOR_CONTENT_BG)

        scroll_content.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas_window = canvas.create_window((0, 0), window=scroll_content, anchor="nw")
        canvas.bind(
            "<Configure>",
            lambda e: canvas.itemconfig(canvas_window, width=e.width),
        )
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 1. Model & Device Card
        model_card = self._create_card(scroll_content, "AI Model & Hardware Acceleration")

        self.model_path_var = tk.StringVar()
        self._add_file_picker_row(
            model_card,
            "Model Weights Path (YOLO):",
            self.model_path_var,
            filetypes=[("PyTorch Weights", "*.pt"), ("All Files", "*.*")],
        )

        test_row = tk.Frame(model_card, bg=COLOR_CARD_BG)
        test_row.pack(fill="x", pady=(0, 14))

        test_btn = tk.Button(
            test_row,
            text="⚡ Verify Model Loading",
            font=FONT_SMALL,
            bg="#EFF6FF",
            fg=COLOR_PRIMARY,
            relief="flat",
            padx=10,
            pady=4,
            cursor="hand2",
            command=self._test_model_load,
        )
        test_btn.pack(side="left")

        # Device selection
        cuda_avail = torch_cuda_available()
        cuda_status_txt = "CUDA GPU detected" if cuda_avail else "No CUDA GPU detected (CPU mode active)"

        dev_lbl = tk.Label(
            model_card,
            text=f"Inference Device ({cuda_status_txt}):",
            font=FONT_BODY_BOLD,
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_CARD_BG,
        )
        dev_lbl.pack(anchor="w", pady=(4, 2))

        self.device_var = tk.StringVar(value="cpu")
        dev_frame = tk.Frame(model_card, bg=COLOR_CARD_BG)
        dev_frame.pack(fill="x", pady=(0, 12))

        rb_cpu = tk.Radiobutton(
            dev_frame,
            text="CPU (Reliable, Cross-platform)",
            value="cpu",
            variable=self.device_var,
            font=FONT_BODY,
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_CARD_BG,
            selectcolor="#FFFFFF",
        )
        rb_cpu.pack(side="left", padx=(0, 16))

        rb_cuda = tk.Radiobutton(
            dev_frame,
            text="CUDA GPU (Requires NVIDIA driver)",
            value="cuda",
            variable=self.device_var,
            font=FONT_BODY,
            fg=COLOR_TEXT_PRIMARY if cuda_avail else COLOR_TEXT_MUTED,
            bg=COLOR_CARD_BG,
            state="normal" if cuda_avail else "disabled",
            selectcolor="#FFFFFF",
        )
        rb_cuda.pack(side="left")

        # 2. Thresholds Card
        thresh_card = self._create_card(scroll_content, "Detection & Tracking Parameters")

        # Confidence slider
        self.conf_scale_var = tk.DoubleVar(value=0.25)
        self.conf_val_lbl = tk.Label(thresh_card, text="0.25 (25%)", font=FONT_BODY_BOLD, bg=COLOR_CARD_BG)
        self._add_slider_row(
            thresh_card,
            "Detection Confidence Threshold:",
            "Objects detected with confidence below this value are ignored.",
            self.conf_scale_var,
            0.10,
            0.90,
            self.conf_val_lbl,
            lambda v: f"{float(v):.2f} ({float(v):.0%})",
        )

        # Cooldown slider
        self.cooldown_scale_var = tk.DoubleVar(value=5.0)
        self.cooldown_val_lbl = tk.Label(thresh_card, text="5.0s", font=FONT_BODY_BOLD, bg=COLOR_CARD_BG)
        self._add_slider_row(
            thresh_card,
            "Incident Alert Cooldown (Seconds):",
            "Prevents duplicate incident records for the same continuous detection within this duration.",
            self.cooldown_scale_var,
            1.0,
            30.0,
            self.cooldown_val_lbl,
            lambda v: f"{float(v):.1f} seconds",
        )

        # Proximity ratio slider
        self.proximity_scale_var = tk.DoubleVar(value=0.6)
        self.proximity_val_lbl = tk.Label(thresh_card, text="0.60x", font=FONT_BODY_BOLD, bg=COLOR_CARD_BG)
        self._add_slider_row(
            thresh_card,
            "Spatial Association Proximity Ratio:",
            "Multiplier of student bounding box size used for proximity association heuristic.",
            self.proximity_scale_var,
            0.2,
            1.5,
            self.proximity_val_lbl,
            lambda v: f"{float(v):.2f}x",
        )

        # 3. Directories & Alerts Card
        storage_card = self._create_card(scroll_content, "Storage Directories & Preferences")

        self.alerts_dir_var = tk.StringVar()
        self._add_dir_picker_row(
            storage_card,
            "Evidence Screenshots Directory:",
            self.alerts_dir_var,
        )

        self.outputs_dir_var = tk.StringVar()
        self._add_dir_picker_row(
            storage_card,
            "Processed Videos Output Directory:",
            self.outputs_dir_var,
        )

        self.sound_alert_var = tk.BooleanVar(value=True)
        cb_sound = tk.Checkbutton(
            storage_card,
            text="Play audio chime when a suspicious incident is detected",
            variable=self.sound_alert_var,
            font=FONT_BODY,
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_CARD_BG,
            selectcolor="#FFFFFF",
        )
        cb_sound.pack(anchor="w", pady=(4, 12))

        # Action Buttons
        btn_row = tk.Frame(scroll_content, bg=COLOR_CONTENT_BG)
        btn_row.pack(fill="x", padx=24, pady=(10, 30))

        save_btn = tk.Button(
            btn_row,
            text="💾 Save Application Settings",
            font=FONT_BODY_BOLD,
            bg=COLOR_PRIMARY,
            fg="#FFFFFF",
            activebackground="#1D4ED8",
            activeforeground="#FFFFFF",
            relief="flat",
            padx=18,
            pady=8,
            cursor="hand2",
            command=self._save_settings,
        )
        save_btn.pack(side="left")

        reset_btn = ttk.Button(
            btn_row,
            text="Reset to Defaults",
            style="Secondary.TButton",
            command=self._reset_defaults,
            cursor="hand2",
        )
        reset_btn.pack(side="left", padx=12)

    def _create_card(self, parent: tk.Widget, title: str) -> tk.Frame:
        card = tk.Frame(
            parent,
            bg=COLOR_CARD_BG,
            highlightthickness=1,
            highlightbackground=COLOR_CARD_BORDER,
            padx=20,
            pady=16,
        )
        card.pack(fill="x", padx=24, pady=(0, 16))

        lbl = tk.Label(
            card,
            text=title,
            font=FONT_HEADING,
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_CARD_BG,
        )
        lbl.pack(anchor="w", pady=(0, 12))
        return card

    def _add_file_picker_row(self, card: tk.Frame, label: str, var: tk.StringVar, filetypes: list) -> None:
        lbl = tk.Label(card, text=label, font=FONT_BODY_BOLD, fg=COLOR_TEXT_PRIMARY, bg=COLOR_CARD_BG)
        lbl.pack(anchor="w", pady=(0, 2))

        row = tk.Frame(card, bg=COLOR_CARD_BG)
        row.pack(fill="x", pady=(0, 10))

        entry = tk.Entry(row, textvariable=var, font=FONT_MONO, relief="solid", bd=1)
        entry.pack(side="left", fill="x", expand=True)

        browse_btn = ttk.Button(
            row,
            text="Browse...",
            style="Secondary.TButton",
            cursor="hand2",
            command=lambda: self._browse_file(var, filetypes),
        )
        browse_btn.pack(side="right", padx=(8, 0))

    def _add_dir_picker_row(self, card: tk.Frame, label: str, var: tk.StringVar) -> None:
        lbl = tk.Label(card, text=label, font=FONT_BODY_BOLD, fg=COLOR_TEXT_PRIMARY, bg=COLOR_CARD_BG)
        lbl.pack(anchor="w", pady=(0, 2))

        row = tk.Frame(card, bg=COLOR_CARD_BG)
        row.pack(fill="x", pady=(0, 10))

        entry = tk.Entry(row, textvariable=var, font=FONT_MONO, relief="solid", bd=1)
        entry.pack(side="left", fill="x", expand=True)

        browse_btn = ttk.Button(
            row,
            text="Browse...",
            style="Secondary.TButton",
            cursor="hand2",
            command=lambda: self._browse_dir(var),
        )
        browse_btn.pack(side="right", padx=(8, 0))

    def _add_slider_row(
        self,
        card: tk.Frame,
        label: str,
        desc: str,
        var: tk.DoubleVar,
        min_v: float,
        max_v: float,
        val_lbl: tk.Label,
        fmt_fn: Any,
    ) -> None:
        top = tk.Frame(card, bg=COLOR_CARD_BG)
        top.pack(fill="x")

        lbl = tk.Label(top, text=label, font=FONT_BODY_BOLD, fg=COLOR_TEXT_PRIMARY, bg=COLOR_CARD_BG)
        lbl.pack(side="left")
        val_lbl.pack(side="right")

        sub = tk.Label(card, text=desc, font=FONT_SMALL, fg=COLOR_TEXT_MUTED, bg=COLOR_CARD_BG)
        sub.pack(anchor="w", pady=(1, 4))

        def on_slide(val_str):
            val_lbl.config(text=fmt_fn(float(val_str)))

        slider = ttk.Scale(
            card,
            from_=min_v,
            to=max_v,
            variable=var,
            orient="horizontal",
            command=on_slide,
        )
        slider.pack(fill="x", pady=(0, 12))

    def _browse_file(self, var: tk.StringVar, filetypes: list) -> None:
        res = filedialog.askopenfilename(filetypes=filetypes)
        if res:
            var.set(res)

    def _browse_dir(self, var: tk.StringVar) -> None:
        res = filedialog.askdirectory()
        if res:
            var.set(res)

    def _load_values(self) -> None:
        cfg = self.config_data
        self.model_path_var.set(cfg.get("model_path", ""))
        self.device_var.set(cfg.get("device", "cpu"))
        self.conf_scale_var.set(cfg.get("confidence_threshold", 0.25))
        self.conf_val_lbl.config(text=f"{self.conf_scale_var.get():.2f} ({self.conf_scale_var.get():.0%})")
        self.cooldown_scale_var.set(cfg.get("cooldown_seconds", 5.0))
        self.cooldown_val_lbl.config(text=f"{self.cooldown_scale_var.get():.1f} seconds")
        self.proximity_scale_var.set(cfg.get("proximity_threshold_ratio", 0.6))
        self.proximity_val_lbl.config(text=f"{self.proximity_scale_var.get():.2f}x")
        self.alerts_dir_var.set(cfg.get("alerts_dir", ""))
        self.outputs_dir_var.set(cfg.get("outputs_dir", ""))
        self.sound_alert_var.set(cfg.get("sound_alerts", True))

    def _test_model_load(self) -> None:
        p = Path(self.model_path_var.get())
        if not p.is_file():
            messagebox.showerror("Model Not Found", f"Model file not found at:\n{p}")
            return

        try:
            from ultralytics import YOLO
            m = YOLO(str(p))
            class_count = len(m.names) if hasattr(m, "names") else "Unknown"
            messagebox.showinfo(
                "Model Verified",
                f"Successfully loaded YOLO weights from:\n{p.name}\n\nClasses recognized: {class_count}",
            )
        except Exception as e:
            messagebox.showerror("Model Load Error", f"Failed to load weights:\n{e}")

    def _save_settings(self) -> None:
        new_cfg = {
            "model_path": self.model_path_var.get().strip(),
            "device": self.device_var.get(),
            "confidence_threshold": round(self.conf_scale_var.get(), 2),
            "cooldown_seconds": round(self.cooldown_scale_var.get(), 1),
            "proximity_threshold_ratio": round(self.proximity_scale_var.get(), 2),
            "alerts_dir": self.alerts_dir_var.get().strip(),
            "outputs_dir": self.outputs_dir_var.get().strip(),
            "sound_alerts": self.sound_alert_var.get(),
        }

        if save_config(new_cfg):
            self.config_data = load_config()
            messagebox.showinfo("Saved", "Settings successfully saved to config.json.")
        else:
            messagebox.showerror("Error", "Could not write settings file.")

    def _reset_defaults(self) -> None:
        if messagebox.askyesno("Reset", "Reset all settings to factory defaults?"):
            self.config_data = dict(DEFAULT_CONFIG)
            self._load_values()
