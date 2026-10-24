# RoadVision AI — Intelligent Road Damage Detection & Automation

An AI-powered road damage detection and workflow automation system that integrates computer vision, a web dashboard, FastAPI, n8n, PostgreSQL, and Telegram notifications.

RoadVision AI uses a trained YOLOv8 object detection model to analyze uploaded road images and detect potholes, cracks, and manholes. Detection results are processed by a FastAPI backend and forwarded to an n8n workflow for automated processing, database storage, and Telegram notifications.

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
- [Security](#security)
- [Future Improvements](#future-improvements)
- [Author](#author)

## Overview

RoadVision AI demonstrates how computer vision can be integrated with backend services and workflow automation to create an end-to-end road damage analysis pipeline.

Users can upload road images through a web dashboard, run AI-powered object detection, and view the detection results. The backend sends structured detection data to an n8n webhook, where conditional logic connects the detection process with PostgreSQL storage and Telegram notifications.

The project combines AI inference, API development, frontend development, workflow orchestration, database integration, and messaging automation.

## Key Features

- **AI-Powered Detection:** Detects potholes, cracks, and manholes in uploaded road images.
- **Interactive Dashboard:** Provides a web interface for uploading images and viewing detection results.
- **YOLOv8 Model Integration:** Uses trained model weights for object detection.
- **FastAPI Backend:** Handles application requests and detection processing.
- **Webhook Integration:** Transfers structured detection data to n8n.
- **Conditional Workflow Automation:** Routes detection data through configured workflow logic.
- **PostgreSQL Integration:** Stores detection records in a relational database.
- **Telegram Notifications:** Sends automated notifications through a Telegram bot.
- **End-to-End Integration:** Connects computer vision, backend processing, workflow automation, database storage, and messaging.

## Screenshots

### Web Dashboard

The main interface for interacting with RoadVision AI.

![RoadVision AI Dashboard](screenshots/dashboard-ui.png.png)

### Road Damage Detection Results

An example of the detection interface and model output.

![Road Damage Detection Results](screenshots/detection-results.png.png)

### Image Upload Interface

The interface used to submit road images for analysis.

![RoadVision AI Image Upload](screenshots/upload-interface.png.png)

### n8n Automation Workflow

The workflow connecting the backend to conditional processing, PostgreSQL, and Telegram.

![RoadVision AI n8n Workflow](screenshots/n8n-workflow.png.png)

### Telegram Notification

An example of the automated Telegram notification.

![RoadVision AI Telegram Notification](screenshots/telegram-notification.png.png)

## System Architecture

The application follows an integrated processing pipeline:

1. **Image Upload:** The user uploads a road image through the web dashboard.
2. **AI Inference:** The trained YOLOv8 model analyzes the image and identifies supported classes.
3. **Backend Processing:** FastAPI handles the request and prepares detection results.
4. **Webhook Communication:** The backend sends structured data to the configured n8n webhook.
5. **Workflow Processing:** n8n receives the payload and applies the configured conditional logic.
6. **Database Storage:** Detection information is stored in PostgreSQL.
7. **Telegram Notification:** The workflow sends a notification according to its configured conditions.

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
| Model Training | Kaggle Notebook with GPU |
| Backend API | FastAPI |
| Frontend | HTML, CSS, JavaScript |
| API Integration | REST API and Webhooks |
| Workflow Automation | n8n Cloud |
| Database | PostgreSQL |
| Notifications | Telegram Bot API |
| Version Control | Git and GitHub |

## Supported Detection Classes

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
│   ├── dashboard-ui.png.png
│   ├── detection-results.png.png
│   ├── upload-interface.png.png
│   ├── n8n-workflow.png.png
│   └── telegram-notification.png.png
└── n8n/
    └── roadvision-workflow.json
```

## Installation

### Prerequisites

- Python
- pip
- The trained YOLOv8 model weights
- An accessible n8n instance or n8n Cloud account
- PostgreSQL database configuration
- Telegram bot configuration

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

If the model weights are hosted separately, download them and place them at the expected path before running inference.

### 5. Configure the Automation Workflow

Configure the n8n workflow with the required webhook, PostgreSQL connection, and Telegram bot credentials.

Keep credentials in the appropriate secure configuration fields. Do not commit API keys, bot tokens, passwords, or private webhook URLs to GitHub.

## Running the Application

From the project directory, start the FastAPI server.

If the FastAPI application instance in `main.py` is named `app`, run:

```bash
uvicorn main:app --reload
```

Open the local URL displayed in the terminal. The dashboard route depends on the application's configuration.

For end-to-end automation, ensure the n8n workflow is active and its integrations are configured correctly.

## Workflow Automation

The n8n workflow connects model output to downstream automation.

Its configured responsibilities include:

- Receiving detection data through a webhook.
- Processing structured detection information.
- Applying conditional logic.
- Storing detection records in PostgreSQL.
- Sending Telegram notifications according to workflow conditions.

The workflow can be exported as JSON for version control, documentation, and reuse. Credentials should be configured separately after importing the workflow.

## Model Training

The object detection model was trained using a Kaggle Notebook with GPU acceleration. The trained weights are used by the backend to perform inference on uploaded images.

The model supports three classes: potholes, cracks, and manholes.

This repository focuses on the deployment and integration pipeline, including the web dashboard, backend API, and workflow automation.

## Security

Before deploying or sharing the project:

- Never commit Telegram bot tokens, database passwords, or private API keys.
- Do not publish `.env` files containing secrets.
- Review exported n8n workflow files for credentials and private webhook URLs.
- Keep virtual environments, caches, and temporary files out of version control.
- Avoid including sensitive information in screenshots, logs, or sample payloads.
- If `best.pt` exceeds GitHub's standard 100 MB file limit, use Git LFS or external model hosting.

## Future Improvements

Potential extensions include:

- Real-time road damage detection from video streams.
- Geolocation tagging for detected defects.
- Historical detection analytics and reporting.
- Road damage severity estimation and prioritization.
- Map-based visualization of road defects.
- Cloud deployment and integration with road maintenance systems.

## Author

**Fares Elgohary**

AI Agentic & Automation Engineer

- **GitHub:** [fareselgohary2003](https://github.com/fareselgohary2003)
- **LinkedIn:** [Fares Elgohary](https://www.linkedin.com/in/fares-elgohary-91ba22380/)
- **Kaggle:** [elgohary249](https://www.kaggle.com/elgohary249)

---

RoadVision AI demonstrates the integration of computer vision and AI inference with backend API development, workflow automation, database storage, and messaging integrations.
