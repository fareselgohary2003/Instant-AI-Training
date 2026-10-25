"""
Tests for visual overlay rendering and color coding (Requirement D).
"""

from __future__ import annotations

import numpy as np
import pytest

from core.association import DetectionBox
from core.visualizer import (
    COLOR_NORMAL_PERSON,
    COLOR_PHONE,
    COLOR_REVIEW_REQUIRED,
    annotate_frame,
)


def test_annotate_frame_normal_and_review_colors():
    """Verify that normally tracked students and review-required students are distinctly rendered."""
    blank_frame = np.zeros((480, 640, 3), dtype=np.uint8)

    normal_person = DetectionBox(x1=50, y1=50, x2=150, y2=250, conf=0.9, class_id=0, track_id=1)
    review_person = DetectionBox(x1=300, y1=50, x2=400, y2=250, conf=0.9, class_id=0, track_id=2)
    phone = DetectionBox(x1=330, y1=150, x2=360, y2=190, conf=0.85, class_id=67)

    review_set = {2}  # Person 2 is flagged

    annotated = annotate_frame(
        frame=blank_frame,
        person_boxes=[normal_person, review_person],
        phone_boxes=[phone],
        review_track_ids=review_set,
        frame_number=1,
        total_frames=100,
        fps=25.0,
        incidents_count=1,
    )

    assert annotated.shape == blank_frame.shape
    assert annotated.dtype == np.uint8

    # The frame should contain green pixels (normal person), red pixels (review person), and orange pixels (phone)
    # Check green color presence
    assert np.any(
        (annotated[:, :, 0] == COLOR_NORMAL_PERSON[0])
        & (annotated[:, :, 1] == COLOR_NORMAL_PERSON[1])
        & (annotated[:, :, 2] == COLOR_NORMAL_PERSON[2])
    )

    # Check red color presence
    assert np.any(
        (annotated[:, :, 0] == COLOR_REVIEW_REQUIRED[0])
        & (annotated[:, :, 1] == COLOR_REVIEW_REQUIRED[1])
        & (annotated[:, :, 2] == COLOR_REVIEW_REQUIRED[2])
    )

    # Check phone orange color presence
    assert np.any(
        (annotated[:, :, 0] == COLOR_PHONE[0])
        & (annotated[:, :, 1] == COLOR_PHONE[1])
        & (annotated[:, :, 2] == COLOR_PHONE[2])
    )
