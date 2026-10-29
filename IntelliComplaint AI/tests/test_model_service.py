"""Automated tests for ModelService in CIPHER.

Validates model loading, device handling, input validation, probability constraints,
label mapping integrity, and batch execution using the local fine-tuned model.
"""

import json
from pathlib import Path
import pytest
import torch

from src.model_service import (
    DEFAULT_MODEL_DIR,
    LABEL_DISPLAY_NAMES,
    ModelService,
)


@pytest.fixture(scope="module")
def model_service():
    """Fixture to provide a loaded ModelService instance."""
    service = ModelService.get_instance(model_dir=DEFAULT_MODEL_DIR)
    assert service.is_loaded, f"Model failed to load: {service.load_error}"
    return service


def test_label_mapping_consistency(model_service):
    """Test that label mappings in metadata, model config, and display names match perfectly."""
    expected_labels = {
        "credit_card",
        "credit_reporting",
        "debt_collection",
        "mortgages_and_loans",
        "retail_banking",
    }

    # Verify model_service id2label contains all 5 labels
    service_labels = set(model_service.id2label.values())
    assert service_labels == expected_labels, f"Expected {expected_labels}, got {service_labels}"

    # Verify display name mapping exists for all 5 labels
    for label in expected_labels:
        assert label in LABEL_DISPLAY_NAMES, f"Display name missing for label {label}"
        assert len(LABEL_DISPLAY_NAMES[label]) > 0

    # Cross-reference with model_metadata.json
    meta_path = DEFAULT_MODEL_DIR / "model_metadata.json"
    if meta_path.exists():
        with open(meta_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)
        meta_labels = set(metadata["label2id"].keys())
        assert meta_labels == expected_labels, f"Metadata labels {meta_labels} != {expected_labels}"


def test_empty_complaint_validation(model_service):
    """Test that empty or whitespace strings are rejected gracefully with informative errors."""
    for empty_input in ["", "   ", "\n\t  \n"]:
        res = model_service.predict(empty_input)
        assert res["success"] is False, f"Expected failure for input: {repr(empty_input)}"
        assert res["error"] is not None
        assert "empty" in res["error"].lower() or "whitespace" in res["error"].lower()
        assert res["predicted_category"] is None
        assert res["top_probability"] == 0.0


def test_invalid_type_validation(model_service):
    """Test that non-string inputs are rejected gracefully."""
    for invalid_input in [None, 12345, ["complaint list"]]:
        res = model_service.predict(invalid_input)  # type: ignore
        assert res["success"] is False
        assert res["predicted_category"] is None


def test_single_prediction_probabilities(model_service):
    """Test that predictions satisfy all mathematical and structural probability constraints."""
    sample_text = (
        "I was charged an improper late fee on my credit card even though "
        "my payment was submitted three days before the due date."
    )
    res = model_service.predict(sample_text)

    assert res["success"] is True, f"Prediction failed: {res.get('error')}"
    assert res["predicted_category"] in model_service.label2id
    assert res["display_name"] == LABEL_DISPLAY_NAMES[res["predicted_category"]]
    assert res["latency_ms"] > 0

    probs = res["probabilities"]
    assert len(probs) == 5, f"Expected 5 probabilities, got {len(probs)}"

    prob_sum = 0.0
    max_prob = -1.0
    argmax_category = None

    for cat, p in probs.items():
        assert isinstance(p, float), f"Probability for {cat} is not float: {type(p)}"
        assert not (p != p), f"Probability for {cat} is NaN"
        assert 0.0 <= p <= 1.0, f"Probability {p} outside [0, 1] for {cat}"
        prob_sum += p
        if p > max_prob:
            max_prob = p
            argmax_category = cat

    # Sum of softmax probabilities should be approx 1.0
    assert pytest.approx(prob_sum, abs=1e-3) == 1.0, f"Probabilities sum to {prob_sum}, expected ~1.0"

    # Top probability and predicted category match argmax
    assert res["predicted_category"] == argmax_category
    assert pytest.approx(res["top_probability"], abs=1e-4) == max_prob


def test_long_complaint_truncation(model_service):
    """Test that complaint text exceeding max_token_length (256) is truncated without crashing."""
    long_narrative = "Repeated billing error on mortgage payment. " * 100  # ~500 words
    res = model_service.predict(long_narrative)

    assert res["success"] is True
    assert res["token_count"] <= model_service.max_token_length
    assert res["predicted_category"] is not None


def test_cpu_fallback():
    """Test that CPU inference works reliably even when instantiated explicitly with CPU."""
    cpu_service = ModelService(model_dir=DEFAULT_MODEL_DIR, device_override="cpu")
    assert cpu_service.is_loaded is True
    assert str(cpu_service.device) == "cpu"
    assert cpu_service.is_gpu_active is False

    res = cpu_service.predict("I need assistance disputing an error on my credit report.")
    assert res["success"] is True
    assert res["predicted_category"] is not None
    assert pytest.approx(sum(res["probabilities"].values()), abs=1e-3) == 1.0


def test_batch_prediction_with_missing_entries(model_service):
    """Test that batch prediction handles mixed valid, empty, and whitespace texts gracefully."""
    texts = [
        "Unauthorized transactions on my retail checking debit card at an ATM.",
        "",
        "Debt collectors have been calling repeatedly at all hours.",
        "   ",
        "My mortgage company failed to credit my escrow balance properly.",
    ]

    results = model_service.predict_batch(texts, batch_size=2)
    assert len(results) == len(texts)

    # Valid rows
    assert results[0]["success"] is True
    assert results[0]["predicted_category"] is not None

    assert results[2]["success"] is True
    assert results[2]["predicted_category"] == "debt_collection"

    assert results[4]["success"] is True
    assert results[4]["predicted_category"] == "mortgages_and_loans"

    # Invalid / empty rows
    assert results[1]["success"] is False
    assert results[1]["predicted_category"] is None
    assert results[3]["success"] is False
    assert results[3]["predicted_category"] is None
