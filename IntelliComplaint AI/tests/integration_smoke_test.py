import sys
from pathlib import Path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import pandas as pd
from src.model_service import ModelService
from src.analytics import process_batch, SessionAnalytics

def run_integration_check():
    print("==================================================")
    print("CIPHER - End-to-End Integration Smoke Test")
    print("==================================================")

    # 1. Load Model
    svc = ModelService.get_instance()
    assert svc.is_loaded, f"Model not loaded: {svc.load_error}"
    print(f"[PASS] 1. Model loaded successfully on: {svc.device_name} ({svc.device})")

    # 2. Test Single Prediction
    sample = "I was charged an unauthorized late fee on my credit card."
    res = svc.predict(sample)
    assert res["success"] is True, f"Prediction failed: {res.get('error')}"
    top_p = res["top_probability"]
    lat = res["latency_ms"]
    cat = res["predicted_category"]
    print(f"[PASS] 2. Single prediction: {cat} ({top_p * 100:.2f}%) in {lat} ms")
    assert cat == "credit_card", f"Expected credit_card, got {cat}"

    # 3. Test Batch Processing on sample_complaints.csv
    csv_path = "assets/sample_complaints.csv"
    df = pd.read_csv(csv_path)
    enriched, summary, err = process_batch(df, "narrative", svc, batch_size=4)
    assert err is None, f"Batch failed with error: {err}"
    print(f"[PASS] 3. Batch processing completed: {summary['successful_predictions']}/{summary['total_rows']} rows classified.")
    for idx, row in enriched.head(5).iterrows():
        print(f"   Row {idx+1}: [{row['predicted_category_name']}] (Prob: {row['top_probability']*100:.1f}%) -> {row['narrative'][:65]}...")

    # 4. Verify Session Analytics
    analytics = SessionAnalytics()
    analytics.add_record(sample, res)
    metrics = analytics.get_summary_metrics()
    assert metrics["total_analyzed"] == 1
    print(f"[PASS] 4. Session Analytics tracking verified (Total Analyzed: {metrics['total_analyzed']}).")

    print("\n[SUCCESS] ALL INTEGRATION CHECKS PASSED PERFECTLY!\n")

if __name__ == "__main__":
    run_integration_check()
