"""Automated tests for Analytics, Session History, and Batch CSV Ingestion."""

import io
import pandas as pd
import pytest

from src.analytics import (
    CANDIDATE_TEXT_COLUMNS,
    LABEL_DISPLAY_NAMES,
    SessionAnalytics,
    detect_text_column,
    parse_and_validate_csv,
    plot_category_distribution,
    plot_probability_bars,
    process_batch,
)
from src.model_service import DEFAULT_MODEL_DIR, ModelService


@pytest.fixture(scope="module")
def model_service():
    service = ModelService.get_instance(model_dir=DEFAULT_MODEL_DIR)
    assert service.is_loaded is True
    return service


def test_session_analytics_lifecycle():
    analytics = SessionAnalytics()

    # Initial empty state
    metrics = analytics.get_summary_metrics()
    assert metrics["total_analyzed"] == 0
    assert metrics["distinct_categories"] == 0
    assert metrics["avg_top_probability"] in ("---", "—")
    assert metrics["avg_latency_ms"] in ("---", "—")

    df = analytics.get_history_dataframe()
    assert len(df) == 0

    # Add mock single record
    dummy_prediction = {
        "success": True,
        "predicted_category": "credit_card",
        "display_name": "Credit Card",
        "top_probability": 0.9250,
        "latency_ms": 25.4,
        "probabilities": {
            "credit_card": 0.9250,
            "credit_reporting": 0.0300,
            "debt_collection": 0.0200,
            "mortgages_and_loans": 0.0150,
            "retail_banking": 0.0100,
        },
    }
    analytics.add_record("Billing issue with my APR charges.", dummy_prediction)

    metrics = analytics.get_summary_metrics()
    assert metrics["total_analyzed"] == 1
    assert metrics["distinct_categories"] == 1
    assert "92.5%" in metrics["avg_top_probability"]
    assert "25.4" in metrics["avg_latency_ms"]

    df = analytics.get_history_dataframe()
    assert len(df) == 1
    assert df.iloc[0]["Predicted Category"] == "Credit Card"

    csv_out = analytics.export_csv()
    assert "prob_credit_card" in csv_out
    assert "0.925" in csv_out

    # Test clear
    analytics.clear()
    assert analytics.get_summary_metrics()["total_analyzed"] == 0


def test_csv_validation_and_column_detection():
    # Valid CSV bytes
    valid_csv = b"complaint_id,narrative\n1,Unrecognized credit card charge.\n2,Foreclosure notice received."
    df, err = parse_and_validate_csv(valid_csv)
    assert err is None
    assert df is not None
    assert len(df) == 2

    col, all_cols = detect_text_column(df)
    assert col == "narrative"
    assert "narrative" in all_cols

    # Empty CSV bytes
    empty_csv = b""
    df, err = parse_and_validate_csv(empty_csv)
    assert df is None
    assert err is not None


def test_batch_processing_workflow(model_service):
    data = {
        "id": [101, 102, 103],
        "complaint_text": [
            "Excessive collection phone calls at work regarding disputed medical bill.",
            "",  # empty edge case
            "Disputed incorrect trade line with credit bureau but it was not updated.",
        ],
        "customer_state": ["NY", "CA", "TX"],
    }
    input_df = pd.DataFrame(data)

    enriched_df, summary, err = process_batch(
        df=input_df,
        text_column="complaint_text",
        model_service=model_service,
        batch_size=2
    )

    assert err is None
    assert enriched_df is not None
    assert summary["total_rows"] == 3
    assert summary["successful_predictions"] == 2
    assert summary["failed_or_blank_rows"] == 1

    # Verify original columns preserved
    for original_col in ["id", "complaint_text", "customer_state"]:
        assert original_col in enriched_df.columns

    # Verify new prediction columns added
    assert "predicted_category" in enriched_df.columns
    assert "top_probability" in enriched_df.columns
    assert "inference_duration_ms" in enriched_df.columns
    for cat in LABEL_DISPLAY_NAMES:
        assert f"prob_{cat}" in enriched_df.columns

    # Check row 0 (debt collection)
    assert enriched_df.iloc[0]["predicted_category"] == "debt_collection"
    assert enriched_df.iloc[0]["top_probability"] > 0.5

    # Check row 1 (empty complaint failure handling)
    assert pd.isna(enriched_df.iloc[1]["predicted_category"])
    assert enriched_df.iloc[1]["top_probability"] == 0.0

    # Check row 2 (credit reporting)
    assert enriched_df.iloc[2]["predicted_category"] == "credit_reporting"


