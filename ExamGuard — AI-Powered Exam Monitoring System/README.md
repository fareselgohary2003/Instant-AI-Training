# ExamGuard — Cheating Tracking & Alert System

**ExamGuard** is an AI-powered proctoring assistance system designed to detect suspicious objects (such as mobile phones) in examination video recordings, track individual students across frames using ByteTrack, automatically archive high-resolution evidence screenshots, and present actionable incidents to human proctors via an **Enterprise PySide6 (Qt for Python) Desktop Application**, a **Standard Tkinter Desktop Application**, and a **React + Vite Web Dashboard**.

---

## ⚠️ Important Ethical, Responsible Use & Technical Clarifications

1. **Observations vs. Misconduct**: An AI object detection (e.g. `phone_detected_review_required`) is a sensory observation and a review signal. **It is NOT conclusive proof of academic dishonesty or cheating intent.**
2. **Detection Confidence**: The confidence percentage (e.g., 85%) reflects how confident the YOLO neural network is that a bounding box contains a cell phone. **It is NOT the probability that a student cheated.**
3. **Human Proctor Authority**: Disciplinary actions must never be made automatically. All incidents require human proctor inspection, contextual verification, and manual determination (`pending`, `reviewed`, `dismissed`).
4. **Spatial Association Heuristic**: If a phone bounding box center falls inside a student's bounding box, or within an unambiguous proximity boundary, the system heuristically associates that track ID. When multiple students are overlapping or equidistant, the system leaves the track ID **unassigned (`None`)** rather than fabricating an identity.

---

## System Architecture

```
ExamGuard Workspace
│
├── desktop_app_qt.py            # Enterprise PySide6 (Qt) Desktop Application entry point
├── desktop_app.py               # Standard Tkinter Desktop Application entry point
├── main.py                      # FastAPI REST Backend & API services
├── database.py                  # SQLite schema manager, safe migrations & CRUD operations
├── config.py                    # Centralized settings and directory paths
├── cheating_system.db           # Persistent SQLite database (incidents & jobs)
├── yolov8n.pt                   # Ultralytics YOLOv8 nano model weights
│
├── core/                        # Core Computer Vision Engine
│   ├── engine.py                # Frame-by-frame tracker, cooldown deduplicator, video processor
│   ├── visualizer.py            # Green/Red/Orange bounding box and high-contrast HUD overlays
│   └── association.py           # Spatial proximity & containment heuristics
│
├── desktop_qt/                  # Enterprise PySide6 Desktop Application
│   ├── theme.py                 # Dark Navy theme, QSS design tokens, color palette
│   ├── worker.py                # QThread background worker with Qt Signals & Slots
│   ├── main_window.py           # Main QMainWindow shell with QStackedWidget
│   ├── components/
│   │   ├── sidebar.py           # Collapsible navigation sidebar (240px / 64px)
│   │   └── notification.py      # Floating in-app alert banner & audio chimes
│   └── views/
│       ├── overview_view.py     # Analytics KPI cards, custom painted distribution chart
│       ├── processing_view.py   # Native video picker, live progress, video preview, summary
│       ├── incidents_view.py    # Search, status filter, and incidents table
│       ├── review_view.py       # High-res evidence screenshot inspection & decision logger
│       └── settings_view.py     # Inference thresholds, model path, directories, device toggle
│
├── desktop/                     # Standard Tkinter Desktop Application Modular UI
│   ├── theme.py                 # Tkinter palette & ttk style configurations
│   ├── notifications.py         # Floating in-app alert banner
│   └── views/                   # Tkinter views (Overview, Processing, Incidents, Review, Settings)
│
├── frontend/                    # React + Vite Web Dashboard
│   ├── src/                     # React components, Tailwind/CSS, icons
│   └── package.json
│
├── alerts/screenshots/          # Verified evidence screenshots
├── outputs/processed_videos/    # Color-coded annotated output videos (.mp4)
└── tests/                       # Pytest automated test suite (32 comprehensive tests)
```

---

## Key Features

- **Enterprise PySide6 Desktop Application (`desktop_app_qt.py`)**:
  - Polished security-operations center UI with deep navy surfaces (`#0B1120`, `#1E293B`).
  - **Collapsible sidebar** toggling between full 240px labeled view and compact 64px icon view.
  - Dedicated pages: **Overview Dashboard**, **Video Processing**, **Incident History**, **Incident Evidence Review**, and **Settings**.
  - Non-blocking background worker execution using **Qt `QThread`** and thread-safe **Signals & Slots**.
  - Real-time progress bar, live FPS counter, student tracking counter, and live frame preview canvas.
  - Floating in-app notification banner with direct "Review Incident" action button and audio chime.
  - Interactive Review page displaying evidence screenshots, event metadata, and reviewer notes editor.
  - Settings page allowing configuration of confidence thresholds, cooldown seconds, and storage paths.

- **Standard Tkinter Desktop Application (`desktop_app.py`)**:
  - Preserved to ensure 100% compliance with the original project specification requiring Tkinter.
  - Zero external GUI library dependencies; runs out of the box with standard Python `tkinter`.

- **Computer Vision & Tracking Pipeline**:
  - YOLOv8 object detection targeting persons (class 0) and cell phones (class 67).
  - ByteTrack multi-object tracking preserving consistent student track IDs across video frames.
  - Color-coded visual overlays:
    - **Green bounding boxes**: Normally tracked students (`Student #ID`).
    - **Red bounding boxes**: Students associated with a suspicious detection (`REVIEW REQ: ID #ID`).
    - **Orange/Amber bounding boxes**: Detected cell phones with confidence scores (`Phone 82%`).
  - High-contrast text badges rendered over filled backgrounds for legibility against any background.
  - Configurable cooldown deduplication preventing continuous adjacent frames from spamming the database with hundreds of redundant incidents.

