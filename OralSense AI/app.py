
from pathlib import Path

import numpy as np
import keras
import gradio as gr
from keras.applications.mobilenet_v2 import preprocess_input


# =====================================================
# 1. Configuration
# =====================================================

BASE_DIR = Path(__file__).parent

CLASSES = [
    "calculus",
    "cancer",
    "caries",
    "gingivitis",
    "ulcer",
]

CLASS_LABELS = {
    "calculus": "Dental Calculus",
    "cancer": "Oral Cancer",
    "caries": "Dental Caries",
    "gingivitis": "Gingivitis",
    "ulcer": "Oral Ulcer",
}

print("Loading OralSense AI...")

model = keras.models.load_model(
    str(BASE_DIR),
    custom_objects={"preprocess_input": preprocess_input},
    compile=False,
)

print("Model loaded successfully!")
print("Input shape:", model.input_shape)
print("Output shape:", model.output_shape)


# =====================================================
# 2. Prediction
# =====================================================

def predict_image(image):
    if image is None:
        raise gr.Error("Please upload an image to begin analysis.")

    processed_image = image.convert("RGB").resize((224, 224))

    image_array = np.asarray(
        processed_image,
        dtype=np.float32,
    )
    image_array = np.expand_dims(image_array, axis=0)

    # Preprocessing is already included inside the model.
    predictions = model.predict(image_array, verbose=0)[0]

    if len(predictions) != len(CLASSES):
        raise gr.Error(
            f"Expected {len(CLASSES)} outputs, "
            f"but the model returned {len(predictions)}."
        )

    predicted_index = int(np.argmax(predictions))
    predicted_class = CLASSES[predicted_index]
    predicted_label = CLASS_LABELS[predicted_class]

    print("\n" + "=" * 45)
    print("Predicted class:", predicted_label)
    print("Raw predictions:", predictions)
    print("=" * 45)

    results = {
        CLASS_LABELS[CLASSES[i]]: float(predictions[i])
        for i in range(len(CLASSES))
    }

    return results, processed_image, predicted_label


# =====================================================
# 3. Professional Light Theme
# =====================================================

