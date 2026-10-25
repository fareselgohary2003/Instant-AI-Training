"""
Tests for spatial association heuristics (Requirement D).
Tests unambiguous containment, near-boundary proximity, overlapping ambiguity, and unassigned objects.
"""

from __future__ import annotations

import pytest
from core.association import DetectionBox, associate_phone_to_person


def test_direct_containment_single_person():
    """When phone center is inside a single person's box, associate with that person's track ID."""
    person1 = DetectionBox(x1=100, y1=100, x2=300, y2=500, conf=0.9, class_id=0, track_id=1)
    person2 = DetectionBox(x1=500, y1=100, x2=700, y2=500, conf=0.9, class_id=0, track_id=2)

    # Phone is in the lap of person 1
    phone = DetectionBox(x1=180, y1=300, x2=220, y2=360, conf=0.85, class_id=67, track_id=10)

    associated_id = associate_phone_to_person(phone, [person1, person2])
    assert associated_id == 1


def test_near_boundary_proximity():
    """When phone is outside the person box but within allowable proximity, associate with nearest person."""
    person = DetectionBox(x1=100, y1=100, x2=300, y2=500, conf=0.9, class_id=0, track_id=7)
    # Phone is 20 pixels to the right of person's boundary
    phone = DetectionBox(x1=320, y1=200, x2=340, y2=240, conf=0.8, class_id=67)

    associated_id = associate_phone_to_person(phone, [person], proximity_ratio=0.6)
    assert associated_id == 7


def test_ambiguous_containment_overlapping_people():
    """When phone is inside multiple overlapping people boxes at similar distances, do NOT invent an identity (return None)."""
    # Overlapping students
    person1 = DetectionBox(x1=100, y1=100, x2=300, y2=500, conf=0.9, class_id=0, track_id=1)
    person2 = DetectionBox(x1=110, y1=100, x2=310, y2=500, conf=0.9, class_id=0, track_id=2)

    # Phone is directly in the middle of both
    phone = DetectionBox(x1=200, y1=300, x2=210, y2=320, conf=0.8, class_id=67)

    associated_id = associate_phone_to_person(phone, [person1, person2], ambiguity_ratio=0.7)
    assert associated_id is None


def test_isolated_distant_phone_returns_none():
    """When phone is too far from any person box, return None (unassigned phone requiring review)."""
    person = DetectionBox(x1=50, y1=50, x2=150, y2=250, conf=0.9, class_id=0, track_id=3)
    # Phone is far away on the floor or empty desk
    phone = DetectionBox(x1=800, y1=600, x2=850, y2=680, conf=0.85, class_id=67)

    associated_id = associate_phone_to_person(phone, [person])
    assert associated_id is None


def test_empty_person_boxes():
    """When no people are detected in the frame, return None."""
    phone = DetectionBox(x1=100, y1=100, x2=140, y2=160, conf=0.8, class_id=67)
    assert associate_phone_to_person(phone, []) is None