def test_plotly_figures_generation():
    # Probability bar chart
    probs = {
        "credit_card": 0.85,
        "credit_reporting": 0.05,
        "debt_collection": 0.04,
        "mortgages_and_loans": 0.03,
        "retail_banking": 0.03,
    }
    fig = plot_probability_bars(probs, predicted_category="credit_card")
    assert fig is not None
    assert hasattr(fig, "data")
    assert len(fig.data) > 0

    # Category distribution chart
    counts = {"credit_card": 3, "credit_reporting": 8, "debt_collection": 2}
    fig_dist = plot_category_distribution(counts)
    assert fig_dist is not None
    assert len(fig_dist.data) > 0


def test_complaint_intelligence_extraction():
    from src.analytics import extract_complaint_intelligence, plot_urgency_distribution

    # Test critical trigger (lawsuit / lawyer)
    critical_text = "I am consulting my lawyer to file a CFPB lawsuit regarding a $1,500 fraudulent loan."
    dummy_pred = {
        "success": True,
        "predicted_category": "credit_reporting",
        "top_probability": 0.94,
        "probabilities": {
            "credit_reporting": 0.94,
            "credit_card": 0.03,
            "debt_collection": 0.01,
            "mortgages_and_loans": 0.01,
            "retail_banking": 0.01
        }
    }
    intel = extract_complaint_intelligence(critical_text, dummy_pred)
    assert intel["urgency_level"] == "CRITICAL"
    assert "< 24 Hours" in intel["sla_window"]
    assert len(intel["monetary_entities"]) > 0
    assert "$1,500" in intel["monetary_entities"]
    assert "Bureau Liaison" in intel["department"]
    assert len(intel["recommended_actions"]) == 3

    # Test urgency donut chart
    u_counts = {"CRITICAL": 2, "HIGH": 5, "MODERATE": 1, "STANDARD": 3}
    fig_urg = plot_urgency_distribution(u_counts)
    assert fig_urg is not None
    assert len(fig_urg.data) > 0


def test_keyword_explainability():
    """Test approximate keyword attribution returns expected keys and highlights."""
    from src.analytics import explain_prediction

    text = "My credit card billing statement shows an unauthorized charge of $150 and I was charged APR fees."
    result = explain_prediction(text, "credit_card")

    assert "matched_keywords" in result
    assert "highlight_html" in result
    assert "method_note" in result
    assert isinstance(result["matched_keywords"], list)
    # Should match 'credit card' and 'apr' from the text
    assert len(result["matched_keywords"]) > 0
    # HTML should contain mark tags for highlights
    assert "<mark" in result["highlight_html"]
    assert "approximate attribution" in result["method_note"].lower()


def test_benchmark_data_integrity():
    """Validate that benchmark data constants contain expected verified values."""
    from src.analytics import VALIDATION_BENCHMARK_DATA, TEST_BENCHMARK_DATA

    # DistilBERT validation metrics from notebook Cell 84
    distilbert_val = next(d for d in VALIDATION_BENCHMARK_DATA if d["Model"] == "DistilBERT")
    assert abs(distilbert_val["Accuracy"] - 0.8685) < 0.0001
    assert abs(distilbert_val["Macro F1"] - 0.8537) < 0.0001
    assert abs(distilbert_val["Val Loss"] - 0.7502) < 0.0001
    assert distilbert_val["Parameters"] == 66_957_317

    # GRU validation metrics from notebook Cell 62
    gru_val = next(d for d in VALIDATION_BENCHMARK_DATA if d["Model"] == "GRU")
    assert abs(gru_val["Accuracy"] - 0.8575) < 0.0001
    assert abs(gru_val["Macro F1"] - 0.8401) < 0.0001

    # Test set metrics from notebook Cell 88
    distilbert_test = next(d for d in TEST_BENCHMARK_DATA if d["Model"] == "DistilBERT")
    assert abs(distilbert_test["Accuracy"] - 0.8650) < 0.0001
    assert abs(distilbert_test["Macro F1"] - 0.8521) < 0.0001

    gru_test = next(d for d in TEST_BENCHMARK_DATA if d["Model"] == "GRU")
    assert abs(gru_test["Accuracy"] - 0.8521) < 0.0001


