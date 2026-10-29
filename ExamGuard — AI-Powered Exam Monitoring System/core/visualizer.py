"""
High-contrast, professional visual overlay renderer for ExamGuard video frames.

Rules (per Requirement D):
- Normal tracked people: Green bounding box (BGR: 0, 200, 0)
- Review-required people (associated with suspicious detection): Red bounding box (BGR: 0, 0, 230)
- Suspicious objects (e.g. phone): Orange/Amber bounding box (BGR: 0, 165, 255)
- Text is rendered over a filled badge rectangle to ensure high contrast regardless of video background.
"""

from __future__ import annotations

from typing import List, Optional, Set
import cv2
import numpy as np

from core.association import DetectionBox

# Color definitions (BGR format for OpenCV)
COLOR_NORMAL_PERSON = (40, 190, 40)       # Green
COLOR_REVIEW_REQUIRED = (30, 30, 235)      # Red
COLOR_PHONE = (0, 150, 255)                # Amber / Orange
COLOR_TEXT_WHITE = (255, 255, 255)
COLOR_TEXT_BLACK = (20, 20, 20)
COLOR_HUD_BG = (25, 20, 20)


def draw_badge(
    image: np.ndarray,
    text: str,
    x: int,
    y: int,
    bg_color: tuple[int, int, int],
    text_color: tuple[int, int, int] = COLOR_TEXT_WHITE,
    font_scale: float = 0.52,
    thickness: int = 1,
) -> None:
    """Draw a text badge with a solid background rectangle for maximum legibility."""
    font = cv2.FONT_HERSHEY_SIMPLEX
    (text_w, text_h), baseline = cv2.getTextSize(text, font, font_scale, thickness)

    # Position badge above (x, y) if space permits, otherwise below
    pad = 4
    if y - text_h - 2 * pad < 0:
        box_top = y
        box_bottom = y + text_h + 2 * pad
        text_y = box_top + text_h + pad
    else:
        box_top = y - text_h - 2 * pad
        box_bottom = y
        text_y = box_bottom - pad

    box_left = max(0, x)
    box_right = min(image.shape[1], x + text_w + 2 * pad)

    cv2.rectangle(image, (box_left, box_top), (box_right, box_bottom), bg_color, -1)
    cv2.putText(
        image,
        text,
        (box_left + pad, text_y),
        font,
        font_scale,
        text_color,
        thickness,
        cv2.LINE_AA,
    )


def draw_hud(
    frame: np.ndarray,
    frame_number: int,
    total_frames: int,
    fps: float,
    people_count: int,
    incidents_count: int,
) -> None:
    """Draw a subtle top status HUD bar with processing statistics."""
    hud_h = 32
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (frame.shape[1], hud_h), COLOR_HUD_BG, -1)
    cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)

    info_text = (
        f"ExamGuard | Frame: {frame_number}/{total_frames} | "
        f"FPS: {fps:.1f} | People Tracked: {people_count} | Incidents: {incidents_count}"
    )
    cv2.putText(
        frame,
        info_text,
        (12, 21),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.52,
        (230, 240, 255),
        1,
        cv2.LINE_AA,
    )


def annotate_frame(
    frame: np.ndarray,
    person_boxes: List[DetectionBox],
    phone_boxes: List[DetectionBox],
    review_track_ids: Set[int],
    frame_number: int = 0,
    total_frames: int = 0,
    fps: float = 0.0,
    incidents_count: int = 0,
    show_hud: bool = True,
    review_reasons: Optional[dict] = None,
) -> np.ndarray:
    """
    Annotate a frame with color-coded bounding boxes and badges according to ExamGuard rules.

    Args:
        frame: BGR numpy image frame.
        person_boxes: List of person detections.
        phone_boxes: List of cell phone / suspicious object detections.
        review_track_ids: Set of person track IDs associated with suspicious events.
        frame_number: Current frame index.
        total_frames: Total video frames.
        fps: Processing FPS.
        incidents_count: Total cumulative incidents recorded.
        show_hud: Whether to render the top info HUD banner.
        review_reasons: Optional mapping of track_id to specific reason (e.g. 'PEEKING', 'PHONE').

    Returns:
        Annotated BGR numpy frame.
    """
    annotated = frame.copy()

    # 1. Draw Person Bounding Boxes
    for person in person_boxes:
        x1, y1, x2, y2 = int(person.x1), int(person.y1), int(person.x2), int(person.y2)
        track_id = person.track_id

        is_review_req = track_id is not None and track_id in review_track_ids

        if is_review_req:
            box_color = COLOR_REVIEW_REQUIRED
            reason_str = ""
            if review_reasons and track_id is not None and track_id in review_reasons:
                reason_str = f" [{review_reasons[track_id]}]"
            label = f"CHEATING / REVIEW: #{track_id}{reason_str}" if track_id is not None else f"CHEATING{reason_str}"
            thickness = 3
        else:
            box_color = COLOR_NORMAL_PERSON
            label = f"Student #{track_id}" if track_id is not None else "Student"
            thickness = 2

        cv2.rectangle(annotated, (x1, y1), (x2, y2), box_color, thickness)
        draw_badge(annotated, label, x1, y1, box_color, COLOR_TEXT_WHITE)

    # 2. Draw Suspicious Object Bounding Boxes (Phone, Notes, Laptop)
    for obj in phone_boxes:
        px1, py1, px2, py2 = int(obj.x1), int(obj.y1), int(obj.x2), int(obj.y2)
        obj_color = COLOR_PHONE
        cv2.rectangle(annotated, (px1, py1), (px2, py2), obj_color, 2)
        obj_name = obj.label if obj.label else "Phone"
        obj_label = f"{obj_name} {obj.conf:.0%}"
        draw_badge(annotated, obj_label, px1, py1, obj_color, COLOR_TEXT_WHITE)

    # 3. Draw Top HUD
    if show_hud and total_frames > 0:
        draw_hud(
            annotated,
            frame_number=frame_number,
            total_frames=total_frames,
            fps=fps,
            people_count=len(person_boxes),
            incidents_count=incidents_count,
        )

    return annotated
