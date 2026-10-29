# 🚀 Instant AI Training — 1-Month Intensive AI Engineering Journey

<div align="center">

![AI Training Banner](https://img.shields.io/badge/Duration-1%20Month%20Intensive-blueviolet?style=for-the-badge)
![Projects](https://img.shields.io/badge/Projects-7%2B%20Completed-brightgreen?style=for-the-badge)
![Stack](https://img.shields.io/badge/Stack-Python%20%7C%20AI%20%7C%20ML%20%7C%20NLP-orange?style=for-the-badge)

</div>

---

## 📖 About This Repository

This repository documents a **1-month intensive AI engineering training program**, covering the full spectrum of modern Artificial Intelligence — from classical Machine Learning and Computer Vision to Large Language Models, NLP, and multi-agent AI systems.

Each project in this repo was built from scratch during the training, representing a real-world problem solved end-to-end using state-of-the-art AI tools and frameworks. Projects range from **data analysis dashboards** and **computer vision pipelines** to **fine-tuned transformer models** and **autonomous multi-agent platforms**.

> 💡 The training spans applied AI across multiple domains: **NLP**, **Computer Vision**, **Data Analytics**, **Agentic AI**, and **Enterprise Automation**.

---

## 🗂️ Projects Index

| # | Project | Domain | Stack | Status |
|---|---------|--------|-------|--------|
| 1 | [🏠 Airbnb Market Insights](#-airbnb-market-insights) | Data Analytics | Power BI | ✅ Complete |
| 2 | [👁️ OralSense AI](#-oralsense-ai) | Computer Vision | TensorFlow, Keras | ✅ Complete |
| 3 | [🛣️ RoadVision AI](#-roadvision-ai) | Computer Vision + Automation | YOLOv8, n8n, FastAPI | ✅ Complete |
| 4 | [🎓 ExamGuard AI](#-examguard-ai) | Computer Vision + Edge AI | YOLOv8, FastAPI, SQLite | ✅ Complete |
| 5 | [🤖 AgentFlow AI](#-agentflow-ai) | Multi-Agent AI | FastAPI, LLMs | ✅ Complete |
| 6 | [📋 IntelliComplaint AI](#-intellicomplaint-ai-cipher) | NLP + Transformers | DistilBERT, Gradio | ✅ Complete |
| 7 | More coming... | — | — | 🔄 In Progress |

---

## 🏠 Airbnb Market Insights

**Domain:** Business Intelligence & Data Analytics
**Folder:** [`Airbnb Market/`](./Airbnb%20Market/)

An interactive Power BI dashboard analyzing Airbnb market trends, pricing dynamics, and host performance metrics. Built to demonstrate data storytelling and BI engineering skills.

**Highlights:**
- 📊 Multi-page Power BI report with advanced DAX measures
- 🗺️ Geographic distribution of listings and pricing heatmaps
- 📈 Occupancy rate trends and seasonal demand analysis
- 🏆 Host performance benchmarking and rating breakdowns

---

## 👁️ OralSense AI

**Domain:** Computer Vision — Medical Imaging
**Folder:** [`OralSense AI/`](./OralSense%20AI/)

An AI-powered oral disease detection system trained to identify dental and oral health conditions from images using deep learning.

**Highlights:**
- 🦷 Custom CNN model trained for oral disease classification
- 🔬 Medical-grade image preprocessing pipeline
- 📱 Gradio-based interactive inference interface
- 🏋️ Fine-tuned model weights included

**Stack:** Python, TensorFlow/Keras, Gradio

---

## 🛣️ RoadVision AI

**Domain:** Computer Vision + Workflow Automation
**Folder:** [`RoadVision AI/`](./RoadVision%20AI/)

An automated road damage detection and reporting system that combines YOLOv8 object detection with n8n workflow automation for real-time infrastructure monitoring.

**Highlights:**
- 🚧 YOLOv8-based road damage detection (cracks, potholes, markings)
- 📡 Automated Telegram alert notifications on detections
- 🔄 n8n workflow integration for end-to-end automation
- 📊 Detection results dashboard and comparison analytics

**Stack:** Python, YOLOv8, n8n, FastAPI, Telegram Bot API

---

## 🎓 ExamGuard AI

**Domain:** Computer Vision + Real-Time Monitoring
**Folder:** [`ExamGuard — AI-Powered Exam Monitoring System/`](./ExamGuard%20—%20AI-Powered%20Exam%20Monitoring%20System/)

An AI-powered exam integrity monitoring system that uses computer vision to detect suspicious behavior during exams in real time, with a full web dashboard and alert system.

**Highlights:**
- 👀 Real-time student behavior detection (phone use, head turns, talking)
- 📹 Live camera feed processing with YOLO-based detection
- 🖥️ Web dashboard for live monitoring and incident review
- 🗃️ SQLite-backed incident logging and audit trail
- 🔔 Automated alert system for violations

**Stack:** Python, YOLOv8, FastAPI, SQLite, HTML/CSS/JS

---

## 🤖 AgentFlow AI

**Domain:** Multi-Agent AI Systems
**Folder:** [`AgentFlow-AI/`](./AgentFlow-AI/)

A sophisticated multi-agent AI workflow platform where autonomous agents collaborate to complete complex tasks. Demonstrates modern agentic AI patterns, inter-agent communication, and orchestrated LLM-powered pipelines.

**Highlights:**
- 🧠 Multi-agent orchestration with specialized role-based agents
- 🔗 Agent-to-agent communication and task delegation
- 🌐 REST API backend + interactive frontend
- 📋 Full test suite for agent workflow validation

**Stack:** Python, FastAPI, LLMs, HTML/CSS/JS

---

## 📋 IntelliComplaint AI (CIPHER)

**Domain:** NLP — Transformer Fine-Tuning
**Folder:** [`IntelliComplaint AI/`](./IntelliComplaint%20AI/)

An enterprise-grade consumer complaint intelligence platform powered by a fine-tuned **DistilBERT** transformer (66.9M parameters) trained on the CFPB consumer complaints dataset. Classifies financial complaints, scores regulatory urgency, routes to departments, and extracts monetary entities — all running fully offline with no external API dependencies.

**Highlights:**
- 🏆 **93%+ accuracy** on 18,645-sample held-out test set
- ⚡ **< 25ms inference** per complaint on CPU
- 🔍 5-class financial product classification (Credit Card, Credit Reporting, Debt Collection, Mortgages & Loans, Retail Banking)
- 🚨 Regulatory urgency scoring: `CRITICAL` / `HIGH` / `MODERATE` / `STANDARD`
- 🏛️ Automated departmental routing with SLA guidance
- 📁 High-throughput batch CSV processing
- 🔒 Privacy-preserving: no data persisted to disk automatically
- 📊 Session analytics, audit trail, and benchmark leaderboard

**Model:** DistilBERT-base-uncased (fine-tuned) — weights stored via **Git LFS**

**Stack:** Python, PyTorch, HuggingFace Transformers, Gradio, Plotly, Pandas

---

## 🛠️ Tech Stack Overview

```
Languages:    Python 3.10+, JavaScript, SQL
AI/ML:        PyTorch, TensorFlow/Keras, HuggingFace Transformers, YOLOv8
NLP:          DistilBERT, Tokenizers, Transformers
CV:           YOLOv8, OpenCV, TensorFlow
Interfaces:   Gradio, FastAPI, HTML/CSS/JS
Data/BI:      Power BI, Pandas, Plotly, SQLite
Automation:   n8n, Telegram Bot API
Testing:      Pytest
Deployment:   Git LFS (for large model weights)
```

---

## 📈 Training Journey

This repository is the output of a structured 1-month AI engineering intensive covering:

- **Week 1:** Data Analysis, Business Intelligence & Visualization (Power BI, Python)
- **Week 2:** Computer Vision — Object Detection, Medical Imaging, Real-Time Systems
- **Week 3:** Agentic AI — Multi-Agent Workflows, LLM Orchestration, API Design
- **Week 4:** NLP & Transformers — Fine-Tuning, Deployment, Enterprise AI Systems

> 🔄 **More projects are being added as the training continues...**

---

## 👤 Author

**Fares Elgohary**
[![GitHub](https://img.shields.io/badge/GitHub-fareselgohary2003-181717?style=flat&logo=github)](https://github.com/fareselgohary2003)

---

<div align="center">
<sub>Built with ❤️ during an intensive 1-month AI engineering training program.</sub>
</div>