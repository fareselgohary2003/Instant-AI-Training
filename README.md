# CIPHER — Consumer Complaint Intelligence Platform

[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11-blue.svg)](https://www.python.org/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0+-ee4c2c.svg)](https://pytorch.org/)
[![HuggingFace](https://img.shields.io/badge/Transformers-DistilBERT-yellow.svg)](https://huggingface.co/)
[![Gradio](https://img.shields.io/badge/Gradio-6.0+-ff7c00.svg)](https://gradio.app/)
[![License](https://img.shields.io/badge/License-Proprietary-red.svg)]()

> **Enterprise AI platform for automated triage, categorization, and decision support for consumer financial complaints.** Powered by a fine-tuned DistilBERT transformer loaded strictly from local weights without external API dependencies.

---

## 📌 Executive Summary

Financial institutions and regulatory authorities receive tens of thousands of complex, unstructured consumer complaints each month across mortgages, credit reporting, debt collection, credit cards, and retail banking. Manually routing these grievances is slow, error-prone, and creates substantial compliance liability.

**CIPHER (Consumer Complaint Intelligence)** provides an end-to-end operational suite:
1. **Instant Complaint Diagnosis:** Classifies unstructured consumer narratives into one of five financial product categories in under 25 milliseconds.
2. **AI Regulatory Urgency & Risk Scoring:** Scans for CFPB, litigation, fraud, bankruptcy, and harassment triggers, classifying grievances into `🚨 CRITICAL`, `⚠️ HIGH`, `🟡 MODERATE`, and `🟢 STANDARD` with tailored SLA resolution windows.
3. **Automated Departmental Routing & Action Checklists:** Maps complaints directly to operational divisions (e.g., *Bureau Liaison & Fraud SIU*, *Fair Debt Taskforce*, *Mortgage Escrow Appeals*) with step-by-step remediation guidance.
4. **Financial Entity & Trigger Discovery:** Automatically extracts disputed monetary amounts (`$400`, `$1,500`) and regulatory trigger chips.
5. **Cross-Department Grievance Detection:** Detects multi-product complaints when top confidence margin is narrow.
6. **High-Throughput Batch Triage:** Ingests CSV files, auto-detects narrative columns, and enriches datasets with predictions, risk categories, target departments, and class distributions.
7. **Privacy-Preserving Audit Trail:** Maintains session telemetry entirely in volatile memory; customer data is never written to disk without explicit user export.

---

## 🗂️ Classification Categories

CIPHER classifies narratives into five standard financial categories:

| Internal Model Key | Clean Display Name | Operational Scope & Typical Grievances |
| :--- | :--- | :--- |
| `credit_card` | **Credit Card** | Billing disputes, APR spikes, rewards errors, unauthorized card charges, fee waivers. |
| `credit_reporting` | **Credit Reporting** | Incorrect bureau trade lines, identity theft disputes, TransUnion/Equifax/Experian errors. |
| `debt_collection` | **Debt Collection** | Harassment, calls to workplaces, zombie/time-barred debts, failure to validate debt. |
| `mortgages_and_loans` | **Mortgages & Loans** | Escrow calculation errors, refinancing delays, loan modification disputes, foreclosure notices. |
| `retail_banking` | **Retail Banking** | Checking/savings holds, ATM cash dispensing failures, wire delays, overdraft fees. |

---

## 🏆 Verified Model Evaluation & Benchmark

The underlying model is a fine-tuned `distilbert-base-uncased` sequence classifier trained on over 160,000 real-world financial complaints.

### Test Set Benchmark (18,645 Untouched Test Complaints)

| Metric | DistilBERT Fine-Tuned | GRU Recurrent Baseline | Relative Improvement |
| :--- | :---: | :---: | :---: |
| **Accuracy** | **86.50%** | 85.21% | +1.29% |
| **Weighted F1-Score** | **86.47%** | 85.19% | +1.28% |
| **Weighted Precision** | **86.48%** | 85.20% | +1.28% |
| **Weighted Recall** | **86.50%** | 85.21% | +1.29% |

### Per-Category Performance Breakdown (DistilBERT)

| Category | Precision | Recall | F1-Score | Test Support |
| :--- | :---: | :---: | :---: | :---: |
| **Credit Card** | 80.42% | 83.61% | 81.98% | 2,245 |
| **Credit Reporting** | 89.09% | 90.55% | 89.82% | 8,426 |
| **Debt Collection** | 82.10% | 77.90% | 79.94% | 3,149 |
| **Mortgages & Loans** | 87.47% | 84.60% | 86.01% | 2,805 |
| **Retail Banking** | 87.73% | 88.86% | 88.29% | 2,020 |

---

## 🏛️ Application Architecture

```
cipher_model/
│
├── app.py                      # Main Gradio application & UI dashboard
│
├── src/
│   ├── __init__.py             # Package descriptor
│   ├── model_service.py        # Local DistilBERT inference engine (CPU/CUDA)
│   └── analytics.py            # Session telemetry, CSV batching & Plotly charts
│
├── models/
│   └── best-distilbert-complaints/
│       ├── config.json         # Architecture definition & label mappings
│       ├── model.safetensors   # Fine-tuned DistilBERT weights (268 MB)
│       ├── model_metadata.json # Training metrics & hyperparameters
│       ├── tokenizer.json      # Fast WordPiece tokenizer vocabulary
│       ├── tokenizer_config.json
│       └── training_args.bin
│
├── assets/
│   └── sample_complaints.csv   # Synthetic multi-category demonstration dataset
│
├── tests/
│   ├── __init__.py
│   ├── test_model_service.py   # Unit & integration tests for model loading & math
│   └── test_analytics.py       # Unit tests for CSV ingestion, batching & charts
│
├── requirements.txt            # Minimal verified production dependencies
├── .env.example                # Configurable server & device parameters
├── .gitignore                  # Clean repository filters
├── README.md                   # Complete documentation
└── notebook6caffa8944.ipynb    # Original Kaggle training notebook (preserved)
```

---

## 💻 Windows Setup & Local Execution Guide

### 1. Verify Installed Python Version
Open PowerShell or Command Prompt and verify you are running **Python 3.10** or **3.11**:
```powershell
python --version
```

### 2. Create and Activate Virtual Environment
Initialize an isolated virtual environment in the project directory:
```powershell
# Create virtual environment
python -m venv .venv

# Activate in PowerShell
.\.venv\Scripts\Activate.ps1

# (If PowerShell blocks script execution, run this once: Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass)
```

### 3. Install Dependencies
Install the required packages from `requirements.txt`:
```powershell
pip install -r requirements.txt
```

### 4. GPU Acceleration Setup (Optional for NVIDIA GPUs)
CIPHER runs smoothly on **CPU** by default. If your machine is equipped with an NVIDIA GPU (e.g., RTX 2060, RTX 3060, etc.) and you wish to enable hardware CUDA acceleration:
```powershell
# Install PyTorch with CUDA 12.4 support
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124
```
Verify device availability:
```powershell
python -c "import torch; print('CUDA Available:', torch.cuda.is_available(), '| Device:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU')"
```

### 5. Run Automated Smoke Tests
Validate that model weights load correctly from local disk, label mappings align, and batch processing functions as expected:
```powershell
pytest -v tests/
```
*Expected: 11 passed in ~7 seconds.*

### 6. Launch the Dashboard
Start the local server:
```powershell
python app.py
```
Open your web browser and navigate to:
```
http://127.0.0.1:7860
```

---

## 🎨 Professional Dashboard Sections

CIPHER features an executive dark theme tailored for decision analysts:
- **Background:** Dark Aubergine (`#160d1b`)
- **Surfaces & Cards:** Warm Aubergine (`#22142c`) with subtle borders
- **Primary Typography:** Warm Ivory (`#f7f4ed`)
- **Key Accents:** Electric Lime (`#b6f028`), Muted Coral (`#ff7262`), Restrained Lavender (`#9d8ec2`)

### 1. 📊 Overview
- Real-time KPI metric boxes: Total complaints analyzed, distinct categories identified, average uncalibrated probability, and average latency.
- Dynamic session-level category distribution bar chart.
- Quick preview table of recent session predictions.

### 2. 🔍 Complaint Analyzer
- Free-form text area for typing or pasting narrative complaints.
- Five instant demonstration scenario buttons representing real consumer cases.
- Primary **Analyze Complaint** and **Reset** triggers.
- Prominent prediction card displaying category name, probability percentage, internal key, and token sequence count.
- Horizontal probability distribution chart across all 5 categories.
- Tabular rank and probability breakdown.

### 3. 📁 Batch Processing
- Drag-and-drop CSV upload (supports files up to 100,000+ rows).
- Automatic complaint column detection (suggests `narrative`, `complaint`, `text`, etc.).
- Configurable mini-batch size slider (8 to 128) optimized for 16 GB RAM laptops.
- Interactive 25-row results preview table.
- One-click **Download Enriched Prediction CSV** containing original data plus predicted categories, top probabilities, and individual class distributions.

### 4. 📈 History & Analytics
- Complete chronological audit log of all predictions made during the session.
- Category distribution analytics.
- **Export Session History to CSV** button for regulatory recordkeeping.
- **Clear Session History** button.

### 5. ℹ️ Model Information
- Complete architectural parameters, parameter counts, and saved weight locations.
- Active device telemetry (CUDA GPU vs CPU).
- Verified Kaggle test set evaluation tables and per-category precision/recall metrics.
- Compliance, intended use, and limitations disclosure.

---

## 🔒 Privacy & Data Protection

- **Local Execution:** 100% of inference runs locally. No complaint text or metadata is sent to OpenAI, Hugging Face, or any external cloud API.
- **In-Memory History:** Session history is held exclusively in RAM. Complaints are never automatically saved to persistent disk.
- **No Weight Retraining:** Model weights (`model.safetensors`) are read-only and preserved permanently.

---

## ⚖️ Legal & Decision-Support Disclaimer

> **CIPHER is an assistive decision-support tool, not an automated financial, legal, or regulatory adjudicator.**
> Model probabilities reflect raw softmax outputs from supervised training on historical complaints and are uncalibrated. Output predictions can be inaccurate and must be reviewed by qualified human compliance officers or customer specialists before taking regulatory, legal, or financial action.
