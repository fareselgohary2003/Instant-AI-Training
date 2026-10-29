"""
Configuration and settings management for ExamGuard.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


# Root directories
BASE_DIR = Path(__file__).resolve().parent
ALERTS_DIR = BASE_DIR / "alerts" / "screenshots"
INCIDENTS_DIR = BASE_DIR / "incidents"  # Preserved for backward compatibility
OUTPUTS_DIR = BASE_DIR / "outputs" / "processed_videos"
LOGS_DIR = BASE_DIR / "logs"

# Database path (matches existing cheating_system.db)
DB_PATH = BASE_DIR / "cheating_system.db"

# Model configuration
DEFAULT_MODEL_PATH = BASE_DIR / "yolov8n.pt"
DEFAULT_POSE_MODEL_PATH = BASE_DIR / "yolov8n-pose.pt"

# Default detection & tracking parameters
DEFAULT_CONFIG: Dict[str, Any] = {
    "model_path": str(DEFAULT_MODEL_PATH),
    "pose_model_path": str(DEFAULT_POSE_MODEL_PATH),
    "enable_pose_detection": True,
    "confidence_threshold": 0.15,
    "cooldown_seconds": 4.0,
    "iou_threshold": 0.45,
    "proximity_threshold_ratio": 0.6,
    "device": "cpu",  # 'cpu' or 'cuda'
    "alerts_dir": str(ALERTS_DIR),
    "outputs_dir": str(OUTPUTS_DIR),
    "sound_alerts": True,
}

CONFIG_FILE = BASE_DIR / "config.json"


def ensure_directories() -> None:
    """Ensure all required output and storage directories exist."""
    ALERTS_DIR.mkdir(parents=True, exist_ok=True)
    INCIDENTS_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)


def load_config() -> Dict[str, Any]:
    """Load configuration from config.json with fallback to default settings."""
    ensure_directories()
    config = dict(DEFAULT_CONFIG)

    if CONFIG_FILE.is_file():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                if isinstance(saved, dict):
                    config.update(saved)
        except Exception as e:
            print(f"[ExamGuard Config] Warning: Failed to load {CONFIG_FILE}: {e}")

    return config


def save_config(new_config: Dict[str, Any]) -> bool:
    """Save configuration to config.json."""
    ensure_directories()
    try:
        current = load_config()
        current.update(new_config)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(current, f, indent=4)
        return True
    except Exception as e:
        print(f"[ExamGuard Config] Error saving {CONFIG_FILE}: {e}")
        return False