def test_confusion_matrix_dimensions():
    """Verify confusion matrix arrays have correct 5x5 dimensions."""
    from src.analytics import DISTILBERT_TEST_CM, GRU_TEST_CM, DISTILBERT_VAL_CM

    for cm_name, cm in [
        ("DISTILBERT_TEST_CM", DISTILBERT_TEST_CM),
        ("GRU_TEST_CM", GRU_TEST_CM),
        ("DISTILBERT_VAL_CM", DISTILBERT_VAL_CM),
    ]:
        assert len(cm) == 5, f"{cm_name} should have 5 rows"
        for row in cm:
            assert len(row) == 5, f"{cm_name} rows should have 5 columns"
        # Row sums should approximately equal per-class test support
        row_sums = [sum(r) for r in cm]
        for s in row_sums:
            assert s > 1000, f"{cm_name} row sum should be > 1000 samples"


def test_confusion_matrix_plotly_figure():
    """Test that plot_confusion_matrix returns a valid Plotly figure."""
    from src.analytics import (
        DISTILBERT_TEST_CM, CATEGORY_DISPLAY_NAMES, plot_confusion_matrix
    )

    fig = plot_confusion_matrix(
        DISTILBERT_TEST_CM,
        CATEGORY_DISPLAY_NAMES,
        "Test CM",
        "Blues",
    )
    assert fig is not None
    assert len(fig.data) == 1  # one heatmap trace
    # Annotations text should contain percentage brackets
    sample_text = fig.data[0].text[0][0]
    assert "(" in sample_text and "%" in sample_text


def test_audit_trail_unique_ids():
    """Verify audit records get unique Event IDs and that filtering works."""
    analytics = SessionAnalytics()

    dummy_pred = {
        "success": True,
        "predicted_category": "retail_banking",
        "display_name": "Retail Banking",
        "top_probability": 0.88,
        "latency_ms": 15.0,
        "probabilities": {
            "credit_card": 0.02,
            "credit_reporting": 0.04,
            "debt_collection": 0.03,
            "mortgages_and_loans": 0.03,
            "retail_banking": 0.88,
        },
    }

    req_id_1 = analytics.add_record("ATM dispensing error.", dummy_pred, source="single")
    req_id_2 = analytics.add_record("Missing deposit.", dummy_pred, source="batch")

    assert req_id_1.startswith("CIPHER-REQ-")
    assert req_id_2.startswith("CIPHER-REQ-")
    assert req_id_1 != req_id_2

    audit_df = analytics.get_audit_dataframe()
    assert len(audit_df) == 2
    event_ids = audit_df["Event ID"].tolist()
    assert event_ids[0] != event_ids[1]
    assert all(e.startswith("CIPHER-EVT-") for e in event_ids)

    # Filter by event type
    single_df = analytics.get_audit_dataframe(filter_type="Single")
    batch_df = analytics.get_audit_dataframe(filter_type="Batch")
    assert len(single_df) == 1
    assert len(batch_df) == 1


def test_human_review_flag():
    """Verify human review is flagged for critical/low-confidence predictions."""
    from src.analytics import extract_complaint_intelligence

    # Low confidence should flag for review
    low_conf_pred = {
        "success": True,
        "predicted_category": "credit_card",
        "display_name": "Credit Card",
        "top_probability": 0.45,  # below 0.60 threshold
        "probabilities": {
            "credit_card": 0.45,
            "credit_reporting": 0.35,
            "debt_collection": 0.10,
            "mortgages_and_loans": 0.05,
            "retail_banking": 0.05,
        },
    }
    intel = extract_complaint_intelligence("Some complaint text.", low_conf_pred)
    assert intel["requires_human_review"] is True
    assert intel["human_review_reason"] is not None

    # High confidence STANDARD should NOT flag for review
    high_conf_pred = {
        "success": True,
        "predicted_category": "retail_banking",
        "display_name": "Retail Banking",
        "top_probability": 0.95,
        "probabilities": {
            "credit_card": 0.01,
            "credit_reporting": 0.01,
            "debt_collection": 0.01,
            "mortgages_and_loans": 0.02,
            "retail_banking": 0.95,
        },
    }
    intel2 = extract_complaint_intelligence("ATM cash dispense error.", high_conf_pred)
    assert intel2["requires_human_review"] is False