CSS = """
:root {
    --page-bg: #f3f6fa;
    --panel-bg: #ffffff;
    --border-color: #e1e7ef;
    --text-main: #172338;
    --text-secondary: #5e6b7e;
    --accent: #087f8c;
}

body,
.gradio-container,
.gradio-container main {
    background: #f3f6fa !important;
    color: #172338 !important;
    font-family: Arial, Helvetica, sans-serif !important;
}

.gradio-container {
    max-width: 1240px !important;
    margin: 0 auto !important;
    padding: 24px !important;
}

/* Consistent readable text */
.gradio-container h1,
.gradio-container h2,
.gradio-container h3,
.gradio-container p,
.gradio-container label,
.gradio-container .prose,
.gradio-container .markdown {
    color: #172338;
}

.gradio-container .secondary,
.helper-text,
.section-description {
    color: #5e6b7e !important;
}

/* Header */
#brand-header {
    padding: 22px 0;
    border-bottom: 1px solid #e1e7ef;
    margin-bottom: 30px;
}

.brand-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 16px;
}

.brand-left {
    display: flex;
    align-items: center;
    gap: 14px;
}

.brand-mark {
    width: 48px;
    height: 48px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 13px;
    background: #e0f3f3;
    color: #087f8c !important;
    font-size: 20px;
    font-weight: 800;
}

.brand-name {
    color: #142238 !important;
    font-size: 25px;
    font-weight: 800;
    letter-spacing: -0.8px;
}

.brand-caption {
    margin-top: 5px;
    color: #65748a !important;
    font-size: 11px;
    letter-spacing: 1.3px;
    text-transform: uppercase;
}

.header-status {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 9px 13px;
    border: 1px solid #cce9e4;
    border-radius: 24px;
    background: #edf9f6;
    color: #17685f !important;
    font-size: 12px;
    font-weight: 600;
}

.status-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #159b83;
}

/* Page introduction */
#page-intro {
    margin-bottom: 25px;
}

#page-intro h1 {
    color: #142238 !important;
    font-size: 34px;
    font-weight: 800;
    letter-spacing: -1px;
    line-height: 1.3;
    margin-bottom: 10px;
}

#page-intro p {
    color: #5e6b7e !important;
    font-size: 14px;
    line-height: 1.8;
    max-width: 680px;
}

/* Main panels */
.panel {
    background: #ffffff !important;
    border: 1px solid #e1e7ef !important;
    border-radius: 16px !important;
    padding: 22px !important;
    box-shadow: 0 5px 20px rgba(22, 42, 68, 0.045) !important;
}

.section-title {
    color: #172338 !important;
    font-size: 17px;
    font-weight: 700;
    margin-bottom: 7px;
}

.section-description {
    color: #65748a !important;
    font-size: 13px;
    line-height: 1.7;
    margin-bottom: 18px;
}

/* Image upload and preview */
#image-upload,
#image-preview {
    background: #f8fafc !important;
    border: 1px solid #dce4ee !important;
    border-radius: 12px !important;
    overflow: hidden !important;
}

#image-upload label,
#image-preview label {
    color: #26364d !important;
}

#image-upload img,
#image-preview img {
    object-fit: contain !important;
}

/* Inputs */
.gradio-container input,
.gradio-container textarea,
.gradio-container select {
    background: #ffffff !important;
    color: #172338 !important;
    border-color: #d6dfeb !important;
}

.gradio-container input::placeholder,
.gradio-container textarea::placeholder {
    color: #7b8798 !important;
    opacity: 1 !important;
}

/* Primary button */
#analyze-button {
    background: #087f8c !important;
    color: #ffffff !important;
    border: 1px solid #087f8c !important;
    border-radius: 10px !important;
    min-height: 48px !important;
    font-size: 14px !important;
    font-weight: 700 !important;
    transition: background 0.2s ease !important;
}

#analyze-button:hover {
    background: #066873 !important;
}

/* Secondary button */
#clear-button {
    background: #ffffff !important;
    color: #33445c !important;
    border: 1px solid #d6dfeb !important;
    border-radius: 10px !important;
    min-height: 43px !important;
}

#clear-button:hover {
    background: #f1f5f9 !important;
}

/* Prediction results */
#prediction-output {
    background: #ffffff !important;
    border: 1px solid #e1e7ef !important;
    border-radius: 12px !important;
    padding: 14px !important;
}

#prediction-output,
#prediction-output * {
    color: #172338 !important;
}

#prediction-output progress {
    accent-color: #087f8c !important;
}

/* Predicted class summary */
#top-result {
    background: #eff9f8 !important;
    border: 1px solid #cce9e4 !important;
    border-radius: 12px !important;
    padding: 12px !important;
}

#top-result label {
    color: #42615f !important;
}

#top-result input {
    background: #ffffff !important;
    color: #075e63 !important;
    font-weight: 700 !important;
}

/* Helper text */
.helper-text {
    color: #65748a !important;
    font-size: 12px;
    line-height: 1.8;
    margin-top: 13px;
}

/* Disclaimer */
#medical-note {
    margin-top: 22px;
    padding: 15px 18px;
    border: 1px solid #dce5ef;
    background: #ffffff;
    border-radius: 12px;
    color: #526177 !important;
    font-size: 12px;
    line-height: 1.9;
}

#medical-note strong {
    color: #24354c !important;
}

/* Hide default footer */
footer {
    display: none !important;
}

/* Mobile layout */
@media (max-width: 700px) {
    .gradio-container {
        padding: 14px !important;
    }

    #brand-header {
        padding: 12px 0 22px;
    }

    .brand-name {
        font-size: 21px;
    }

    .brand-caption {
        font-size: 9px;
        letter-spacing: 0.7px;
    }

    .brand-mark {
        width: 42px;
        height: 42px;
    }

    .header-status {
        font-size: 10px;
        padding: 7px 9px;
    }

    .panel {
        padding: 15px !important;
    }

    #page-intro h1 {
        font-size: 28px;
    }
}
"""


