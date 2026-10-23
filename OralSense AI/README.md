# OralSense AI

**AI-Powered Oral Disease Classification Using Deep Learning**

OralSense AI is a web-based computer vision application that analyzes oral images and predicts one of five trained categories using a MobileNetV2 deep learning model. Built with TensorFlow, Keras, and Gradio, it provides an interactive interface for image classification and prediction visualization.

## Features

- **AI-Based Image Classification:** Predicts the category of an uploaded oral image.
- **Five Classification Categories:** Dental calculus, oral cancer, dental caries, gingivitis, and oral ulcer.
- **Deep Learning:** Uses a MobileNetV2-based image classification model.
- **Interactive Web Interface:** Upload images and view classification results through Gradio.
- **Prediction Visualization:** Displays model predictions and the predicted category.
- **Simple Deployment:** Runs locally with Python and the required dependencies.

## Supported Categories

| Category | Description |
|---|---|
| Calculus | Dental calculus classification |
| Cancer | Oral cancer classification |
| Caries | Dental caries classification |
| Gingivitis | Gum inflammation classification |
| Ulcer | Oral ulcer classification |

## Tech Stack

- Python
- TensorFlow
- Keras
- MobileNetV2
- Computer Vision
- Deep Learning
- Gradio
- NumPy
- Pillow

## Project Structure

```text
OralSense-AI/
├── app.py
├── config.json
├── metadata.json
├── model.weights.h5
├── requirements.txt
├── .gitignore
└── README.md
```

## Getting Started

### Prerequisites

- Python 3.11
- Git

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/OralSense-AI.git
cd OralSense-AI
```

### 2. Create a Virtual Environment

**Windows:**

```bash
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install Dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Run the Application

```bash
python app.py
```

Open the local URL displayed in the terminal, usually:

`http://127.0.0.1:7860`

## How to Use

1. Launch the application.
2. Upload an oral image using the image input component.
3. Click **Run Analysis**.
4. Review the predicted category and the displayed classification results.

## Model Information

The application uses a MobileNetV2-based deep learning model for five-class image classification. Input images are resized to 224 × 224 pixels before inference.

The model's predictions depend on its training data, image quality, and the similarity between uploaded images and the training distribution.

## Limitations and Responsible Use

OralSense AI is an educational and research-oriented image classification project. It is not a clinically validated diagnostic system and must not be used as a substitute for examination, diagnosis, or treatment by a qualified dental or medical professional.

Predictions may be inaccurate, particularly for images that differ from the model's training data. Any real-world clinical use would require appropriate validation, testing, and professional oversight.

## License

No license is currently specified. All rights to the source code, model weights, and associated assets must be confirmed before reuse or redistribution.