- **FastAPI REST Backend (`main.py`)**:
  - Serves incident feeds, statistics, and reviewer decisions.
  - Secure evidence image endpoint with strict path-traversal prevention (`403 Forbidden` on unauthorized paths).
  - Background video processing API trigger (`POST /api/process-video`).

- **React + Vite Web Dashboard (`frontend/`)**:
  - Modern web dashboard with real-time statistics cards, search filtering, and evidence review modals.

---

## Prerequisites

- **Python**: 3.10, 3.11, or 3.12 (64-bit recommended)
- **Node.js**: 18+ and npm (for the React web dashboard)
- **Operating System**: Windows 10/11 (fully supported; macOS / Linux compatible)

---

## Installation & Setup (Windows)

### 1. Set Up Python Virtual Environment

In PowerShell or Command Prompt inside the repository root:

```powershell
# Create virtual environment (if not already created)
python -m venv .venv

# Activate virtual environment
.\.venv\Scripts\Activate.ps1
# (Or in cmd.exe: .\.venv\Scripts\activate.bat)

# Upgrade pip and install dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Verify Model Weights

ExamGuard uses `yolov8n.pt`. A copy is already included in the workspace root. If you need to re-download or update weights:

```powershell
python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"
```

### 3. Install Frontend Dependencies (Optional for Web Dashboard)

```powershell
cd frontend
npm install
cd ..
```

---

## How to Run ExamGuard

You can run ExamGuard in any of the following modes:

### Mode 1: Enterprise PySide6 Desktop Application (Flagship)

```powershell
.\.venv\Scripts\python.exe desktop_app_qt.py
```

### Mode 2: Standard Tkinter Desktop Application (Specification Mandate)

```powershell
.\.venv\Scripts\python.exe desktop_app.py
```

### Mode 3: FastAPI Backend Server

Run the REST API backend (serves `http://127.0.0.1:8000`):

```powershell
.\.venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000
```
Interactive Swagger documentation is accessible at: `http://127.0.0.1:8000/docs`

### Mode 4: React + Vite Web Dashboard

In a separate terminal:

```powershell
cd frontend
npm run dev
```
Open your browser to: `http://localhost:5173`

---

## Video Processing Workflow

1. Launch **ExamGuard Desktop** (`python desktop_app_qt.py` or `python desktop_app.py`).
2. Navigate to **Video Processing** in the left sidebar.
3. Click **Select Exam Video...** and choose an exam recording (e.g., `WhatsApp Video 2026-10-24 at 17.59.33.mp4`).
4. Click **Start AI Processing**.
5. Observe live tracking metrics and frame-by-frame preview in the monitor.
6. When a suspicious object is detected:
   - An annotated screenshot is verified and saved to `alerts/screenshots/`.
   - The incident is persisted to `cheating_system.db`.
   - An in-app alert banner sounds a chime and displays the event details.
7. Upon completion:
   - The annotated video with green/red boxes is saved to `outputs/processed_videos/`.
   - Click **Play Output Video** to view the recording in your default media player.
8. Switch to **Incident History** or **Incident Evidence Review** to record reviewer determinations and notes.

---

## Storage Locations

| Artifact | Location | Description |
| :--- | :--- | :--- |
| **Database** | `cheating_system.db` | SQLite database storing incidents and processing jobs |
| **Evidence Screenshots** | `alerts/screenshots/` | Verified JPEG evidence captures of suspicious frames |
| **Annotated Videos** | `outputs/processed_videos/` | Fully rendered videos with track IDs and bounding boxes |
| **Legacy Incidents** | `incidents/` | Backward-compatible folder containing previous screenshots |
| **Settings File** | `config.json` | Local user preferences and custom threshold overrides |

---

## Running the Automated Test Suite

ExamGuard includes an extensive test suite verifying database migrations, spatial heuristics, image rendering, cooldown deduplication, API endpoints, and both PySide6 and Tkinter GUI components:

```powershell
.\.venv\Scripts\pytest.exe -v
```

All 32 tests will execute and validate:
- Database schema creation and migration.
- Incident addition, retrieval, filtering, and search.
- Review status updates and notes persistence.
- Spatial containment and proximity association heuristics.
- Color overlay contrast and bounding box rendering.
- VideoDetectionEngine execution and safe cancellation.
- FastAPI endpoints, path-traversal security, and image serving.
- Tkinter Desktop initialization, view switching, and notification triggers.
- PySide6 Desktop initialization, collapsible sidebar, QThread worker signals, and notification triggers.

---

## Troubleshooting & Hardware Notes

- **CUDA Acceleration**: If an NVIDIA GPU with CUDA is present, ExamGuard will automatically leverage it. If no GPU is available, the engine automatically runs inference on the CPU without crashing.
- **Tcl/Tk on Windows Virtual Environments**: If Python cannot find `init.tcl` for Tkinter, ExamGuard's `desktop_app.py` automatically detects and sets `TCL_LIBRARY` and `TK_LIBRARY` paths from the base Python installation.
- **PySide6 vs Tkinter**: Both desktop applications use the exact same underlying `core.engine` and `database` modules. Changes made in one desktop client or the React dashboard immediately reflect across all interfaces.
