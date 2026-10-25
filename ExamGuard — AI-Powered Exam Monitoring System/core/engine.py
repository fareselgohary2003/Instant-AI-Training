"""
Real-time Computer Vision Detection and Tracking Engine for ExamGuard.
Handles video decoding, YOLOv8 tracking with ByteTrack, spatial association,
cooldown deduplication, annotated video encoding, automatic evidence screenshot capture,
and database persistence.
"""

from __future__ import annotations

import os
import threading
import time
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set

import cv2
import numpy as np

from config import ALERTS_DIR, DEFAULT_CONFIG, OUTPUTS_DIR, ensure_directories
from core.association import DetectionBox, associate_phone_to_person
from core.visualizer import annotate_frame
from database import add_incident, create_job, update_job


@dataclass
class VideoProcessingResult:
    """Summary metrics of a completed video processing session."""
    job_id: str
    source_video: str
    output_video: Optional[str]
    status: str  # 'completed', 'failed', 'cancelled'
    total_frames: int
    processed_frames: int
    fps: float
    incident_count: int
    people_count: int
    screenshots_saved: int
    start_time: str
    end_time: str
    error_message: Optional[str] = None


class VideoDetectionEngine:
    """
    Modular execution engine for ExamGuard proctoring and incident detection.
    """

    def __init__(
        self,
        model_path: Optional[str | Path] = None,
        pose_model_path: Optional[str | Path] = None,
        enable_pose_detection: Optional[bool] = None,
        confidence_threshold: Optional[float] = None,
        cooldown_seconds: Optional[float] = None,
        proximity_threshold_ratio: Optional[float] = None,
        device: Optional[str] = None,
        alerts_dir: Optional[Path] = None,
        outputs_dir: Optional[Path] = None,
    ):
        ensure_directories()
        self.model_path = Path(model_path or DEFAULT_CONFIG["model_path"]).resolve()
        default_pose = DEFAULT_CONFIG.get("pose_model_path", str(self.model_path.parent / "yolov8n-pose.pt"))
        self.pose_model_path = Path(pose_model_path or default_pose).resolve()
        self.enable_pose_detection = (
            enable_pose_detection
            if enable_pose_detection is not None
            else bool(DEFAULT_CONFIG.get("enable_pose_detection", True))
        )
        self.confidence_threshold = float(
            confidence_threshold if confidence_threshold is not None else DEFAULT_CONFIG["confidence_threshold"]
        )
        self.cooldown_seconds = float(
            cooldown_seconds if cooldown_seconds is not None else DEFAULT_CONFIG["cooldown_seconds"]
        )
        self.proximity_threshold_ratio = float(
            proximity_threshold_ratio if proximity_threshold_ratio is not None else DEFAULT_CONFIG["proximity_threshold_ratio"]
        )
        self.device = str(device or DEFAULT_CONFIG.get("device", "cpu")).lower()
        self.alerts_dir = Path(alerts_dir or ALERTS_DIR).resolve()
        self.outputs_dir = Path(outputs_dir or OUTPUTS_DIR).resolve()

        self._model = None
        self._pose_model = None
        self._is_running = False
        self._lock = threading.Lock()

    def get_model(self):
        """Lazy load and validate the YOLO detection model."""
        if self._model is not None:
            return self._model

        if not self.model_path.is_file():
            raise FileNotFoundError(
                f"YOLO model weights file not found at: {self.model_path}. "
                "Please place 'yolov8n.pt' in the project root or configure the path in Settings."
            )

        try:
            from ultralytics import YOLO
            model = YOLO(str(self.model_path))
            self._model = model
            return self._model
        except Exception as e:
            raise RuntimeError(f"Failed to initialize YOLO model: {e}") from e

    def get_pose_model(self):
        """Lazy load pose estimation model for behavioral cheating / peeking detection."""
        if not self.enable_pose_detection:
            return None
        if self._pose_model is not None:
            return self._pose_model
        if self.pose_model_path.is_file():
            try:
                from ultralytics import YOLO
                self._pose_model = YOLO(str(self.pose_model_path))
                return self._pose_model
            except Exception as e:
                print(f"[ExamGuard Engine] Pose model notice: {e}")
                return None
        return None

    def is_running(self) -> bool:
        """Check whether a video processing session is currently active."""
        with self._lock:
            return self._is_running

    def process_video(
        self,
        video_path: str | Path,
        stop_event: Optional[threading.Event] = None,
        on_progress: Optional[Callable[[int, int, float, int, int, Optional[np.ndarray]], None]] = None,
        on_incident: Optional[Callable[[Dict[str, Any]], None]] = None,
        job_id: Optional[str] = None,
    ) -> VideoProcessingResult:
        """
        Process a video file through detection, tracking, association, and alert generation.

        Args:
            video_path: Path to the target exam video file.
            stop_event: Optional threading.Event to signal cancellation.
            on_progress: Callback(frame_idx, total_frames, fps, incident_count, people_count, preview_frame)
            on_incident: Callback(incident_dict) triggered when a new incident is saved.
            job_id: Optional unique job identifier.

        Returns:
            VideoProcessingResult summarizing the run.
        """
        with self._lock:
            if self._is_running:
                raise RuntimeError("Another video processing job is already running.")
            self._is_running = True

        video_path = Path(video_path).resolve()
        if not video_path.is_file():
            with self._lock:
                self._is_running = False
            raise FileNotFoundError(f"Selected video file does not exist: {video_path}")

        job_id = job_id or f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
        start_time_iso = datetime.now().astimezone().isoformat(timespec="seconds")

        # Open video capture
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            with self._lock:
                self._is_running = False
            raise ValueError(f"Cannot open video file: {video_path}. Verify codec and file integrity.")

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        video_fps = cap.get(cv2.CAP_PROP_FPS)
        if video_fps <= 0 or np.isnan(video_fps):
            video_fps = 25.0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # Setup output video path
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_stem = video_path.stem.replace(" ", "_")
        output_filename = f"processed_{safe_stem}_{timestamp_str}.mp4"
        output_path = self.outputs_dir / output_filename

        # Initialize video writer (try mp4v, fallback to XVID)
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(str(output_path), fourcc, video_fps, (width, height))
        if not writer.isOpened():
            # Fallback to AVI
            output_path = self.outputs_dir / f"processed_{safe_stem}_{timestamp_str}.avi"
            fourcc = cv2.VideoWriter_fourcc(*"XVID")
            writer = cv2.VideoWriter(str(output_path), fourcc, video_fps, (width, height))

        # Register initial job in database
        try:
            create_job(
                job_id=job_id,
                source_video=video_path.name,
                output_video=str(output_path) if writer.isOpened() else None,
                total_frames=total_frames,
                fps=video_fps,
            )
        except Exception as e:
            print(f"[ExamGuard Engine] Warning: Failed to create database job entry: {e}")

        # Load model
        try:
            model = self.get_model()
        except Exception as e:
            cap.release()
            if writer.isOpened():
                writer.release()
            with self._lock:
                self._is_running = False
            update_job(job_id=job_id, status="failed", error_message=str(e))
            raise

        frame_number = 0
        incident_count = 0
        screenshots_saved = 0
        tracked_people_ids: Set[int] = set()
        last_logged_frame: Dict[str, int] = {}
        consecutive_peeking: Dict[int, int] = {}
        cooldown_frames = int(self.cooldown_seconds * video_fps)

        # Suspicious exam items: 67=phone, 73=book/notes, 63=laptop
        suspicious_class_map = {
            67: "Phone",
            73: "Notes / Book",
            63: "Laptop",
        }
        target_classes = [0] + list(suspicious_class_map.keys())

        # Lazy load pose model for behavioral cheating / peeking detection
        pose_model = self.get_pose_model()

        status = "completed"
        error_message: Optional[str] = None
        t_start = time.perf_counter()

        try:
            while True:
                if stop_event and stop_event.is_set():
                    status = "cancelled"
                    break

                ret, frame = cap.read()
                if not ret:
                    break

                frame_number += 1

                # Execute YOLOv8 detection and ByteTrack tracking
                # Class 0: person, 67: cell phone, 73: book/notes, 63: laptop
                try:
                    results = model.track(
                        source=frame,
                        persist=True,
                        tracker="bytetrack.yaml",
                        imgsz=640,
                        conf=self.confidence_threshold,
                        classes=target_classes,
                        device=self.device if self.device != "auto" else "cpu",
                        verbose=False,
                    )
                except Exception as track_err:
                    print(f"[ExamGuard Engine] Frame {frame_number} tracking error: {track_err}")
                    writer.write(frame)
                    continue

                result = results[0]

                # Parse detection boxes
                person_boxes: List[DetectionBox] = []
                phone_boxes: List[DetectionBox] = []

                if result.boxes is not None and len(result.boxes) > 0:
                    for box in result.boxes:
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
                                tracked_people_ids.add(track_val)
                        elif cls_id in suspicious_class_map:
                            phone_boxes.append(det_box)

                current_frame_review_tracks: Set[int] = set()
                review_reasons: Dict[int, str] = {}

                # --- 1. Behavioral Cheating & Peeking Detection (Pose Estimation) ---
                if pose_model is not None and person_boxes:
                    try:
                        pose_res = pose_model(frame, verbose=False)[0]
                        if pose_res.keypoints is not None and len(pose_res.keypoints) > 0:
                            for kp_obj in pose_res.keypoints:
                                kpts = kp_obj.data[0].cpu().numpy()
                                nose = kpts[0]
                                le, re = kpts[1], kpts[2]
                                lear, rear = kpts[3], kpts[4]

                                if nose[2] > 0.35:
                                    # Associate pose to the matching student box
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
                                            if d < best_d and d < max(pbox.width, pbox.height):
                                                best_d = d
                                                matched_person = pbox

                                    if matched_person and matched_person.track_id is not None:
                                        tid = matched_person.track_id
                                        is_glancing = False
                                        glance_reason = "PEEKING / HEAD TURN"
                                        conf_score = 0.85

                                        # Eye-to-Nose Glance Ratio (Any glance left or right)
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

                                        # Ear Asymmetry Ratio
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

                                        # Instant frame turn: immediate red box!
                                        if is_glancing:
                                            consecutive_peeking[tid] = consecutive_peeking.get(tid, 0) + 1
                                            current_frame_review_tracks.add(tid)
                                            review_reasons[tid] = glance_reason

                                            if consecutive_peeking[tid] >= 2:  # immediate ~0.08s
                                                peeking_key = f"peeking_{tid}"
                                                last_peek_frame = last_logged_frame.get(peeking_key, -999999)
                                                if (frame_number - last_peek_frame) >= cooldown_frames:
                                                    annotated_snapshot = annotate_frame(
                                                        frame=frame,
                                                        person_boxes=person_boxes,
                                                        phone_boxes=phone_boxes,
                                                        review_track_ids=current_frame_review_tracks,
                                                        frame_number=frame_number,
                                                        total_frames=total_frames,
                                                        fps=video_fps,
                                                        incidents_count=incident_count + 1,
                                                        show_hud=True,
                                                        review_reasons=review_reasons,
                                                    )
                                                    timestamp_now = datetime.now().strftime("%Y%m%d_%H%M%S")
                                                    screenshot_name = f"incident_{timestamp_now}_frame_{frame_number}_peeking_track_{tid}.jpg"
                                                    screenshot_path = self.alerts_dir / screenshot_name

                                                    write_success = cv2.imwrite(str(screenshot_path), annotated_snapshot)
                                                    if write_success and screenshot_path.is_file() and screenshot_path.stat().st_size > 0:
                                                        screenshots_saved += 1
                                                        last_logged_frame[peeking_key] = frame_number

                                                        notes_text = (
                                                            f"Frame {frame_number} at {frame_number / video_fps:.1f}s. "
                                                            f"Student #{tid} detected peeking / turning head towards neighbor exam paper. "
                                                            "Proctor review required."
                                                        )
                                                        conf_score = round(min(0.98, 0.72 + ear_asymm * 0.25), 2)
                                                        inc_id = add_incident(
                                                            track_id=tid,
                                                            event_type="peeking_neighbor_exam",
                                                            confidence=conf_score,
                                                            screenshot_path=str(screenshot_path),
                                                            notes=notes_text,
                                                            source_video=video_path.name,
                                                            frame_number=frame_number,
                                                            job_id=job_id,
                                                        )
                                                        incident_count += 1
                                                        if on_incident:
                                                            try:
                                                                on_incident({
                                                                    "id": inc_id,
                                                                    "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
                                                                    "track_id": tid,
                                                                    "event_type": "peeking_neighbor_exam",
                                                                    "confidence": conf_score,
                                                                    "screenshot_path": str(screenshot_path),
                                                                    "notes": notes_text,
                                                                    "source_video": video_path.name,
                                                                    "frame_number": frame_number,
                                                                    "job_id": job_id,
                                                                })
                                                            except Exception as cb_err:
                                                                print(f"[ExamGuard Engine] on_incident callback error: {cb_err}")
                                        else:
                                            consecutive_peeking[tid] = max(0, consecutive_peeking.get(tid, 0) - 1)
                    except Exception as pose_err:
                        pass

                # --- 2. Process Suspicious Objects & Spatial Associations ---
                for phone in phone_boxes:
                    associated_track_id = associate_phone_to_person(
                        phone_box=phone,
                        person_boxes=person_boxes,
                        proximity_ratio=self.proximity_threshold_ratio,
                    )

                    obj_name = phone.label or "Phone"
                    if associated_track_id is not None:
                        current_frame_review_tracks.add(associated_track_id)
                        review_reasons[associated_track_id] = obj_name.upper()

                    # Deduplication / Cooldown key
                    if associated_track_id is not None:
                        event_key = f"track_{associated_track_id}_{obj_name.lower()}"
                    elif phone.track_id is not None:
                        event_key = f"obj_{phone.track_id}_{obj_name.lower()}"
                    else:
                        event_key = f"unassigned_{obj_name.lower()}"

                    last_frame = last_logged_frame.get(event_key, -999999)
                    if (frame_number - last_frame) >= cooldown_frames:
                        annotated_snapshot = annotate_frame(
                            frame=frame,
                            person_boxes=person_boxes,
                            phone_boxes=phone_boxes,
                            review_track_ids=current_frame_review_tracks,
                            frame_number=frame_number,
                            total_frames=total_frames,
                            fps=video_fps,
                            incidents_count=incident_count + 1,
                            show_hud=True,
                            review_reasons=review_reasons,
                        )

                        timestamp_now = datetime.now().strftime("%Y%m%d_%H%M%S")
                        sanitized_event = event_key.replace(":", "_").replace(" ", "_").replace("/", "_")
                        screenshot_name = f"incident_{timestamp_now}_frame_{frame_number}_{sanitized_event}.jpg"
                        screenshot_path = self.alerts_dir / screenshot_name

                        # Save screenshot with verification
                        write_success = cv2.imwrite(str(screenshot_path), annotated_snapshot)
                        if write_success and screenshot_path.is_file() and screenshot_path.stat().st_size > 0:
                            screenshots_saved += 1
                            last_logged_frame[event_key] = frame_number

                            # Insert into database
                            notes_text = (
                                f"Frame {frame_number} at {frame_number / video_fps:.1f}s. "
                                f"{obj_name} detected (confidence {phone.conf:.1%}). "
                                f"{'Associated with Person #' + str(associated_track_id) if associated_track_id is not None else 'Unassigned detection'}. "
                                "Human proctor review required."
                            )

                            event_type_name = f"{obj_name.lower().replace(' ', '_').replace('/', '_')}_detected"
                            inc_id = add_incident(
                                track_id=associated_track_id,
                                event_type=event_type_name,
                                confidence=phone.conf,
                                screenshot_path=str(screenshot_path),
                                notes=notes_text,
                                source_video=video_path.name,
                                frame_number=frame_number,
                                job_id=job_id,
                            )

                            incident_count += 1

                            # Trigger real-time incident callback
                            if on_incident:
                                incident_payload = {
                                    "id": inc_id,
                                    "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
                                    "track_id": associated_track_id,
                                    "event_type": event_type_name,
                                    "confidence": phone.conf,
                                    "screenshot_path": str(screenshot_path),
                                    "notes": notes_text,
                                    "source_video": video_path.name,
                                    "frame_number": frame_number,
                                    "job_id": job_id,
                                }
                                try:
                                    on_incident(incident_payload)
                                except Exception as cb_err:
                                    print(f"[ExamGuard Engine] on_incident callback error: {cb_err}")

                # Final frame annotation for output video
                annotated_frame = annotate_frame(
                    frame=frame,
                    person_boxes=person_boxes,
                    phone_boxes=phone_boxes,
                    review_track_ids=current_frame_review_tracks,
                    frame_number=frame_number,
                    total_frames=total_frames,
                    fps=video_fps,
                    incidents_count=incident_count,
                    show_hud=True,
                    review_reasons=review_reasons,
                )

                if writer.isOpened():
                    writer.write(annotated_frame)

                # Report progress callback
                if on_progress:
                    elapsed = max(0.001, time.perf_counter() - t_start)
                    current_fps = frame_number / elapsed
                    # Send preview frame every 2 frames for smooth UI rendering
                    preview = annotated_frame if frame_number % 2 == 0 else None
                    try:
                        on_progress(
                            frame_number,
                            total_frames,
                            current_fps,
                            incident_count,
                            len(tracked_people_ids),
                            preview,
                        )
                    except Exception as prog_err:
                        print(f"[ExamGuard Engine] on_progress error: {prog_err}")

        except Exception as e:
            status = "failed"
            error_message = str(e)
            print(f"[ExamGuard Engine] Processing error: {e}")
        finally:
            cap.release()
            if writer.isOpened():
                writer.release()
            with self._lock:
                self._is_running = False

        end_time_iso = datetime.now().astimezone().isoformat(timespec="seconds")
        total_time = max(0.001, time.perf_counter() - t_start)
        final_fps = frame_number / total_time

        # Update final job record in database
        try:
            update_job(
                job_id=job_id,
                status=status,
                output_video=str(output_path) if writer.isOpened() and output_path.is_file() else None,
                processed_frames=frame_number,
                incident_count=incident_count,
                people_count=len(tracked_people_ids),
                error_message=error_message,
            )
        except Exception as db_err:
            print(f"[ExamGuard Engine] Warning: Failed to update job status: {db_err}")

        return VideoProcessingResult(
            job_id=job_id,
            source_video=video_path.name,
            output_video=str(output_path) if output_path.is_file() else None,
            status=status,
            total_frames=total_frames,
            processed_frames=frame_number,
            fps=final_fps,
            incident_count=incident_count,
            people_count=len(tracked_people_ids),
            screenshots_saved=screenshots_saved,
            start_time=start_time_iso,
            end_time=end_time_iso,
            error_message=error_message,
        )


def torch_cuda_available() -> bool:
    """Helper to safely verify if CUDA is available in PyTorch."""
    try:
        import torch
        return bool(torch.cuda.is_available())
    except Exception:
        return False
