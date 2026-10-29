# IntelliComplaint AI
### Intelligent Customer Complaint Classification & Analytics Platform

IntelliComplaint AI is an AI-powered platform designed to automatically classify consumer financial complaints using Natural Language Processing (NLP) and Deep Learning.

The platform combines automated text classification, batch complaint processing, model benchmarking, classification reports, and interactive analytics to help transform unstructured customer complaints into structured, actionable insights.

## Overview

Financial institutions receive large volumes of customer complaints across multiple products and services. Manually reviewing and categorizing these complaints can be time-consuming and inconsistent.

IntelliComplaint AI addresses this challenge by applying machine learning and transformer-based NLP models to classify complaint narratives into predefined categories, evaluate model performance, and provide an interactive interface for analyzing individual complaints and batches of data.

## Key Features

- **AI-Powered Classification:** Automatically predicts the category of a customer complaint from its text.
- **Five Complaint Categories:** Supports credit cards, credit reporting, debt collection, mortgages and loans, and retail banking.
- **Interactive Complaint Analyzer:** Submit individual complaint narratives and review the predicted category and confidence score.
- **Batch Processing:** Upload CSV files to classify multiple complaints in a single workflow.
- **Model Benchmarking:** Compare multiple deep learning architectures and a transformer-based model.
- **Classification Reports:** Examine class-level evaluation metrics and confusion matrices.
- **Executive Dashboard:** Review complaint statistics, category distributions, processing activity, and performance indicators.
- **Session Audit Trail:** Inspect recorded classification and processing activity.
- **Inference Monitoring:** Display processing latency and other available operational metrics.

## Machine Learning Models

The project evaluates four neural network architectures for text classification.

| Model | Architecture |
|---|---|
| SimpleRNN | Recurrent Neural Network |
| LSTM | Long Short-Term Memory Network |
| GRU | Gated Recurrent Unit |
| DistilBERT | Transformer-based language model |

The models provide a basis for comparing conventional recurrent neural networks with a pretrained transformer architecture on consumer complaint classification.

## Dataset

The project uses the Consumer Complaint Classification dataset available through Kaggle.

