
from ultralytics import YOLO
import cv2
from pathlib import Path
from datetime import datetime

from database import init_db, add_incident

VIDEO_PATH = "WhatsApp Video 2026-10-24 at 17.59.33.mp4"
OUTPUT_PATH = "output_detected.mp4"
INCIDENTS_DIR = Path("incidents")

CONFIDENCE = 0.20
EVENT_COOLDOWN_SECONDS = 5


def center_of(box):
    x1, y1, x2, y2 = map(float, box.xyxy[0].tolist())
    return ((x1 + x2) / 2, (y1 + y2) / 2)


def find_nearest_person(phone_box, person_boxes):
    if not person_boxes:
        return None

    px, py = center_of(phone_box)
    nearest_id = None
    nearest_distance = float("inf")

    for person_box in person_boxes:
        person_id = None

        if person_box.id is not None:
            person_id = int(person_box.id.item())

        x1, y1, x2, y2 = map(float, person_box.xyxy[0].tolist())

        # Check whether the phone center lies inside the person box.
        if x1 <= px <= x2 and y1 <= py <= y2:
            return person_id

        cx, cy = center_of(person_box)
        distance = ((px - cx) ** 2 + (py - cy) ** 2) ** 0.5

        if distance < nearest_distance:
            nearest_distance = distance
            nearest_id = person_id

    return nearest_id


def main():
    init_db()
    INCIDENTS_DIR.mkdir(parents=True, exist_ok=True)

    model = YOLO("yolov8n.pt")
    cap = cv2.VideoCapture(VIDEO_PATH)

    if not cap.isOpened():
        print(f"Error: Cannot open video: {VIDEO_PATH}")
        return

    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    if fps <= 0:
        fps = 25

    output = cv2.VideoWriter(
        OUTPUT_PATH,
        cv2.VideoWriter_fourcc(*"mp4v"),
        fps,
        (width, height)
    )

    if not output.isOpened():
        print("Error: Cannot create output video.")
        cap.release()
        return

    frame_number = 0
    last_logged_frame = {}

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame_number += 1

            results = model.track(
                source=frame,
                persist=True,
                tracker="bytetrack.yaml",
                imgsz=960,
                conf=CONFIDENCE,
                classes=[0, 67],
                verbose=False
            )

            result = results[0]
            annotated = result.plot()

            person_boxes = [
                box for box in result.boxes
                if int(box.cls.item()) == 0
            ]

            phone_boxes = [
                box for box in result.boxes
                if int(box.cls.item()) == 67
            ]

            for phone_box in phone_boxes:
                phone_confidence = float(phone_box.conf.item())

                person_id = find_nearest_person(
                    phone_box,
                    person_boxes
                )

                # Use the nearby person's ID when available.
                # Otherwise use the phone track ID to prevent duplicates.
                phone_id = (
                    int(phone_box.id.item())
                    if phone_box.id is not None
                    else None
                )

                event_key = (
                    f"person_{person_id}"
                    if person_id is not None
                    else f"phone_{phone_id}"
                    if phone_id is not None
                    else f"phone_frame_{frame_number}"
                )

                cooldown_frames = int(
                    EVENT_COOLDOWN_SECONDS * fps
                )

                previous_frame = last_logged_frame.get(event_key, -1)

                if frame_number - previous_frame < cooldown_frames:
                    continue

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                screenshot_name = (
                    f"incident_{timestamp}_frame_{frame_number}_"
                    f"{event_key}.jpg"
                )
                screenshot_path = INCIDENTS_DIR / screenshot_name

                if not cv2.imwrite(
                    str(screenshot_path),
                    annotated
                ):
                    print(f"Warning: Could not save {screenshot_path}")
                    continue

                incident_id = add_incident(
                    track_id=person_id if person_id is not None else phone_id,
                    event_type="phone_detected_review_required",
                    confidence=phone_confidence,
                    screenshot_path=screenshot_path,
                    notes=(
                        f"Frame {frame_number}. "
                        "Phone detection requires human review; "
                        "this is not proof of cheating."
                    )
                )

                last_logged_frame[event_key] = frame_number

                print(
                    f"Incident #{incident_id} saved | "
                    f"Person ID={person_id} | "
                    f"Phone confidence={phone_confidence:.2f} | "
                    f"Image={screenshot_path}"
                )

            output.write(annotated)

            if frame_number % 25 == 0:
                print(
                    f"Frame {frame_number}: "
                    f"People={len(person_boxes)}, "
                    f"Phones={len(phone_boxes)}"
                )

            cv2.imshow("People and Phone Detection", annotated)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                print("Stopped by user.")
                break

    finally:
        cap.release()
        output.release()
        cv2.destroyAllWindows()

    print(f"\nFinished. Output saved to: {Path(OUTPUT_PATH).resolve()}")
    print(f"Incident images folder: {INCIDENTS_DIR.resolve()}")


if __name__ == "__main__":
    main()
