"""
Incident Detail and Review view for ExamGuard.
Allows inspection of high-resolution evidence screenshots, observation logging,
and status determination (pending, reviewed, dismissed).
"""

from __future__ import annotations

import os
import subprocess
import sys
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk
from typing import Callable, Optional

from PIL import Image, ImageTk

from config import BASE_DIR
from database import get_incident, update_incident_review
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


class ReviewView(tk.Frame):
    """
    Detailed evidence review panel for individual incidents.
    """

    def __init__(
        self,
        parent: tk.Widget,
        on_back: Callable[[], None],
        on_review_saved: Optional[Callable[[], None]] = None,
        **kwargs,
    ):
        super().__init__(parent, bg=COLOR_CONTENT_BG, **kwargs)
        self.on_back = on_back
        self.on_review_saved = on_review_saved

        self.current_incident_id: Optional[int] = None
        self.current_incident_data: Optional[dict] = None
        self._current_photo: Optional[ImageTk.PhotoImage] = None

        self._build_ui()

    def _build_ui(self) -> None:
        # Header
        header = tk.Frame(self, bg=COLOR_CONTENT_BG)
        header.pack(fill="x", padx=24, pady=(20, 14))

        back_btn = ttk.Button(
            header,
            text="← Back to List",
            style="Secondary.TButton",
            command=self.on_back,
            cursor="hand2",
        )
        back_btn.pack(side="left", padx=(0, 16))

        title_frame = tk.Frame(header, bg=COLOR_CONTENT_BG)
        title_frame.pack(side="left")

        self.title_lbl = tk.Label(
            title_frame,
            text="Incident Evidence Review",
            font=FONT_TITLE,
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_CONTENT_BG,
        )
        self.title_lbl.pack(anchor="w")

        self.sub_lbl = tk.Label(
            title_frame,
            text="Verify the AI-flagged frame and record your disciplinary observation objectively.",
            font=FONT_BODY,
            fg=COLOR_TEXT_MUTED,
            bg=COLOR_CONTENT_BG,
        )
        self.sub_lbl.pack(anchor="w")

        # Two-column layout container
        content = tk.Frame(self, bg=COLOR_CONTENT_BG)
        content.pack(fill="both", expand=True, padx=24, pady=(0, 20))
        content.columnconfigure(0, weight=6)  # Evidence screenshot (left)
        content.columnconfigure(1, weight=4)  # Decision form & metadata (right)

        # 1. Left: Evidence Screenshot Card
        self.evidence_card = tk.Frame(
            content,
            bg=COLOR_CARD_BG,
            highlightthickness=1,
            highlightbackground=COLOR_CARD_BORDER,
            padx=18,
            pady=16,
        )
        self.evidence_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        img_top = tk.Frame(self.evidence_card, bg=COLOR_CARD_BG)
        img_top.pack(fill="x", pady=(0, 8))

        lbl_img_heading = tk.Label(
            img_top,
            text="Captured Evidence Frame",
            font=FONT_HEADING,
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_CARD_BG,
        )
        lbl_img_heading.pack(side="left")

        self.open_external_btn = tk.Button(
            img_top,
            text="🔍 Open Full Image",
            font=FONT_SMALL,
            bg="#EFF6FF",
            fg=COLOR_PRIMARY,
            relief="flat",
            padx=10,
            pady=3,
            cursor="hand2",
            command=self._open_in_system_viewer,
        )
        self.open_external_btn.pack(side="right")

        # Canvas for image
        self.image_canvas = tk.Canvas(
            self.evidence_card,
            bg="#0F172A",
            highlightthickness=0,
            height=380,
        )
        self.image_canvas.pack(fill="both", expand=True)

        self.no_image_lbl = self.image_canvas.create_text(
            260,
            190,
            text="No incident selected",
            font=FONT_BODY,
            fill="#94A3B8",
        )

        # 2. Right: Metadata and Decision Form Card
        self.form_card = tk.Frame(
            content,
            bg=COLOR_CARD_BG,
            highlightthickness=1,
            highlightbackground=COLOR_CARD_BORDER,
            padx=20,
            pady=16,
        )
        self.form_card.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        form_title = tk.Label(
            self.form_card,
            text="Incident Metadata & Decision",
            font=FONT_HEADING,
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_CARD_BG,
        )
        form_title.pack(anchor="w", pady=(0, 10))

        # Metadata grid
        meta_grid = tk.Frame(self.form_card, bg="#F8FAFC", padx=12, pady=10)
        meta_grid.pack(fill="x", pady=(0, 14))
        meta_grid.columnconfigure((0, 1), weight=1)

        self.lbl_meta_id = self._add_meta_row(meta_grid, 0, "Incident ID", "—")
        self.lbl_meta_track = self._add_meta_row(meta_grid, 1, "Track ID", "—")
        self.lbl_meta_conf = self._add_meta_row(meta_grid, 2, "Model Confidence", "—")
        self.lbl_meta_time = self._add_meta_row(meta_grid, 3, "Captured At", "—")
        self.lbl_meta_video = self._add_meta_row(meta_grid, 4, "Source Video", "—")
        self.lbl_meta_frame = self._add_meta_row(meta_grid, 5, "Frame #", "—")

        # Status Radio buttons
        status_lbl = tk.Label(
            self.form_card,
            text="Review Decision:",
            font=FONT_BODY_BOLD,
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_CARD_BG,
        )
        status_lbl.pack(anchor="w", pady=(4, 4))

        status_box = tk.Frame(self.form_card, bg=COLOR_CARD_BG)
        status_box.pack(fill="x", pady=(0, 10))

        self.status_var = tk.StringVar(value="pending")
        for val, text, tone in [
            ("pending", "⏳ Pending", COLOR_WARNING),
            ("reviewed", "✓ Reviewed (Misconduct)", COLOR_SUCCESS),
            ("dismissed", "✕ Dismissed (False Flag)", COLOR_DANGER),
        ]:
            rb = tk.Radiobutton(
                status_box,
                text=text,
                value=val,
                variable=self.status_var,
                font=FONT_BODY,
                fg=COLOR_TEXT_PRIMARY,
                bg=COLOR_CARD_BG,
                activebackground=COLOR_CARD_BG,
                selectcolor="#FFFFFF",
            )
            rb.pack(anchor="w", pady=2)

        # Notes area
        notes_lbl = tk.Label(
            self.form_card,
            text="Reviewer Observations / Notes:",
            font=FONT_BODY_BOLD,
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_CARD_BG,
        )
        notes_lbl.pack(anchor="w", pady=(6, 4))

        self.notes_text = tk.Text(
            self.form_card,
            font=FONT_BODY,
            height=5,
            relief="solid",
            bd=1,
            wrap="word",
        )
        self.notes_text.pack(fill="x", pady=(0, 12))

        # Disclaimer
        disclaimer = tk.Label(
            self.form_card,
            text="⚠ AI detections are review signals, not proof of cheating. Final decisions must be made by a human reviewer.",
            font=FONT_SMALL,
            fg=COLOR_TEXT_MUTED,
            bg=COLOR_CARD_BG,
            justify="left",
            wraplength=340,
        )
        disclaimer.pack(fill="x", pady=(0, 14))

        # Save Action Button
        self.save_btn = tk.Button(
            self.form_card,
            text="💾 Save Review Decision",
            font=FONT_BODY_BOLD,
            bg=COLOR_PRIMARY,
            fg="#FFFFFF",
            activebackground="#1D4ED8",
            activeforeground="#FFFFFF",
            relief="flat",
            padx=16,
            pady=8,
            cursor="hand2",
            command=self._save_review,
        )
        self.save_btn.pack(fill="x")

    def _add_meta_row(self, parent: tk.Widget, row: int, label: str, init_val: str) -> tk.Label:
        lbl_k = tk.Label(
            parent,
            text=label + ":",
            font=FONT_SMALL,
            fg=COLOR_TEXT_MUTED,
            bg="#F8FAFC",
            anchor="w",
        )
        lbl_k.grid(row=row, column=0, sticky="w", pady=2)

        lbl_v = tk.Label(
            parent,
            text=init_val,
            font=FONT_BODY_BOLD,
            fg=COLOR_TEXT_PRIMARY,
            bg="#F8FAFC",
            anchor="w",
        )
        lbl_v.grid(row=row, column=1, sticky="w", pady=2, padx=(8, 0))
        return lbl_v

    def load_incident(self, incident_id: int) -> None:
        """Load and display incident details by ID."""
        self.current_incident_id = incident_id
        row = get_incident(incident_id)

        if not row:
            messagebox.showerror("Error", f"Incident #{incident_id} not found.")
            return

        self.current_incident_data = dict(row)
        data = self.current_incident_data

        # Populate header & meta
        self.title_lbl.config(text=f"Incident #{data['id']} Evidence Review")
        self.lbl_meta_id.config(text=f"#{data['id']}")
        self.lbl_meta_track.config(
            text=f"Student #{data['track_id']}" if data["track_id"] is not None else "Unassigned"
        )
        self.lbl_meta_conf.config(
            text=f"{data['confidence']:.1%}" if data["confidence"] is not None else "—"
        )
        self.lbl_meta_time.config(text=data["timestamp"].replace("T", " ")[:19])
        self.lbl_meta_video.config(text=str(data.get("source_video") or "—"))
        self.lbl_meta_frame.config(text=str(data.get("frame_number") or "—"))

        # Populate form
        self.status_var.set(data.get("review_status", "pending"))
        self.notes_text.delete("1.0", "end")
        if data.get("notes"):
            self.notes_text.insert("1.0", data["notes"])

        # Display image
        self._display_screenshot(data.get("screenshot_path"))

    def _display_screenshot(self, screenshot_path: Optional[str]) -> None:
        """Render screenshot on canvas."""
        self.image_canvas.delete("all")

        if not screenshot_path:
            self.image_canvas.create_text(
                260, 190, text="No screenshot recorded for this incident.", font=FONT_BODY, fill="#94A3B8"
            )
            return

        path = Path(screenshot_path)
        if not path.is_absolute():
            path = BASE_DIR / path

        if not path.is_file():
            self.image_canvas.create_text(
                260, 190, text=f"Screenshot file missing on disk:\n{path.name}", font=FONT_BODY, fill="#EF4444"
            )
            return

        try:
            pil_img = Image.open(path)
            c_w = self.image_canvas.winfo_width()
            c_h = self.image_canvas.winfo_height()
            if c_w < 50 or c_h < 50:
                c_w, c_h = 520, 380

            scale = min(c_w / pil_img.width, c_h / pil_img.height)
            new_w = max(1, int(pil_img.width * scale))
            new_h = max(1, int(pil_img.height * scale))

            resized = pil_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            self._current_photo = ImageTk.PhotoImage(resized)

            self.image_canvas.create_image(c_w / 2, c_h / 2, image=self._current_photo, anchor="center")
        except Exception as e:
            self.image_canvas.create_text(
                260, 190, text=f"Failed to load image:\n{e}", font=FONT_BODY, fill="#EF4444"
            )

    def _save_review(self) -> None:
        if not self.current_incident_id:
            return

        status = self.status_var.get()
        notes = self.notes_text.get("1.0", "end").strip()

        try:
            success = update_incident_review(
                incident_id=self.current_incident_id,
                review_status=status,
                notes=notes,
            )

            if success:
                messagebox.showinfo("Success", f"Review for Incident #{self.current_incident_id} saved successfully.")
                if self.on_review_saved:
                    self.on_review_saved()
            else:
                messagebox.showerror("Error", "Could not update incident record.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save review: {e}")

    def _open_in_system_viewer(self) -> None:
        if not self.current_incident_data:
            return

        raw_path = self.current_incident_data.get("screenshot_path")
        if not raw_path:
            messagebox.showwarning("No Screenshot", "No screenshot file recorded for this incident.")
            return

        path = Path(raw_path)
        if not path.is_absolute():
            path = (BASE_DIR / path).resolve()

        if not path.is_file():
            messagebox.showerror("File Missing", f"Image file not found on disk:\n{path}")
            return

        if sys.platform.startswith("win"):
            os.startfile(str(path))
        else:
            subprocess.Popen(["xdg-open", str(path)])