# =====================================================
# 4. Gradio Interface
# =====================================================

with gr.Blocks(
    theme=gr.themes.Base(
        primary_hue="teal",
        secondary_hue="slate",
        neutral_hue="slate",
    ),
    css=CSS,
    title="OralSense AI | Oral Image Analysis",
) as demo:

    # Brand header
    gr.HTML("""
    <header id="brand-header">
        <div class="brand-row">
            <div class="brand-left">
                <div class="brand-mark">OS</div>
                <div>
                    <div class="brand-name">OralSense AI</div>
                    <div class="brand-caption">
                        Intelligent Oral Image Analysis
                    </div>
                </div>
            </div>
            <div class="header-status">
                <span class="status-dot"></span>
                Classification System
            </div>
        </div>
    </header>
    """)

    # Page introduction
    gr.HTML("""
    <section id="page-intro">
        <h1>Oral Image Analysis</h1>
        <p>
            Analyze oral images using an AI-powered image classification
            system designed to identify patterns across supported
            oral condition categories.
        </p>
    </section>
    """)

    with gr.Row(equal_height=False):

        # Image input panel
        with gr.Column(scale=1, min_width=300):
            with gr.Group(elem_classes=["panel"]):

                gr.HTML("""
                <div class="section-title">Image Input</div>
                <div class="section-description">
                    Upload an image to begin the classification process.
                    PNG and JPG formats are supported.
                </div>
                """)

                image_input = gr.Image(
                    type="pil",
                    label="Source image",
                    height=300,
                    elem_id="image-upload",
                )

                analyze_btn = gr.Button(
                    "Run Analysis",
                    variant="primary",
                    size="lg",
                    elem_id="analyze-button",
                )

                clear_btn = gr.Button(
                    "Clear Selection",
                    variant="secondary",
                    elem_id="clear-button",
                )

                gr.HTML("""
                <div class="helper-text">
                    Images are resized to 224 × 224 pixels
                    before model inference.
                </div>
                """)

        # Results panel
        with gr.Column(scale=1, min_width=300):
            with gr.Group(elem_classes=["panel"]):

                gr.HTML("""
                <div class="section-title">Classification Results</div>
                <div class="section-description">
                    Review the predicted category and the model's
                    output scores for the supported classes.
                </div>
                """)

                predicted_class_output = gr.Textbox(
                    label="Top classification",
                    interactive=False,
                    elem_id="top-result",
                    placeholder="Results will appear here",
                )

                prediction_output = gr.Label(
                    num_top_classes=5,
                    label="Model output scores",
                    elem_id="prediction-output",
                )

                preview_output = gr.Image(
                    label="Processed image",
                    height=220,
                    interactive=False,
                    elem_id="image-preview",
                )

    # Disclaimer
    gr.HTML("""
    <div id="medical-note">
        <strong>Important information</strong><br>
        This system provides AI-generated image classifications and
        is not a substitute for professional dental assessment.
        Predictions may be inaccurate and should not be used alone
        to make medical decisions.
    </div>
    """)

    # Run analysis
    analyze_btn.click(
        fn=predict_image,
        inputs=[image_input],
        outputs=[
            prediction_output,
            preview_output,
            predicted_class_output,
        ],
    )

    # Clear all outputs
    clear_btn.click(
        fn=lambda: (None, None, None, None),
        inputs=[],
        outputs=[
            image_input,
            prediction_output,
            preview_output,
            predicted_class_output,
        ],
    )


# =====================================================
# 5. Launch
# =====================================================

if __name__ == "__main__":
    demo.launch()
