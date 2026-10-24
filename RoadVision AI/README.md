# RoadVision AI — Intelligent Road Damage Detection & Automation

An end-to-end AI-powered road damage detection and workflow automation system that combines computer vision, a web dashboard, REST API development, database integration, and automated Telegram notifications.

RoadVision AI uses a trained YOLOv8 object detection model to analyze uploaded road images and detect potholes, cracks, and manholes. Detection results are processed by a FastAPI backend and forwarded to an n8n automation workflow for conditional processing, PostgreSQL storage, and Telegram notifications.

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Screenshots](#screenshots)
- [System Architecture](#system-architecture)
- [Technology Stack](#technology-stack)
- [Supported Detection Classes](#supported-detection-classes)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Running the Application](#running-the-application)
- [Workflow Automation](#workflow-automation)
- [Model Training](#model-training)
- [Security Considerations](#security-considerations)
- [Future Improvements](#future-improvements)
- [Author](#author)

## Overview

RoadVision AI demonstrates how computer vision can be integrated with backend services and workflow automation to create a practical road damage analysis pipeline.

The application allows users to upload road images through a web interface, run object detection using a trained YOLOv8 model, and view the detection results. The backend then forwards structured detection data to an n8n webhook, where automation logic connects the detection process with PostgreSQL and Telegram.

The project brings together AI inference, API development, frontend development, workflow orchestration, database operations, and messaging integrations in one solution.

## Key Features

- **AI-Powered Object Detection:** Detects potholes, cracks, and manholes in uploaded road images.
- **Interactive Web Dashboard:** Provides a user interface for image uploads and viewing detection results.
- **YOLOv8 Model Integration:** Uses trained model weights for road image inference.
- **FastAPI Backend:** Handles application requests and detection processing.
- **Webhook Integration:** Transfers structured detection results from the backend to n8n.
- **Conditional Workflow Automation:** Processes detection information according to configured workflow conditions.
- **PostgreSQL Integration:** Stores detection records through the automation workflow.
- **Telegram Notifications:** Sends automated notifications through a Telegram bot.
- **End-to-End Pipeline:** Connects AI inference, API processing, workflow automation, database storage, and notifications.

## Screenshots

### Web Dashboard

The main interface for interacting with RoadVision AI.

![RoadVision AI Dashboard](screenshots/dashboard-ui.png)

### Road Damage Detection Results

Example of the detection interface and model output.

![Road Damage Detection Results](screenshots/detection-results.png)

### Image Upload Interface

The interface used to submit road images for analysis.

![RoadVision AI Image Upload](screenshots/upload-interface.png)

### n8n Automation Workflow

The workflow connecting the detection backend to conditional processing, PostgreSQL, and Telegram.

![RoadVision AI n8n Workflow](screenshots/n8n-workflow.png)

### Telegram Notification

Example of the Telegram conversation displaying an automated notification.

![RoadVision AI Telegram Notification](screenshots/telegram-notification.png)

## System Architecture

The application follows an integrated processing pipeline:

1. **Image Input:** The user uploads a road image through the web dashboard.
2. **Model Inference:** The trained YOLOv8 model analyzes the image and identifies supported classes.
3. **Backend Processing:** FastAPI handles the request and prepares the detection results.
4. **Webhook Communication:** The backend sends structured data to the configured n8n webhook.
5. **Workflow Processing:** n8n receives the payload and executes the configured conditional logic.
6. **Database Integration:** The workflow stores detection information in PostgreSQL.
7. **Telegram Notification:** The workflow sends a notification through Telegram according to its configured conditions.

```text
Road Image
    |
    v
Web Dashboard
    |
    v
FastAPI Backend
    |
    v
YOLOv8 Detection
    |
    v
Structured Detection Results
    |
    v
n8n Webhook
    |
    v
Conditional Workflow Logic
    |
    +--------------------+
    |                    |
    v                    v
PostgreSQL          Telegram Bot
Detection Records   Notifications
```

## Technology Stack

| Component | Technology |
|---|---|
| Programming Language | Python |
| Object Detection | YOLOv8 |
| Model Framework | Ultralytics |
| Model Training Environment | Kaggle Notebook with GPU |
| Backend | FastAPI |
| Frontend | HTML, CSS, JavaScript |
| API Integration | REST API and Webhooks |
| Workflow Automation | n8n Cloud |
| Database | PostgreSQL |
| Notifications | Telegram Bot API |
| Version Control | Git and GitHub |

## Supported Detection Classes

The trained model is configured to detect the following classes:

| Class | Description |
|---|---|
| Pothole | Road surface holes and localized pavement damage |
| Crack | Visible cracks in road surfaces |
| Manhole | Manholes and related road-surface structures |

Detection results depend on the trained model, input image quality, and inference configuration.

## Project Structure

```text
road_damage_deployment/
├── main.py
├── best.pt
├── requirements.txt
├── README.md
├── .gitignore
├── static/
│   ├── app.js
│   ├── index.html
│   └── style.css
├── screenshots/
│   ├── dashboard-ui.png
│   ├── detection-results.png
│   ├── upload-interface.png
│   ├── n8n-workflow.png
│   └── telegram-notification.png
└── n8n/
    └── roadvision-workflow.json
```

The project structure above represents the intended repository layout. The `best.pt` file contains the trained model weights. The `screenshots/` directory contains the project demonstration images, and the `n8n/` directory can contain an exported workflow for reference and reuse.

## Installation

### Prerequisites

- Python installed on your machine.
- pip for Python package installation.
- The trained YOLOv8 model weights.
- Access to the configured n8n workflow.
- PostgreSQL database configuration.
- Telegram bot configuration for notifications.

### 1. Clone the Repository

```bash
git clone https://github.com/fareselgohary2003/RoadVision-AI.git
cd RoadVision-AI
```

### 2. Create a Virtual Environment

On Windows:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

On macOS or Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure the Model

Ensure that `best.pt` is available at the model path expected by the application.

If the trained weights are hosted separately rather than included in the repository, download them and place them at the expected path before running inference.

### 5. Configure Workflow Integrations

The n8n workflow requires valid configuration for the webhook, PostgreSQL connection, and Telegram bot.

Configure credentials securely within n8n. Ensure that the backend points to the correct webhook endpoint using the configuration expected by the application.

## Running the Application

Start the FastAPI server from the project directory.

If the FastAPI application instance is named `app` in `main.py`, run:

```bash
uvicorn main:app --reload
```

Open the local URL displayed in the terminal. The dashboard route depends on the application's FastAPI configuration.

Keep the backend running while using the dashboard. For end-to-end automation, ensure the n8n workflow is active and its integrations are configured correctly.

## Workflow Automation

The n8n workflow is responsible for connecting model output to downstream automation.

Its configured responsibilities include:

- Receiving detection data through a webhook.
- Processing structured detection information.
- Applying conditional logic.
- Saving detection records to PostgreSQL.
- Sending Telegram notifications according to the workflow configuration.

The workflow can be exported as a JSON file and included in the repository for technical reference. Credentials and environment-specific values should be configured separately after importing the workflow.

## Model Training

The object detection model was trained in a Kaggle Notebook using GPU acceleration. The resulting trained weights are used by the application to perform inference on uploaded images.

The model supports three detection classes: potholes, cracks, and manholes.

This repository focuses on the deployment and integration pipeline, including the web interface, backend API, and workflow automation.

## Security Considerations

Before deploying or sharing the project:

- Never commit Telegram bot tokens, database passwords, or private API keys.
- Do not publish `.env` files containing secrets.
- Review exported n8n workflow JSON files for credentials and private webhook URLs.
- Keep local virtual environments and temporary files out of version control.
- Avoid publishing sensitive information in screenshots, logs, or sample payloads.
- If `best.pt` exceeds GitHub's standard 100 MB file limit, use Git Large File Storage (Git LFS) or external model hosting.

## Future Improvements

Potential extensions include:

- Real-time road damage detection from video streams.
- Geolocation tagging for detected defects.
- Historical detection analytics and reporting.
- Road damage severity estimation and prioritization.
- Map-based visualization of detected road defects.
- Cloud deployment and integration with road maintenance systems.

## Author

**Fares Elgohary**

AI Agentic & Automation Engineer

- **GitHub:** [fareselgohary2003](https://github.com/fareselgohary2003)
- **LinkedIn:** [Fares Elgohary](https://www.linkedin.com/in/fares-elgohary-91ba22380/)
- **Kaggle:** [elgohary249](https://www.kaggle.com/elgohary249)

---

RoadVision AI demonstrates the integration of computer vision and AI inference with backend API development, workflow automation, database storage, and messaging integrations.