**Dataset source:** [Consumer Complaints Dataset for NLP](https://www.kaggle.com/datasets/shashwatwork/consume-complaints-dataset-fo-nlp)

The dataset contains complaint narratives paired with product categories.

### Target Classes

The classification task contains five categories:

| Label | Description |
|---|---|
| `credit_card` | Complaints related to credit cards |
| `credit_reporting` | Complaints related to credit reporting |
| `debt_collection` | Complaints related to debt collection |
| `mortgages_and_loans` | Complaints related to mortgages and loans |
| `retail_banking` | Complaints related to retail banking services |

### Data Preparation

The training workflow includes data preparation and text-processing steps intended to improve the reliability of model evaluation.

These steps include handling missing values, removing duplicate complaint narratives, addressing conflicting labels, splitting the data into training, validation, and test sets, and preparing text for neural network or transformer-based models.

The exact preprocessing configuration depends on the model and training pipeline.

## Model Evaluation

The platform includes a model benchmarking interface and a classification report for examining predictive performance.

Recommended evaluation metrics include:

- Accuracy
- Precision
- Recall
- F1-score
- Per-class performance
- Confusion matrix

The project has displayed benchmark results of approximately **86.85% accuracy for DistilBERT** and **85.75% for GRU** in the dashboard. These values should be checked against the final saved evaluation results before being treated as definitive results.

Performance may vary with preprocessing, dataset splits, model checkpoints, and evaluation settings. All reported metrics should correspond to the same documented test set when comparing models.

## Application Modules

### 1. Executive Overview
Provides a high-level view of complaint processing activity, category distributions, and available operational statistics.

### 2. Complaint Analyzer
Accepts an individual complaint narrative and presents the predicted category, confidence score, and other available classification insights.

### 3. Batch Ingestion & Triage
Processes complaint datasets in CSV format and presents batch-level summaries and individual predictions.

### 4. Model Benchmark
Provides a comparative view of the evaluated neural network and transformer models.

### 5. Classification Report
Displays classification metrics and a confusion matrix to support a more detailed evaluation of model performance.

### 6. Session Audit Trail
Provides a view of recorded session activity and classification operations.

## Technology Stack

The project uses a Python-based machine learning workflow and a dashboard for interactive analysis.

| Technology | Purpose |
|---|---|
| Python | Core programming language |
| PyTorch | Deep learning model development and inference |
| Hugging Face Transformers | Transformer-based NLP modeling |
| DistilBERT | Contextual text representation and classification |
| pandas | Dataset processing and tabular analysis |
| Gradio / dashboard components | Interactive application interface, where applicable |
| Plotly | Interactive data visualization, where configured |
| scikit-learn | Model evaluation and classification metrics, where configured |

The exact dependencies should be confirmed against the repository's dependency files.

## Project Workflow

1. Load and prepare the complaint dataset.
2. Clean the data and prepare the target labels.
3. Split the data into training, validation, and test sets.
4. Train or load the supported classification models.
5. Evaluate model performance using consistent evaluation metrics.
6. Submit individual complaints or upload a CSV batch.
7. Generate predictions and available confidence scores.
8. Review classification results, model comparisons, and dashboard analytics.

## Installation

### Prerequisites

- Python 3.10 or later, subject to the versions supported by the project dependencies.
- Git
- A compatible environment for the selected PyTorch and Transformers versions.

### 1. Clone the repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd <YOUR_REPOSITORY_FOLDER>
```

### 2. Create a virtual environment

Windows:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

If the repository includes a `requirements.txt` file:

```bash
python -m pip install -r requirements.txt
```

### 4. Run the application

Use the application entry point and launch command documented in the repository.

The exact command depends on how the dashboard and inference pipeline are packaged. Refer to the project's source files and configuration before launching the application.

## Usage

### Single Complaint Classification

1. Open the dashboard.
2. Navigate to the Complaint Analyzer.
3. Enter a customer complaint narrative.
4. Submit the text for analysis.
5. Review the predicted category and confidence score.
6. Inspect any additional insights provided by the application.

### Batch Complaint Classification

1. Open Batch Ingestion & Triage.
2. Upload a supported CSV file.
3. Confirm that the complaint text column is detected correctly.
4. Process the dataset.
5. Review the predictions and batch summary.

Use the column names supported by the actual CSV ingestion implementation.

### Model Evaluation

1. Open Model Benchmark to compare available models.
2. Review the Classification Report.
3. Inspect the confusion matrix and per-class metrics.
4. Compare results using the same evaluation split and metric definitions.

## Responsible Use and Limitations

- Predictions are model-generated estimates, not guaranteed determinations.
- Confidence scores represent model confidence and should not automatically be interpreted as calibrated probabilities.
- Model performance depends on dataset quality, class distribution, preprocessing, and the evaluation methodology.
- Risk levels, recommended teams, and service-level targets should only be interpreted as operational guidance when their rules are documented and validated.
- Sensitive customer information should be handled according to applicable privacy and data-protection requirements.
- Human review is recommended for ambiguous, high-impact, or incorrectly classified complaints.

## Future Improvements

Potential extensions include:

- Probability calibration and confidence-based review thresholds.
- Explainability tools for understanding classification decisions.
- Model versioning and reproducible experiment tracking.
- Additional language support and multilingual complaint classification.
- Production API integration and database persistence.
- Monitoring for data drift and model performance degradation.
- Automated evaluation pipelines and regression testing.

These are potential extensions rather than claims about currently implemented functionality.

## Project Goals

IntelliComplaint AI demonstrates the application of NLP and deep learning to a practical text-classification problem. It combines model experimentation with an interactive analytics workflow, providing a foundation for further development toward reliable, scalable complaint intelligence systems.

## License

Choose and add an appropriate open-source license before distributing the project. Ensure that the dataset and any third-party model checkpoints are used according to their respective licenses and terms.

---

**IntelliComplaint AI — Turning Customer Complaints into Structured Intelligence.**
