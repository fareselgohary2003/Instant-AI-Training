"""
Spatial association heuristics for associating detected suspicious objects (e.g., cell phones)
with tracked people (e.g., students in an examination room).

IMPORTANT ETHICAL & TECHNICAL DISCLAIMER:
A phone detection and spatial association is a preliminary observation and heuristic signal.
It is NOT conclusive proof of possession, intent, or academic misconduct.
When association is ambiguous (e.g., overlapping people or distant objects),
the system records the event as requiring human review with an unassigned track ID (None)
rather than fabricating an identity.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Optional, Tuple


@dataclass
class DetectionBox:
    """Represents a single object detection bounding box."""
    x1: float
    y1: float
    x2: float
    y2: float
    conf: float
    class_id: int
    track_id: Optional[int] = None
    label: Optional[str] = None

    @property
    def center(self) -> Tuple[float, float]:
        """Compute the center coordinate (cx, cy) of the bounding box."""
        return ((self.x1 + self.x2) / 2.0, (self.y1 + self.y2) / 2.0)

    @property
    def width(self) -> float:
        return max(0.0, self.x2 - self.x1)

    @property
    def height(self) -> float:
        return max(0.0, self.y2 - self.y1)

    def contains_point(self, px: float, py: float) -> bool:
        """Check if point (px, py) lies inside the bounding box."""
        return self.x1 <= px <= self.x2 and self.y1 <= py <= self.y2

    def distance_to_point(self, px: float, py: float) -> float:
        """Calculate shortest Euclidean distance from a point to the box boundary."""
        dx = max(self.x1 - px, 0.0, px - self.x2)
        dy = max(self.y1 - py, 0.0, py - self.y2)
        return math.hypot(dx, dy)


def associate_phone_to_person(
    phone_box: DetectionBox,
    person_boxes: List[DetectionBox],
    proximity_ratio: float = 0.6,
    ambiguity_ratio: float = 0.7,
) -> Optional[int]:
    """
    Associate a cell phone detection with the most likely person track ID
    based on spatial proximity heuristics.

    Heuristic Rules:
    1. Direct Containment:
       If the phone center falls inside a single person's bounding box,
       associate with that person's track ID.
       If it falls inside multiple overlapping person boxes, check center-to-center
       distances. If the closest person is significantly closer than the second closest
       (d1 / d2 < ambiguity_ratio), associate with that person; otherwise mark as ambiguous.

    2. Near-Boundary Proximity:
       If the phone center is outside all person boxes, calculate distance from
       phone center to each person box boundary.
       If the closest person is within an allowable distance (min(width, height) * proximity_ratio)
       and is clearly closer than any other person (d1 / d2 < ambiguity_ratio),
       associate with that person.

    3. Ambiguity / No Near Person:
       If no person is within threshold or multiple persons are equally close,
       return None (unassigned), ensuring evidence is flagged for human review
       without falsely attributing it to a student.

    Returns:
        Optional[int]: The person's track_id, or None if ambiguous / unassigned.
    """
    if not person_boxes:
        return None

    px, py = phone_box.center

    # 1. Check direct containment
    containing_people: List[Tuple[float, DetectionBox]] = []
    for person in person_boxes:
        if person.contains_point(px, py):
            cx, cy = person.center
            dist = math.hypot(px - cx, py - cy)
            containing_people.append((dist, person))

    if len(containing_people) == 1:
        return containing_people[0][1].track_id
    elif len(containing_people) > 1:
        containing_people.sort(key=lambda item: item[0])
        d1, p1 = containing_people[0]
        d2, _ = containing_people[1]
        if d2 > 0 and (d1 / d2) <= ambiguity_ratio:
            return p1.track_id
        # Overlap is ambiguous
        return None

    # 2. Check near-boundary proximity
    nearby_people: List[Tuple[float, DetectionBox]] = []
    for person in person_boxes:
        boundary_dist = person.distance_to_point(px, py)
        max_allowed = max(40.0, min(person.width, person.height) * proximity_ratio)
        if boundary_dist <= max_allowed:
            nearby_people.append((boundary_dist, person))

    if not nearby_people:
        return None

    nearby_people.sort(key=lambda item: item[0])
    d1, p1 = nearby_people[0]

    if len(nearby_people) == 1:
        return p1.track_id

    d2, _ = nearby_people[1]
    if d2 > 0 and (d1 / d2) <= ambiguity_ratio:
        return p1.track_id

    # Ambiguous between multiple nearby people
    return None


# General alias for all unauthorized examination objects (phones, notes, laptops)
associate_object_to_person = associate_phone_to_person
