"""
Live Proctoring & Webcam Stream Engine for ExamGuard.
Handles real-time webcam frame acquisition, YOLOv8 ByteTrack multi-student tracking,
pose peeking detection, real-time green/red annotation, automatic incident screenshot logging,
and MJPEG HTTP video streaming.
"""

from __future__ import annotations

import math
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Set

import cv2
import numpy as np

from config import ALERTS_DIR, DEFAULT_CONFIG, ensure_directories
from core.association import DetectionBox
from core.visualizer import annotate_frame
from database import add_incident


class LiveProctorManager:
    """Manages real-time laptop webcam proctoring session and MJPEG streaming."""

    def __init__(self):
        ensure_directories()
        self.alerts_dir = Path(ALERTS_DIR).resolve()
        self.is_running = False
        self.camera_index = 0
        self.conf_threshold = 0.10
        self.cooldown_seconds = 1.2

        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()

        self._latest_jpeg: Optional[bytes] = None
        self._fps = 0.0
        self._people_count = 0
        self._incident_count = 0
        self._session_start_time: Optional[str] = None
        self._last_incident_desc = ""

        # Models will be lazily loaded
        self._model = None
        self._pose_model = None

    def _load_models(self):
        """Lazy load YOLOv8 detection and pose models."""
        from ultralytics import YOLO

        model_path = Path(DEFAULT_CONFIG["model_path"]).resolve()
        if not model_path.is_file():
            model_path = Path("yolov8n.pt").resolve()

        if self._model is None:
            self._model = YOLO(str(model_path))

        pose_path = Path(DEFAULT_CONFIG.get("pose_model_path", "yolov8n-pose.pt")).resolve()
        if not pose_path.is_file():
            pose_path = Path("yolov8n-pose.pt").resolve()

        if self._pose_model is None and pose_path.is_file():
            try:
                self._pose_model = YOLO(str(pose_path))
            except Exception as e:
                print(f"[LiveProctor] Warning loading pose model: {e}")

    def start(self, camera_index: int = 0, conf_threshold: float = 0.10, cooldown_seconds: float = 1.2) -> Dict[str, Any]:
        """Start the live webcam proctoring session."""
        with self._lock:
            if self.is_running:
                return {
                    "status": "already_running",
                    "message": "Live webcam proctoring is already active.",
                    "camera_index": self.camera_index,
                }

            self.camera_index = camera_index
            self.conf_threshold = conf_threshold
            self.cooldown_seconds = cooldown_seconds
            self._stop_event.clear()
            self._session_start_time = datetime.now().astimezone().isoformat(timespec="seconds")
            self._incident_count = 0
            self._people_count = 0
            self._fps = 0.0
            self._latest_jpeg = None
            self.is_running = True

            self._thread = threading.Thread(target=self._capture_worker, daemon=True)
            self._thread.start()

            return {
                "status": "started",
                "message": "Live webcam proctoring started successfully.",
                "camera_index": camera_index,
            }

    def stop(self) -> Dict[str, Any]:
        """Stop live webcam proctoring session."""
        with self._lock:
            if not self.is_running:
                return {"status": "not_running", "message": "Live webcam is not running."}

            self._stop_event.set()
            self.is_running = False

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=3.0)

        return {
            "status": "stopped",
            "message": "Live webcam proctoring stopped.",
            "total_incidents": self._incident_count,
        }

    def get_status(self) -> Dict[str, Any]:
        """Get current live webcam monitoring telemetry."""
        return {
            "is_running": self.is_running,
            "camera_index": self.camera_index,
            "fps": round(self._fps, 1),
            "people_count": self._people_count,
            "incident_count": self._incident_count,
            "session_start_time": self._session_start_time,
            "last_incident": self._last_incident_desc,
        }

    def _capture_worker(self):
        """Worker thread that decodes webcam frames, runs AI detection, and logs cheating events."""
        print(f"[LiveProctor] Opening webcam {self.camera_index}...")

        cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
        if not cap.isOpened():
            cap = cv2.VideoCapture(self.camera_index)

        if not cap.isOpened():
            print(f"[LiveProctor] ERROR: Unable to open webcam {self.camera_index}")
            with self._lock:
                self.is_running = False
            return

        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        try:
            self._load_models()
        except Exception as e:
            print(f"[LiveProctor] Model load error: {e}")
            cap.release()
            with self._lock:
                self.is_running = False
            return

        model = self._model
        pose_model = self._pose_model

        suspicious_class_map = {
            67: "Phone",
            73: "Notes / Book",
            63: "Laptop",
        }
        target_classes = [0] + list(suspicious_class_map.keys())

        last_logged_time: Dict[str, float] = {}
        consecutive_peeking: Dict[int, int] = {}
        frame_idx = 0
        t_prev = time.perf_counter()

        print("[LiveProctor] Real-time inference loop started.")

        try:
            while not self._stop_event.is_set():
                ret, frame = cap.read()
                if not ret or frame is None:
                    time.sleep(0.02)
                    continue

                frame_idx += 1
                t_now = time.perf_counter()
                dt = t_now - t_prev
                t_prev = t_now
                if dt > 0:
                    current_fps = 1.0 / dt
                    self._fps = 0.85 * self._fps + 0.15 * current_fps if self._fps > 0 else current_fps

                # Run YOLOv8 detection + ByteTrack
                person_boxes: List[DetectionBox] = []
                phone_boxes: List[DetectionBox] = []
                tracked_tids: Set[int] = set()

                try:
                    results = model.track(
                        source=frame,
                        persist=True,
                        tracker="bytetrack.yaml",
                        imgsz=640,
                        conf=self.conf_threshold,
                        classes=target_classes,
                        device="cpu",
                        verbose=False,
                    )
                    res0 = results[0]
                    if res0.boxes is not None and len(res0.boxes) > 0:
                        for box in res0.boxes:
                            cls_id = int(box.cls.item())
                            conf_val = float(box.conf.item())
                            track_val = int(box.id.item()) if box.id is not None else None
                            coords = [float(v) for v in box.xyxy[0].tolist()]

                            det_box = DetectionBox(
                                x1=coords[0],
                                y1=coords[1],
                                x2=coords[2],
                                y2=coords[3],
                                conf=conf_val,
                                class_id=cls_id,
                                track_id=track_val,
                                label=suspicious_class_map.get(cls_id, None),
                            )

                            if cls_id == 0:
                                person_boxes.append(det_box)
                                if track_val is not None:
                                    tracked_tids.add(track_val)
                            elif cls_id in suspicious_class_map:
                                phone_boxes.append(det_box)
                except Exception as track_err:
                    print(f"[LiveProctor] Tracking error: {track_err}")

                self._people_count = len(tracked_tids) or len(person_boxes)

                current_frame_review_tracks: Set[int] = set()
                review_reasons: Dict[int, str] = {}

                # 1. Pose peeking & glance detection (Instant response on any glance left/right)
                if pose_model is not None and person_boxes:
                    try:
                        pose_res = pose_model(frame, verbose=False)[0]
                        if pose_res.keypoints is not None and len(pose_res.keypoints) > 0:
                            for kp_obj in pose_res.keypoints:
                                kpts = kp_obj.data[0].cpu().numpy()
                                nose = kpts[0]
                                le, re = kpts[1], kpts[2]
                                lear, rear = kpts[3], kpts[4]

                                if nose[2] > 0.25:
                                    # Match pose to student box
                                    matched_person = None
                                    for pbox in person_boxes:
                                        if pbox.contains_point(float(nose[0]), float(nose[1])):
                                            matched_person = pbox
                                            break
                                    if not matched_person:
                                        # Distance fallback
                                        best_d = float("inf")
                                        for pbox in person_boxes:
                                            d = math.hypot(nose[0] - pbox.center[0], nose[1] - pbox.center[1])
                                            if d < best_d and d < max(pbox.width, pbox.height) * 1.2:
                                                best_d = d
                                                matched_person = pbox

                                    if matched_person and matched_person.track_id is not None:
                                        tid = matched_person.track_id
                                        is_glancing = False
                                        glance_reason = "PEEKING / HEAD TURN"
                                        conf_score = 0.85

                                        # Heuristic A: Eye-to-Nose Glance Ratio (Any glance left or right)
                                        if le[2] > 0.20 and re[2] > 0.20:
                                            eye_width = abs(re[0] - le[0])
                                            if eye_width > 8:
                                                eye_mid_x = (le[0] + re[0]) / 2.0
                                                eye_offset = abs(nose[0] - eye_mid_x) / eye_width
                                                if eye_offset > 0.16:
                                                    is_glancing = True
                                                    direction = "RIGHT" if nose[0] < eye_mid_x else "LEFT"
                                                    glance_reason = f"PEEKING {direction} (HEAD TURN)"
                                                    conf_score = round(min(0.98, 0.76 + eye_offset * 0.35), 2)

                                        # Heuristic B: Ear Asymmetry Ratio
                                        if not is_glancing:
                                            if lear[2] > 0.20 and rear[2] > 0.20:
                                                dl = abs(lear[0] - nose[0])
                                                dr = abs(rear[0] - nose[0])
                                                ear_asymm = abs(dr - dl) / (dr + dl + 1e-5)
                                                if ear_asymm > 0.18:
                                                    is_glancing = True
                                                    glance_reason = "PEEKING / HEAD TURN"
                                                    conf_score = round(min(0.98, 0.74 + ear_asymm * 0.26), 2)
                                            elif (lear[2] > 0.30 and rear[2] < 0.15) or (rear[2] > 0.30 and lear[2] < 0.15):
                                                is_glancing = True
                                                glance_reason = "HEAD TURNED ASIDE"
                                                conf_score = 0.90

                                        # Heuristic C: Looking down at lap / desk / hidden notes
                                        if not is_glancing and le[2] > 0.25 and re[2] > 0.25:
                                            eye_y = (le[1] + re[1]) / 2.0
                                            eye_w = abs(re[0] - le[0])
                                            if eye_w > 10 and (nose[1] - eye_y) > eye_w * 0.78:
                                                is_glancing = True
                                                glance_reason = "GAZE DOWN (LAP / NOTES)"
                                                conf_score = 0.82

                                        # INSTANT VISUAL FEEDBACK: Change box to RED immediately on frame 1!
                                        if is_glancing:
                                            current_frame_review_tracks.add(tid)
                                            review_reasons[tid] = glance_reason

                                            peeking_key = f"peek_{tid}"
                                            now_t = time.time()
                                            if (now_t - last_logged_time.get(peeking_key, 0)) >= self.cooldown_seconds:
                                                last_logged_time[peeking_key] = now_t
                                                self._log_live_incident(
                                                    frame=frame,
                                                    person_boxes=person_boxes,
                                                    phone_boxes=phone_boxes,
                                                    review_tracks=current_frame_review_tracks,
                                                    review_reasons=review_reasons,
                                                    track_id=tid,
                                                    event_type="peeking_neighbor_exam",
                                                    confidence=conf_score,
                                                    notes=f"Live Camera: Student #{tid} {glance_reason.lower()} detected instantly.",
                                                )
                    except Exception as pose_err:
                        print(f"[LiveProctor] Pose error: {pose_err}")

                # 2. Unauthorized object detection (phone, book, laptop) — INSTANT TRIGGER
                if phone_boxes:
                    for obj in phone_boxes:
                        label_str = obj.label or "UNAUTHORIZED DEVICE"
                        closest_p = None
                        min_d = float("inf")
                        if person_boxes:
                            for p in person_boxes:
                                d = math.hypot(obj.center[0] - p.center[0], obj.center[1] - p.center[1])
                                if d < min_d:
                                    min_d = d
                                    closest_p = p

                        tid = closest_p.track_id if (closest_p and closest_p.track_id is not None) else 1
                        current_frame_review_tracks.add(tid)
                        review_reasons[tid] = f"ALERT: {label_str.upper()}"

                        obj_key = f"obj_{tid}_{obj.class_id}"
                        now_t = time.time()
                        if (now_t - last_logged_time.get(obj_key, 0)) >= self.cooldown_seconds:
                            last_logged_time[obj_key] = now_t
                            self._log_live_incident(
                                frame=frame,
                                person_boxes=person_boxes,
                                phone_boxes=phone_boxes,
                                review_tracks=current_frame_review_tracks,
                                review_reasons=review_reasons,
                                track_id=tid,
                                event_type=f"unauthorized_{label_str.lower().replace(' ', '_')}",
                                confidence=round(float(obj.conf), 2),
                                notes=f"Live Camera: {label_str} detected instantly with {round(obj.conf*100)}% confidence.",
                            )

                # Annotate live frame: Green for normal students, Red for cheating suspects!
                annotated = annotate_frame(
                    frame=frame,
                    person_boxes=person_boxes,
                    phone_boxes=phone_boxes,
                    review_track_ids=current_frame_review_tracks,
                    frame_number=frame_idx,
                    total_frames=0,
                    fps=self._fps,
                    incidents_count=self._incident_count,
                    show_hud=True,
                    review_reasons=review_reasons,
                )

                # Add a distinct "LIVE WEBCAM STREAM" badge at top center
                cv2.putText(
                    annotated,
                    "LIVE WEBCAM PROCTORING",
                    (10, annotated.shape[0] - 15),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.55,
                    (0, 255, 0) if len(current_frame_review_tracks) == 0 else (0, 0, 255),
                    2,
                )

                # Encode to JPEG
                ok, jpeg_buf = cv2.imencode(".jpg", annotated, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
                if ok:
                    self._latest_jpeg = jpeg_buf.tobytes()

                time.sleep(0.005)

        finally:
            cap.release()
            print("[LiveProctor] Webcam capture released and worker finished.")
            with self._lock:
                self.is_running = False

    def _log_live_incident(
        self,
        frame: np.ndarray,
        person_boxes: List[DetectionBox],
        phone_boxes: List[DetectionBox],
        review_tracks: Set[int],
        review_reasons: Dict[int, str],
        track_id: int,
        event_type: str,
        confidence: float,
        notes: str,
    ):
        """Save evidence snapshot and insert incident record into database."""
        try:
            snapshot = annotate_frame(
                frame=frame,
                person_boxes=person_boxes,
                phone_boxes=phone_boxes,
                review_track_ids=review_tracks,
                frame_number=0,
                total_frames=0,
                fps=self._fps,
                incidents_count=self._incident_count + 1,
                show_hud=True,
                review_reasons=review_reasons,
            )

            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            fname = f"incident_live_{timestamp_str}_track_{track_id}_{event_type[:15]}.jpg"
            snap_path = self.alerts_dir / fname

            cv2.imwrite(str(snap_path), snapshot)

            inc_id = add_incident(
                track_id=track_id,
                event_type=event_type,
                confidence=confidence,
                screenshot_path=str(snap_path),
                notes=notes,
                source_video="Live Laptop Webcam",
                frame_number=0,
                job_id="job_live_webcam",
            )

            self._incident_count += 1
            self._last_incident_desc = f"Student #{track_id}: {event_type.replace('_', ' ').title()}"
            print(f"[LiveProctor] 🔴 Cheating incident logged #{inc_id}: Student #{track_id} - {event_type}")
        except Exception as e:
            print(f"[LiveProctor] Error logging live incident: {e}")

    def get_latest_frame(self) -> Optional[bytes]:
        """Return the most recently processed JPEG frame bytes."""
        return self._latest_jpeg

    def generate_mjpeg_stream(self) -> Generator[bytes, None, None]:
        """Yield MJPEG multipart stream chunks for HTTP streaming."""
        while True:
            if not self.is_running:
                # Return placeholder frame if camera is off
                placeholder = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(
                    placeholder,
                    "Webcam Offline. Click 'Start Live Camera'",
                    (70, 240),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.65,
                    (200, 200, 200),
                    2,
                )
                _, buf = cv2.imencode(".jpg", placeholder)
                yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + buf.tobytes() + b"\r\n")
                time.sleep(0.5)
                continue

            frame_bytes = self._latest_jpeg
            if frame_bytes is not None:
                yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n")
                time.sleep(0.04)  # ~25 FPS
            else:
                time.sleep(0.05)


# Global singleton instance
live_proctor_instance = LiveProctorManager()
