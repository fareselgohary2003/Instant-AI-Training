# ExamGuard — AI-Powered Exam Monitoring System

<p align="center">
  <strong>Real-Time Computer Vision · Multi-Object Tracking · Evidence-Based Incident Review</strong>
</p>

<p align="center">
  An AI-assisted exam monitoring system that detects suspicious objects, tracks people across video frames, captures visual evidence, and helps human proctors review potential incidents through desktop and web interfaces.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Computer%20Vision-OpenCV-green" alt="Computer Vision">
  <img src="https://img.shields.io/badge/Object%20Detection-YOLOv8-purple" alt="YOLOv8">
  <img src="https://img.shields.io/badge/Tracking-ByteTrack-orange" alt="ByteTrack">
  <img src="https://img.shields.io/badge/Desktop-PySide6-41CD52?logo=qt&logoColor=white" alt="PySide6">
  <img src="https://img.shields.io/badge/Backend-FastAPI-009688?logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/Database-SQLite-003B57?logo=sqlite&logoColor=white" alt="SQLite">
  <img src="https://img.shields.io/badge/Frontend-React-61DAFB?logo=react&logoColor=black" alt="React">
</p>

---

## Table of Contents

- [Overview](#overview)
- [Project Preview](#project-preview)
- [Key Features](#key-features)
- [How It Works](#how-it-works)
- [System Architecture](#system-architecture)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Running the Application](#running-the-application)
- [Usage Guide](#usage-guide)
- [Incident Management](#incident-management)
- [Testing](#testing)
- [Responsible AI and Privacy](#responsible-ai-and-privacy)
- [Limitations and Future Improvements](#limitations-and-future-improvements)
- [Author](#author)

---

## Overview

**ExamGuard** is an AI-assisted exam monitoring and incident detection system designed to help proctors identify and review potentially suspicious events during examinations.

The system combines computer vision, object tracking, evidence capture, database persistence, and incident management into a unified application. It supports webcam-based monitoring and uploaded video processing, with desktop interfaces and a browser-based dashboard for reviewing recorded incidents.

ExamGuard provides visual observations and supporting evidence for human review rather than making automatic disciplinary decisions.

### Project Goals

- Apply computer vision to examination monitoring.
- Detect relevant objects, including mobile phones.
- Track people across video frames using multi-object tracking.
- Visualize detections using color-coded bounding boxes.
- Capture screenshots when qualifying events occur.
- Store incident metadata and evidence references in a database.
- Support human review through incident history and review statuses.
- Provide desktop and web-based interfaces.

---

## Project Preview

### Desktop Application

![ExamGuard Desktop Overview](docs/images/examguard-overview.png.png)

### Live Camera Monitoring

![ExamGuard Live Camera Monitoring](docs/images/live-camera.png.png)

### Uploaded Video Processing

![ExamGuard Video Processing](docs/images/video-processing.png.png)

### AI Detection Results

![ExamGuard Detection Results](docs/images/detection-results.png.png)

### Incident History and Evidence Review

![ExamGuard Incident History](docs/images/incident-history.png.png)

### Web Dashboard

![ExamGuard Web Dashboard](docs/images/web-dashboard.png.png)

---

## Key Features

### 1. Real-Time Camera Monitoring

- Monitor a live camera feed through the desktop application.
- Run the computer vision pipeline on incoming frames.
- Display visual detection results during monitoring.
- Generate incident records when configured detection conditions are met.
- Stop monitoring and release camera resources.

### 2. Uploaded Video Processing

- Select an existing examination video.
- Process video frames through the detection and tracking pipeline.
- Display annotated frames and processing progress.
- Save processed video output when supported by the selected workflow.
- Review incidents generated during processing.

### 3. AI Object Detection

ExamGuard uses the YOLOv8 object detection model to identify relevant objects, including people and mobile phones.

The detection pipeline can provide:

- Object bounding boxes.
- Object classes.
- Detection confidence scores.
- Frame-level visual annotations.

Detection results depend on video quality, camera position, lighting, occlusion, model performance, and inference settings.

### 4. Multi-Object Tracking

ByteTrack maintains object track IDs across video frames, helping the system associate observations with tracked people over time.

Spatial association heuristics can associate a detected phone with a nearby person when the relationship is sufficiently clear. Ambiguous associations should remain unassigned rather than being treated as certain.

### 5. Visual Detection Overlays

The processed video can display color-coded annotations:

- **Green:** Normally tracked people.
- **Red:** People associated with an event requiring review.
- **Orange/Amber:** Detected mobile phones and their detection confidence.

These colors communicate system observations and review states. They do not establish misconduct.

### 6. Evidence Capture and Storage

When configured conditions are met, the system can:

- Capture an annotated screenshot.
- Save the screenshot to the evidence directory.
- Record event metadata in SQLite.
- Associate the incident with a track ID when available.
- Preserve a reference to the saved evidence.

### 7. Incident Management

The incident workflow supports reviewing recorded events, inspecting associated screenshots, and managing review statuses such as `pending`, `reviewed`, and `dismissed`, where implemented.

### 8. Desktop Applications

ExamGuard includes two Python desktop interfaces:

- **PySide6:** The primary Qt-based desktop interface.
- **Tkinter:** An alternative desktop interface retained for compatibility with the original project specification.

### 9. Web Dashboard and API

The project also includes:

- A FastAPI backend for supported HTTP endpoints.
- A SQLite database for persistent incident records.
- A React + Vite dashboard for viewing incident information and statistics.

---

## How It Works

The general workflow is:

1. **Select a monitoring mode:** Start live camera monitoring or choose a video file.
2. **Process frames:** The computer vision engine analyzes incoming video frames.
3. **Detect objects:** YOLOv8 identifies people and relevant objects.
4. **Track observations:** ByteTrack maintains track IDs across frames.
5. **Associate observations:** Spatial heuristics may associate a detected phone with a tracked person when the evidence is sufficiently clear.
6. **Render annotations:** The system displays detection boxes and relevant labels.
7. **Generate incidents:** Events meeting configured conditions can trigger incident creation and evidence capture.
8. **Persist results:** Incident metadata and evidence paths are saved through the database workflow.
9. **Review evidence:** A human reviewer inspects the incident and records an appropriate review decision.

<details>
<summary><strong>Technical Workflow</strong></summary>

```text
Live Camera / Uploaded Video
            |
            v
      Frame Acquisition
            |
            v
     YOLOv8 Detection
            |
            v
   ByteTrack Association
            |
            v
  Spatial Association Logic
            |
            v
   Detection Visualization
            |
            v
 Incident Trigger / Cooldown
            |
       +----+----+
       |         |
       v         v
 Evidence      Incident
 Screenshot    Metadata
       |         |
       +----+----+
            |
            v
     SQLite Persistence
            |
            v
   Incident Review Interfaces
```

</details>

---

## System Architecture

ExamGuard is organized into several components.

| Component | Responsibility |
|---|---|
| Computer Vision Engine | Video processing, object detection, tracking, and event handling |
| Visualization Module | Bounding boxes, labels, and annotated frames |
| Association Logic | Spatial association between detected objects and tracked people |
| PySide6 Desktop Application | Primary desktop monitoring and review interface |
| Tkinter Desktop Application | Alternative desktop interface |
| FastAPI Backend | HTTP API endpoints and backend services |
| SQLite Database | Persistent incident data and supported job records |
| React + Vite Dashboard | Browser-based incident monitoring and statistics |
| Automated Tests | Verification of supported application components and behavior |

The desktop applications and web dashboard provide different interfaces to the project. Their ability to share updates depends on the configured backend and database integration.

---

## Technology Stack

| Category | Technologies |
|---|---|
| Programming Language | Python |
| Object Detection | Ultralytics YOLOv8 |
| Computer Vision | OpenCV |
| Multi-Object Tracking | ByteTrack |
| Desktop UI | PySide6 / Qt for Python, Tkinter |
| Backend API | FastAPI |
| Database | SQLite |
| Web Frontend | React, Vite |
| Frontend Language | JavaScript / JSX |
| Testing | pytest and project-specific automated tests |

---

## Project Structure

The following is a high-level overview of the main project components. Exact filenames and optional modules may vary by version.

```text
ExamGuard/
├── main.py
├── database.py
├── config.py
├── desktop_app_qt.py
├── desktop_app.py
├── core/
│   ├── engine.py
│   ├── visualizer.py
│   └── association.py
├── desktop_qt/
│   ├── theme.py
│   ├── worker.py
│   ├── main_window.py
│   ├── components/
│   └── views/
├── desktop/
│   ├── theme.py
│   ├── notifications.py
│   └── views/
├── frontend/
│   ├── src/
│   └── package.json
├── alerts/
│   └── screenshots/
├── outputs/
│   └── processed_videos/
├── tests/
├── docs/
│   └── images/
│       ├── examguard-overview.png.png
│       ├── live-camera.png.png
│       ├── video-processing.png.png
│       ├── detection-results.png.png
│       ├── incident-history.png.png
│       └── web-dashboard.png.png
├── requirements.txt
└── README.md
```

---

## Installation

### Prerequisites

- Windows 10/11 or another supported Python environment.
- Python 3.10 or later, compatible with the installed dependencies.
- Git.
- Node.js and npm if you intend to run the web dashboard.
- A webcam for live monitoring.
- The YOLO model weights required by the application.

GPU acceleration depends on compatible hardware, drivers, and the installed PyTorch configuration. CPU inference may be available but can run more slowly.

### 1. Clone the Repository

```powershell
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd <YOUR_REPOSITORY_FOLDER>
```

Replace the placeholders with your actual GitHub repository URL and directory name.

### 2. Create a Virtual Environment

```powershell
python -m venv .venv
```

Activate it in PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Alternatively, use the virtual environment's Python executable directly.

### 3. Install Python Dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Verify the YOLO Model

If the model weights are included in the repository root, verify that the expected file exists:

```text
yolov8n.pt
```

If the weights are missing, use the model-loading or download procedure supported by the project.

### 5. Install Web Dashboard Dependencies

This step is optional if you only intend to use a desktop interface.

```powershell
cd frontend
npm install
cd ..
```

---

## Running the Application

### Option 1: PySide6 Desktop Application

From the repository root:

```powershell
.\.venv\Scripts\python.exe desktop_app_qt.py
```

### Option 2: Tkinter Desktop Application

```powershell
.\.venv\Scripts\python.exe desktop_app.py
```

### Option 3: FastAPI Backend

```powershell
.\.venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000
```

If the server starts successfully, the API base address is:

`http://127.0.0.1:8000`

Interactive API documentation is typically available at:

`http://127.0.0.1:8000/docs`

### Option 4: React + Vite Web Dashboard

Open a separate terminal:

```powershell
cd frontend
npm run dev
```

Open the local address printed by Vite. The default development address is commonly:

`http://localhost:5173`

Ensure the backend is running and the frontend API configuration points to the correct backend address.

---

## Usage Guide

### Live Camera Monitoring

1. Launch the PySide6 desktop application.
2. Open the live camera or monitoring view.
3. Grant camera access when requested.
4. Start monitoring.
5. Observe the camera feed and detection annotations.
6. Inspect any incident notifications generated by the system.
7. Stop monitoring when finished.
8. Open incident history to inspect saved records and associated evidence.

### Uploaded Video Processing

1. Launch the desktop application.
2. Open the video processing view.
3. Select a supported video file.
4. Start processing.
5. Monitor processing progress and annotated frames.
6. Wait for processing to complete.
7. Inspect the generated output if the workflow saves an annotated video.
8. Review any incidents and associated screenshots.

### Reviewing an Incident

1. Open the incident history or review view.
2. Select an incident.
3. Inspect its timestamp, event details, track association, and confidence value.
4. Open the evidence screenshot if available.
5. Evaluate the evidence in context.
6. Record the appropriate review status and notes using the available interface.

A missing screenshot or an unassigned track ID should be treated as missing information, not evidence of misconduct.

---

## Incident Management

Incident records may contain fields such as:

| Field | Description |
|---|---|
| Incident ID | Unique incident identifier |
| Timestamp | Time associated with the recorded event |
| Track ID | Associated tracked person, when confidently assigned |
| Event Type | Type of detection or event |
| Confidence | Model confidence for the relevant object detection |
| Screenshot Path | Location of the saved evidence image |
| Review Status | Current review state |
| Reviewer Notes | Human review notes, where supported |

The exact schema is determined by the database implementation.

### Confidence Is Not a Cheating Probability

A detection confidence score represents the model's confidence in its object detection. A high-confidence phone detection does not mean that a student is likely to have cheated.

---

## Testing

Run the automated test suite with pytest:

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

Depending on the current test suite, tests may cover:

- Database operations and migrations.
- Incident creation and retrieval.
- Incident review status and notes.
- Spatial association logic.
- Detection visualization.
- Video processing and cancellation.
- API endpoints and evidence access.
- Desktop application components.

The actual test coverage depends on the current test files and environment.

Automated tests do not automatically establish that every hardware-dependent workflow works on every machine. Live camera behavior, GPU acceleration, and full end-to-end workflows should also be verified in the target environment.

---

## Responsible AI and Privacy

ExamGuard is designed to support human review, not to make autonomous disciplinary decisions.

### Observations Are Not Proof

A detected phone or another flagged object is an observation that may justify further inspection. It does not prove that a student engaged in academic misconduct.

### Human Review Is Required

All potentially suspicious incidents should be reviewed in context by an authorized human proctor. Final decisions should account for the surrounding circumstances and available evidence.

### Confidence Scores Require Context

Object detection confidence is not a misconduct probability or a measure of intent.

### Identity Association Can Be Uncertain

Tracking and spatial association may fail because of occlusion, overlapping people, camera angles, or ambiguous object positions. Track IDs should not be treated as verified identities.

### Protect Camera Footage and Evidence

- Obtain appropriate consent and authorization before monitoring people.
- Clearly communicate when a camera is active.
- Restrict access to screenshots, recordings, and incident data.
- Avoid uploading sensitive footage to public repositories.
- Use synthetic or consented sample footage for demonstrations.
- Apply appropriate retention and deletion practices.

---

## Limitations and Future Improvements

Potential future improvements include:

- More robust detection under challenging lighting and camera angles.
- Improved person-object association in crowded scenes.
- Additional configurable event types.
- Performance optimization for lower-powered hardware.
- More comprehensive end-to-end and hardware integration tests.
- Improved deployment and packaging workflows.
- Expanded reporting and analytics.
- Stronger access control and evidence-retention management.

These are potential improvements, not claims that they are already implemented.

---

## Author

**Fares Elgohary**

ExamGuard was developed as a computer vision and AI-assisted monitoring project, combining object detection, multi-object tracking, evidence capture, and incident review interfaces.

---

<p align="center">
  <strong>ExamGuard</strong><br>
  AI-assisted monitoring. Evidence-based review. Human-led decisions.
</p>
