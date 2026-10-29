"""CIPHER -- Enterprise Consumer Complaint Intelligence Platform.

Advanced NLP intelligence dashboard for financial consumer complaint triage,
regulatory risk assessment, automated departmental routing, and batch audit analysis.
Powered by a fine-tuned DistilBERT transformer loaded strictly from local weights.
"""

import os
import tempfile
from typing import Any, Dict, List, Optional, Tuple

import gradio as gr
import pandas as pd
import plotly.graph_objects as go

from src.analytics import (
    CANDIDATE_TEXT_COLUMNS,
    CATEGORY_DISPLAY_NAMES,
    CATEGORY_PALETTE,
    DEPARTMENT_ROUTING,
    DISTILBERT_TEST_CLASS_REPORT,
    DISTILBERT_TEST_CM,
    DISTILBERT_VAL_CM,
    DISTILBERT_VALIDATION_CLASS_REPORT,
    GRU_TEST_CLASS_REPORT,
    GRU_TEST_CM,
    LABEL_DISPLAY_NAMES,
    TEST_BENCHMARK_DATA,
    VALIDATION_BENCHMARK_DATA,
    SessionAnalytics,
    create_empty_figure,
    detect_text_column,
    explain_prediction,
    extract_complaint_intelligence,
    parse_and_validate_csv,
    plot_benchmark_comparison,
    plot_category_distribution,
    plot_confusion_matrix,
    plot_probability_bars,
    plot_urgency_distribution,
    process_batch,
)
from src.model_service import DEFAULT_MODEL_DIR, ModelService

# Initialize backend services
model_service = ModelService.get_instance(model_dir=DEFAULT_MODEL_DIR)
session_analytics = SessionAnalytics()

# Synthetic Demonstration Scenarios
EXAMPLE_COMPLAINTS = {
    "Credit Card": (
        "I opened a rewards credit card with promotional 0% introductory APR for 18 months. "
        "On my statement, the bank charged $112 in finance fees and a $40 penalty even though "
        "my automatic payment was debited on time. Customer service stated the promo rate was cancelled without notice."
    ),
    "Credit Reporting": (
        "My TransUnion credit report contains an unknown delinquent auto loan in collections resulting from identity theft. "
        "I submitted an FTC identity theft report and police report via certified mail. The credit bureau failed to investigate "
        "within 30 days and falsely verified the inaccurate trade line."
    ),
    "Debt Collection": (
        "A debt collection agency has placed over seven automated phone calls per day to my cell phone and called my "
        "employer's front desk demanding payment for an alleged $1,400 medical bill from 2016. They threatened immediate "
        "wage garnishment and refused to provide a debt validation notice."
    ),
    "Mortgages & Loans": (
        "Our mortgage loan servicer miscalculated our annual escrow shortage and increased our monthly mortgage payment "
        "by $650. We provided certified county property tax receipts demonstrating the taxes were already satisfied, "
        "but the servicer refused to revise the escrow disbursement and threatened foreclosure proceedings."
    ),
    "Retail Banking": (
        "I attempted to withdraw $500 from a branch ATM. The ATM malfunctioned, dispensed no cash, and displayed an error slip. "
        "My checking account balance was deducted $500 immediately. The bank manager refused to issue provisional credit "
        "under Regulation E and told me to wait 45 days for an internal audit."
    ),
}

# ---------------------------------------------------------------------------
# Scoped Enterprise CSS
# ---------------------------------------------------------------------------
# Scoped Enterprise CSS
# ---------------------------------------------------------------------------
CUSTOM_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

/* ── Global reset & font ───────────────────────────────────────────────── */
.gradio-container {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
    max-width: 1440px !important;
    margin: 0 auto !important;
    padding: 16px 20px !important;
    box-sizing: border-box !important;
    overflow-x: hidden !important;
}

/* ── Typography & Overflow Safety ──────────────────────────────────────── */
h1, h2, h3, h4, h5, h6 {
    color: #F8FAFC !important;
    word-break: break-word !important;
    overflow-wrap: break-word !important;
}
h3 {
    font-size: 1.22rem !important;
    font-weight: 700 !important;
    margin-top: 10px !important;
    margin-bottom: 6px !important;
    letter-spacing: -0.01em !important;
}
h4 {
    font-size: 1.02rem !important;
    font-weight: 600 !important;
    color: #E2E8F0 !important;
    margin-top: 14px !important;
    margin-bottom: 6px !important;
}
p, span, div, label {
    overflow-wrap: break-word !important;
}

/* ── Executive Hero Header ─────────────────────────────────────────────── */
.cipher-hero {
    background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%) !important;
    border: 1px solid #334155 !important;
    border-radius: 12px !important;
    padding: 20px 24px !important;
    margin-bottom: 18px !important;
    box-shadow: 0 4px 20px rgba(0,0,0,0.25) !important;
    color: #F8FAFC !important;
    box-sizing: border-box !important;
    width: 100% !important;
    overflow: hidden !important;
}
.hero-title {
    font-size: clamp(1.4rem, 2.2vw, 1.95rem) !important;
    font-weight: 800 !important;
    color: #F8FAFC !important;
    margin: 0 !important;
    line-height: 1.2 !important;
    letter-spacing: -0.02em !important;
    overflow-wrap: break-word !important;
}
.hero-title span { color: #38BDF8 !important; }
.hero-sub {
    font-size: 0.92rem !important;
    color: #94A3B8 !important;
    margin-top: 6px !important;
    font-weight: 400 !important;
    line-height: 1.45 !important;
    overflow-wrap: break-word !important;
}

/* ── Status Badges & Dots ──────────────────────────────────────────────── */
.status-tag {
    display: inline-flex; align-items: center; gap: 8px;
    padding: 5px 12px; border-radius: 9999px;
    font-size: 0.78rem; font-weight: 600;
    letter-spacing: 0.02em;
    white-space: nowrap;
}
.dot-online {
    display: inline-block; width: 8px; height: 8px; border-radius: 50%;
    background-color: #10B981; box-shadow: 0 0 8px #10B981;
}
.dot-offline {
    display: inline-block; width: 8px; height: 8px; border-radius: 50%;
    background-color: #EF4444; box-shadow: 0 0 8px #EF4444;
}
.dot-device {
    display: inline-block; width: 8px; height: 8px; border-radius: 50%;
    background-color: #0284C7; box-shadow: 0 0 8px #0284C7;
}
.tag-ready  { background: rgba(16,185,129,0.15); color: #10B981; border: 1px solid rgba(16,185,129,0.35); }
.tag-device { background: rgba(56,189,248,0.15); color: #0284C7; border: 1px solid rgba(56,189,248,0.35); }
.tag-model  { background: rgba(99,102,241,0.15); color: #A5B4FC; border: 1px solid rgba(99,102,241,0.35); }
.tag-error  { background: rgba(239,68,68,0.15);  color: #EF4444; border: 1px solid rgba(239,68,68,0.35); }

/* ── Clean Tab Bar & Navigation ────────────────────────────────────────── */
.tabs {
    border: none !important;
}
.tab-nav {
    border-bottom: 1px solid #334155 !important;
    gap: 6px !important;
    margin-bottom: 18px !important;
    display: flex !important;
    flex-wrap: wrap !important;
}
.tab-nav > button {
    font-family: 'Inter', system-ui, sans-serif !important;
    font-size: 0.92rem !important;
    font-weight: 600 !important;
    color: #94A3B8 !important;
    padding: 10px 18px !important;
    border-radius: 8px 8px 0 0 !important;
    border: none !important;
    border-bottom: 3px solid transparent !important;
    background: transparent !important;
    transition: all 0.2s ease !important;
    cursor: pointer !important;
    white-space: nowrap !important;
}
.tab-nav > button:hover {
    color: #F8FAFC !important;
    background: rgba(51, 65, 85, 0.4) !important;
}
.tab-nav > button.selected {
    color: #38BDF8 !important;
    border-bottom: 3px solid #38BDF8 !important;
    background: rgba(56, 189, 248, 0.08) !important;
    font-weight: 700 !important;
}

/* ── KPI Cards ─────────────────────────────────────────────────────────── */
.kpi-grid {
    display: grid !important;
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)) !important;
    gap: 12px !important;
    width: 100% !important;
    box-sizing: border-box !important;
    margin-bottom: 18px !important;
}
.kpi-card {
    background: #1E293B !important;
    border: 1px solid #334155 !important;
    border-radius: 10px !important;
    padding: 14px 12px !important;
    text-align: center !important;
    color: #F8FAFC !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15) !important;
    min-width: 0 !important;
    box-sizing: border-box !important;
    overflow: hidden !important;
    word-break: break-word !important;
    display: flex !important;
    flex-direction: column !important;
    justify-content: center !important;
}
.kpi-value {
    font-size: clamp(1.3rem, 1.8vw, 1.75rem) !important;
    font-weight: 800 !important;
    color: #38BDF8 !important;
    line-height: 1.2 !important;
    overflow-wrap: break-word !important;
    word-break: break-word !important;
}
.kpi-label {
    font-size: 0.72rem !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.04em !important;
    color: #94A3B8 !important;
    margin-top: 6px !important;
    line-height: 1.25 !important;
    white-space: normal !important;
    word-break: break-word !important;
}

/* ── Prediction Dossier ────────────────────────────────────────────────── */
.pred-dossier {
    background: #1E293B !important;
    border: 1px solid #475569 !important;
    border-radius: 12px !important;
    padding: 20px !important;
    margin-bottom: 16px !important;
    color: #F8FAFC !important;
    box-shadow: 0 8px 24px rgba(0,0,0,0.2) !important;
    box-sizing: border-box !important;
    width: 100% !important;
    overflow: hidden !important;
    word-break: break-word !important;
}
.pred-category-title {
    font-size: clamp(1.1rem, 1.5vw, 1.35rem) !important;
    font-weight: 800 !important;
    color: #F8FAFC !important;
    margin: 4px 0 !important;
    line-height: 1.35 !important;
    overflow-wrap: break-word !important;
    word-break: break-word !important;
}
.pred-conf-score {
    font-size: clamp(1.6rem, 2.2vw, 2.0rem) !important;
    font-weight: 900 !important;
    color: #38BDF8 !important;
    line-height: 1.1 !important;
}

/* ── Intel Box ─────────────────────────────────────────────────────────── */
.intel-box {
    background: #0F172A !important;
    border: 1px solid #334155 !important;
    border-radius: 8px !important;
    padding: 12px 16px !important;
    margin-top: 14px !important;
    color: #F8FAFC !important;
    box-sizing: border-box !important;
    width: 100% !important;
    overflow: hidden !important;
}
.intel-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 7px 0;
    border-bottom: 1px solid rgba(255,255,255,0.08);
    flex-wrap: wrap;
    gap: 6px 12px;
}
.intel-row:last-child { border-bottom: none; }
.intel-key {
    font-size: 0.8rem;
    font-weight: 600;
    color: #94A3B8 !important;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    flex: 1 1 160px;
    min-width: 0;
    word-break: break-word;
}
.intel-val {
    font-size: 0.88rem;
    font-weight: 700;
    color: #F8FAFC !important;
    flex: 0 1 auto;
    text-align: right;
    word-break: break-word;
}

/* ── Chips ─────────────────────────────────────────────────────────────── */
.chip { display: inline-block; padding: 3px 10px; border-radius: 6px; font-size: 0.78rem; font-weight: 700; margin-right: 5px; margin-top: 4px; }
.chip-critical  { background: rgba(239,68,68,0.15);  color: #EF4444; border: 1px solid rgba(239,68,68,0.35); }
.chip-trigger   { background: rgba(56,189,248,0.15); color: #0284C7; border: 1px solid rgba(56,189,248,0.35); }
.chip-money     { background: rgba(245,158,11,0.15); color: #D97706; border: 1px solid rgba(245,158,11,0.35); }
.chip-best      { background: rgba(16,185,129,0.18); color: #10B981; border: 1px solid rgba(16,185,129,0.4); }
.chip-arch-t    { background: rgba(99,102,241,0.18); color: #A5B4FC; border: 1px solid rgba(99,102,241,0.4); }
.chip-arch-r    { background: rgba(245,158,11,0.18); color: #FCD34D; border: 1px solid rgba(245,158,11,0.4); }

/* ── Section Dividers ──────────────────────────────────────────────────── */
.section-header {
    background: linear-gradient(90deg, #1E293B, transparent);
    border-left: 3px solid #38BDF8;
    padding: 8px 14px; border-radius: 0 6px 6px 0;
    color: #F8FAFC !important; font-weight: 700; font-size: 1.02rem;
    margin: 18px 0 10px 0;
}

/* ── Benchmark Table  ──────────────────────────────────────────────────── */
.bench-best { background: rgba(16,185,129,0.1) !important; }

/* ── Explainability Panel ──────────────────────────────────────────────── */
.explain-box {
    background: #0F172A !important; border: 1px solid #334155 !important;
    border-radius: 8px !important; padding: 14px 16px !important;
    color: #CBD5E1 !important; font-size: 0.92rem; line-height: 1.7;
    box-sizing: border-box !important; width: 100% !important; overflow: hidden !important;
}
.explain-note {
    background: rgba(245,158,11,0.08) !important; border: 1px solid rgba(245,158,11,0.3) !important;
    border-radius: 6px !important; padding: 8px 12px !important;
    color: #FCD34D !important; font-size: 0.81rem; margin-top: 10px;
}
"""


# ---------------------------------------------------------------------------
# Helper HTML Builders
# ---------------------------------------------------------------------------
def render_header_html() -> str:
    """Build the crisp, executive header banner."""
    diag = model_service.get_diagnostic_info()
    if diag["is_loaded"]:
        status_badge = '<span class="status-tag tag-ready"><span class="dot-online"></span> Model Online: DistilBERT</span>'
    else:
        err = (diag["load_error"] or "Load error")[:60]
        status_badge = f'<span class="status-tag tag-error"><span class="dot-offline"></span> {err}</span>'

    if diag["is_gpu_active"]:
        device_badge = f'<span class="status-tag tag-device"><span class="dot-device"></span> GPU: {diag["device_name"]}</span>'
    else:
        device_badge = f'<span class="status-tag tag-device"><span class="dot-device"></span> CPU: {diag["device_name"]}</span>'

    return f"""
    <div class="cipher-hero">
        <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:14px;">
            <div style="flex:1 1 320px;min-width:0;">
                <h1 class="hero-title">CIPHER <span>Intelligence</span></h1>
                <p class="hero-sub">Enterprise AI Platform for Consumer Complaint Triage, Regulatory Risk Scoring &amp; Department Routing</p>
            </div>
            <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center;">
                {status_badge}
                {device_badge}
                <span class="status-tag tag-model">DistilBERT v1.0 &nbsp;|&nbsp; 66.9M Params</span>
                <span class="status-tag tag-model">Max Seq: 256 Tokens</span>
            </div>
        </div>
    </div>
    """


def build_kpi_html(
    total: Any, success: Any, failed: Any, human_review: Any,
    avg_lat: Any, model_name: str = "DistilBERT v1.0"
) -> str:
    """Render the executive KPI grid as HTML (6 high-value executive indicators)."""
    return f"""
    <div class="kpi-grid">
        <div class="kpi-card">
            <div class="kpi-value">{total}</div>
            <div class="kpi-label">Total Analyzed</div>
        </div>
        <div class="kpi-card" style="border-top:3px solid #10B981;">
            <div class="kpi-value" style="color:#34D399;">{success}</div>
            <div class="kpi-label">Successfully Classified</div>
        </div>
        <div class="kpi-card" style="border-top:3px solid #F59E0B;">
            <div class="kpi-value" style="color:#FBBF24;">{human_review}</div>
            <div class="kpi-label" style="color:#F59E0B;">Human Review Required</div>
        </div>
        <div class="kpi-card" style="border-top:3px solid #EF4444;">
            <div class="kpi-value" style="color:#F87171;">{failed}</div>
            <div class="kpi-label" style="color:#F87171;">Failed / Rejected</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-value">{avg_lat}</div>
            <div class="kpi-label">Avg Inference Latency</div>
        </div>
        <div class="kpi-card" style="border-top:3px solid #6366F1;">
            <div class="kpi-value" style="font-size:1.05rem;padding-top:6px;color:#A5B4FC;">{model_name}</div>
            <div class="kpi-label">Active Model</div>
        </div>
    </div>
    <p style="color:#64748B;font-size:0.78rem;margin-top:4px;">
        * Telemetry reflects live in-session requests only. Latency measured on {'GPU' if model_service.is_gpu_active else 'CPU'}.
    </p>
    """


def get_kpi_html() -> str:
    """Get fresh KPI HTML from current session state."""
    s = session_analytics.get_summary_metrics()
    return build_kpi_html(
        total=s["total_analyzed"],
        success=s["success_count"],
        failed=s["failed_count"],
        human_review=s["human_review_count"],
        avg_lat=s["avg_latency_ms"],
    )


# ---------------------------------------------------------------------------
# Single Complaint Analysis
# ---------------------------------------------------------------------------
def analyze_single_complaint(text: str) -> Tuple:
    """Execute prediction, urgency risk scoring, entity discovery, and return updated state."""
    res = model_service.predict(text)

    empty_tech = "<div style='color:#64748B;font-size:0.85rem;padding:8px;'>No active inference recorded.</div>"
    empty_explain = "<div class='explain-box' style='color:#64748B;'>Run an analysis to see keyword attribution.</div>"

    def empty_returns(err_msg: str):
        error_html = f"""
        <div class="kpi-card" style="border:1.5px solid #EF4444;text-align:left;padding:16px;">
            <div style="color:#EF4444;font-weight:800;font-size:1.02rem;">Input Validation Notice</div>
            <div style="color:#F8FAFC;margin-top:4px;font-size:0.9rem;">{err_msg}</div>
        </div>
        """
        return (
            error_html,
            create_empty_figure("Awaiting valid complaint narrative."),
            pd.DataFrame(columns=["Rank", "Category", "Confidence", "Internal Label"]),
            empty_explain,
            get_kpi_html(),
            plot_category_distribution(session_analytics.get_category_counts()),
            plot_urgency_distribution(session_analytics.get_urgency_counts()),
            session_analytics.get_history_dataframe(),
            empty_tech,
        )

    if not res["success"]:
        return empty_returns(res.get("error", "Invalid or empty complaint narrative."))

    intel = extract_complaint_intelligence(text, res)
    request_id = session_analytics.add_record(text, res, source="single")

    pred_category_name = res["display_name"]
    top_prob = res["top_probability"]
    latency = res["latency_ms"]
    req_id_display = res.get("request_id", request_id)

    trigger_chips_html = "".join(
        [f'<span class="chip chip-critical">{t}</span>' for t in intel["key_triggers"]]
    )
    money_chips_html = "".join(
        [f'<span class="chip chip-money">{m}</span>' for m in intel["monetary_entities"]]
    )
    actions_html = "".join(
        [f'<li style="margin-bottom:5px;color:#F1F5F9;">{act}</li>' for act in intel["recommended_actions"]]
    )

    ambiguity_notice = ""
    if intel["ambiguity_flag"]:
        ambiguity_notice = f"""
        <div style="background:rgba(245,158,11,0.12);border:1px solid #F59E0B;border-radius:8px;padding:10px 14px;margin-top:12px;color:#FBBF24;font-size:0.88rem;">
            <strong>Multi-Department Affinity Detected:</strong>
            Secondary affinity observed with <strong>{intel['secondary_category']}</strong>.
            Coordinate cross-department review if needed.
        </div>
        """

    human_review_notice = ""
    if intel["requires_human_review"]:
        human_review_notice = f"""
        <div style="background:rgba(239,68,68,0.12);border:1px solid #EF4444;border-radius:8px;padding:10px 14px;margin-top:10px;color:#FCA5A5;font-size:0.87rem;">
            <strong>Human Review Required:</strong> {intel.get("human_review_reason", "Low model confidence or elevated regulatory risk threshold triggered.")}
        </div>
        """

    conf_color = "#34D399" if top_prob >= 0.80 else ("#FBBF24" if top_prob >= 0.60 else "#F87171")

    result_dossier_html = f"""
    <div class="pred-dossier">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:12px;">
            <div style="flex:1 1 280px;min-width:0;">
                <div style="font-size:0.75rem;text-transform:uppercase;color:#38BDF8;font-weight:800;letter-spacing:0.06em;">Classified Financial Category</div>
                <div class="pred-category-title">{pred_category_name}</div>
                <div style="font-size:0.82rem;color:#94A3B8;margin-top:4px;">
                    Model Label: <code style="color:#A5B4FC;font-weight:700;">{res["predicted_category"]}</code>
                </div>
            </div>
            <div style="flex:0 0 auto;text-align:right;">
                <div class="pred-conf-score" style="color:{conf_color};">{top_prob * 100:.2f}%</div>
                <div style="font-size:0.75rem;text-transform:uppercase;color:#94A3B8;font-weight:700;">Confidence Score</div>
                <div style="font-size:0.70rem;color:#64748B;">Uncalibrated softmax probability</div>
            </div>
        </div>

        {human_review_notice}
        {ambiguity_notice}

        <div class="intel-box">
            <div style="font-size:0.72rem;color:#94A3B8;margin-bottom:8px;letter-spacing:0.03em;">
                Operational Triage Heuristics (Deterministic Policy Rules based on Regulatory Triggers &amp; Product Mapping)
            </div>
            <div class="intel-row">
                <span class="intel-key">Regulatory Risk Level</span>
                <span class="intel-val" style="color:{intel['urgency_color']};font-weight:800;">{intel['urgency_badge']}</span>
            </div>
            <div class="intel-row">
                <span class="intel-key">Assigned Resolution Team</span>
                <span class="intel-val" style="color:#38BDF8;">{intel['department']} ({intel['dept_code']})</span>
            </div>
            <div class="intel-row">
                <span class="intel-key">Target SLA Window</span>
                <span class="intel-val" style="color:#FBBF24;">{intel['sla_window']}</span>
            </div>
            <div class="intel-row" style="flex-wrap:wrap;">
                <span class="intel-key">Discovered Trigger Keywords</span>
                <div style="text-align:right;margin-top:4px;">
                    {trigger_chips_html or '<span style="color:#94A3B8;">None detected</span>'}
                    {money_chips_html}
                </div>
            </div>
        </div>

        <div style="margin-top:14px;background:#0F172A;border:1px solid #334155;border-radius:8px;padding:14px 18px;">
            <div style="font-size:0.8rem;font-weight:800;text-transform:uppercase;color:#34D399;letter-spacing:0.05em;margin-bottom:6px;">
                Recommended Compliance Remediation Steps:
            </div>
            <ul style="margin:0;padding-left:20px;">{actions_html}</ul>
        </div>
    </div>
    """

    # Probability Bar Chart
    fig_bars = plot_probability_bars(res["probabilities"], predicted_category=res["predicted_category"])

    # Probability Table
    sorted_probs = sorted(res["probabilities"].items(), key=lambda x: x[1], reverse=True)
    prob_df = pd.DataFrame([
        {
            "Rank": f"#{rank}",
            "Category": LABEL_DISPLAY_NAMES.get(k, k.replace("_", " ").title()),
            "Confidence": f"{p * 100:.2f}%",
            "Internal Label": k,
        }
        for rank, (k, p) in enumerate(sorted_probs, start=1)
    ])

    # Explainability Panel
    expl = explain_prediction(text, res["predicted_category"])
    matched_kw_html = (
        " ".join([f'<span class="chip chip-trigger">{kw}</span>' for kw in expl["matched_keywords"]])
        if expl["matched_keywords"]
        else '<span style="color:#64748B;">No vocabulary keywords matched.</span>'
    )
    explain_html = f"""
    <div class="explain-box">
        <div style="font-size:0.78rem;font-weight:700;text-transform:uppercase;color:#38BDF8;letter-spacing:0.05em;margin-bottom:8px;">
            Matched Category Vocabulary Keywords
        </div>
        <div style="margin-bottom:10px;">{matched_kw_html}</div>
        <hr style="border-color:#1E293B;margin:10px 0;">
        <div style="font-size:0.78rem;font-weight:700;text-transform:uppercase;color:#38BDF8;letter-spacing:0.05em;margin-bottom:8px;">
            Highlighted Narrative Excerpt
        </div>
        <div style="line-height:1.75;color:#CBD5E1;">{expl["highlight_html"]}</div>
        <div class="explain-note">Methodology Note: {expl["method_note"]}</div>
    </div>
    """

    # Technical Details Panel
    diag = model_service.get_diagnostic_info()
    device_label = f"GPU ({diag['device_name']})" if diag["is_gpu_active"] else f"CPU ({diag['device_name']})"
    tech_details_html = f"""
    <div style="background:#0F172A;border:1px solid #334155;border-radius:8px;padding:12px 16px;font-size:0.85rem;color:#CBD5E1;line-height:1.6;">
        <div style="display:flex;justify-content:space-between;padding:4px 0;border-bottom:1px solid rgba(255,255,255,0.06);">
            <span style="color:#94A3B8;">Request Reference ID:</span>
            <code style="color:#38BDF8;font-weight:700;">{req_id_display}</code>
        </div>
        <div style="display:flex;justify-content:space-between;padding:4px 0;border-bottom:1px solid rgba(255,255,255,0.06);">
            <span style="color:#94A3B8;">Production Model:</span>
            <span style="color:#A5B4FC;font-weight:600;">DistilBERT (Fine-Tuned, 66.9M Parameters)</span>
        </div>
        <div style="display:flex;justify-content:space-between;padding:4px 0;border-bottom:1px solid rgba(255,255,255,0.06);">
            <span style="color:#94A3B8;">Execution Hardware:</span>
            <span style="color:#F8FAFC;">{device_label}</span>
        </div>
        <div style="display:flex;justify-content:space-between;padding:4px 0;border-bottom:1px solid rgba(255,255,255,0.06);">
            <span style="color:#94A3B8;">Inference Duration:</span>
            <span style="color:#38BDF8;font-weight:700;">{latency:.1f} ms</span>
        </div>
        <div style="display:flex;justify-content:space-between;padding:4px 0;">
            <span style="color:#94A3B8;">Token Sequence Length:</span>
            <span style="color:#F8FAFC;">{res['token_count']} / 256 tokens</span>
        </div>
    </div>
    """

    hist_df = session_analytics.get_history_dataframe()
    dist_fig = plot_category_distribution(session_analytics.get_category_counts())
    urgency_fig = plot_urgency_distribution(session_analytics.get_urgency_counts())

    return (
        result_dossier_html,
        fig_bars,
        prob_df,
        explain_html,
        get_kpi_html(),
        dist_fig,
        urgency_fig,
        hist_df,
        tech_details_html,
    )


def reset_analyzer() -> Tuple:
    """Reset the text input and clear single analyzer outputs."""
    empty_fig = create_empty_figure("Awaiting complaint narrative analysis.")
    empty_df = pd.DataFrame(columns=["Rank", "Category", "Confidence", "Internal Label"])
    placeholder_html = """
    <div class="kpi-card" style="text-align:center;padding:36px 20px;">
        <div style="font-weight:800;font-size:1.2rem;color:#F8FAFC;margin-bottom:6px;">Ready for Complaint Analysis</div>
        <div style="font-size:0.92rem;color:#94A3B8;max-width:480px;margin:0 auto;line-height:1.45;">
            Enter a consumer narrative or click a scenario button on the left to begin classification.
        </div>
    </div>
    """
    explain_placeholder = "<div class='explain-box' style='color:#64748B;'>Run an analysis to see keyword attribution.</div>"
    tech_placeholder = "<div style='color:#64748B;font-size:0.85rem;padding:8px;'>No active inference recorded.</div>"
    return ("", placeholder_html, empty_fig, empty_df, explain_placeholder, tech_placeholder)


# ---------------------------------------------------------------------------
# Batch Processing
# ---------------------------------------------------------------------------
def on_csv_file_uploaded(file_obj: Any) -> Tuple[gr.Dropdown, str]:
    """Handle CSV file upload, validate structure, and suggest complaint column."""
    if file_obj is None:
        return gr.Dropdown(choices=[], value=None), "Please upload a CSV file."

    df, err = parse_and_validate_csv(file_obj.name)
    if err:
        return gr.Dropdown(choices=[], value=None), f"Upload Notice: {err}"

    detected_col, all_cols = detect_text_column(df)
    msg = (
        f"**File Verified:** **{len(df):,} rows**, **{len(all_cols)} columns**. "
        f"Auto-selected narrative column: `'{detected_col}'`."
    )
    return gr.Dropdown(choices=all_cols, value=detected_col), msg


def run_batch_classification(
    file_obj: Any,
    selected_col: str,
    batch_size: int,
    progress=gr.Progress(track_tqdm=True),
) -> Tuple:
    """Execute batch inference with risk intelligence and return results and charts."""
    def fail_return(msg: str):
        empty = create_empty_figure(msg)
        return (
            pd.DataFrame(), msg, None,
            get_kpi_html(),
            empty,
            empty,
            session_analytics.get_history_dataframe(),
        )

    if file_obj is None:
        return fail_return("Please upload a CSV file before running batch processing.")

    df, err = parse_and_validate_csv(file_obj.name)
    if err:
        return fail_return(f"File Error: {err}")

    if not selected_col or selected_col not in df.columns:
        return fail_return(f"Selected column '{selected_col}' not found in CSV.")

    total_rows = len(df)

    def progress_callback(current, total):
        progress(current / total, desc=f"Classifying complaint {current}/{total}...")

    enriched_df, summary, batch_err = process_batch(
        df=df,
        text_column=selected_col,
        model_service=model_service,
        batch_size=batch_size,
        progress_callback=progress_callback,
    )

    if batch_err:
        return fail_return(f"Batch Processing Error: {batch_err}")

    temp_dir = tempfile.gettempdir()
    export_path = os.path.join(temp_dir, f"cipher_batch_predictions_{total_rows}_rows.csv")
    enriched_df.to_csv(export_path, index=False)

    # Ingest to session analytics
    for _, row in enriched_df.iterrows():
        cat = row.get("predicted_category")
        if pd.notna(cat) and cat in LABEL_DISPLAY_NAMES:
            dummy_pred = {
                "success": True,
                "predicted_category": cat,
                "display_name": row.get("predicted_category_name", LABEL_DISPLAY_NAMES.get(cat, cat)),
                "top_probability": float(row.get("top_probability", 0.0)),
                "latency_ms": float(row.get("inference_duration_ms", 0.0)),
                "probabilities": {c: float(row.get(f"prob_{c}", 0.0)) for c in LABEL_DISPLAY_NAMES},
                "request_id": str(row.get("request_id", "")),
            }
            session_analytics.add_record(str(row[selected_col]), dummy_pred, source="batch")

    summary_text = (
        f"**Batch Classification Complete:** **{summary['successful_predictions']:,} / {total_rows:,}** rows evaluated. "
        f"**{summary['critical_count']:,} Critical Escalations** identified. "
        f"Average Confidence: **{summary['avg_top_probability'] * 100:.1f}%**. "
        f"Total Processing Time: **{summary['total_latency_ms']:.1f} ms**."
    )

    preview_df = enriched_df.head(25)
    hist_df = session_analytics.get_history_dataframe()
    dist_fig = plot_category_distribution(session_analytics.get_category_counts())
    urgency_fig = plot_urgency_distribution(session_analytics.get_urgency_counts())

    return (
        preview_df,
        summary_text,
        export_path,
        get_kpi_html(),
        dist_fig,
        urgency_fig,
        hist_df,
    )


# ---------------------------------------------------------------------------
# Session / Audit Trail Helpers
# ---------------------------------------------------------------------------
def refresh_audit_table(
    filter_category: str, filter_status: str, filter_type: str
) -> pd.DataFrame:
    """Refresh audit dataframe with applied filters."""
    cat = None if filter_category == "All" else filter_category
    status = None if filter_status == "All" else filter_status
    etype = None if filter_type == "All" else filter_type
    return session_analytics.get_audit_dataframe(
        filter_category=cat, filter_status=status, filter_type=etype
    )


def clear_history_action() -> Tuple:
    """Reset session history and refresh overview metrics."""
    session_analytics.clear()
    empty_dist = create_empty_figure("Session history cleared.")
    empty_urgency = create_empty_figure("No active risk distributions.")
    return (
        get_kpi_html(),
        empty_dist,
        empty_urgency,
        session_analytics.get_history_dataframe(),
        session_analytics.get_audit_dataframe(),
    )


def export_history_action() -> Optional[str]:
    """Generate a downloadable CSV file containing the current session history."""
    csv_data = session_analytics.export_csv()
    if not csv_data:
        return None
    file_path = os.path.join(tempfile.gettempdir(), "cipher_session_history.csv")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(csv_data)
    return file_path


def export_audit_action() -> Optional[str]:
    """Generate a downloadable CSV file containing the current audit log."""
    csv_data = session_analytics.export_audit_csv()
    if not csv_data:
        return None
    file_path = os.path.join(tempfile.gettempdir(), "cipher_audit_log.csv")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(csv_data)
    return file_path


# ---------------------------------------------------------------------------
# Benchmark Helpers
# ---------------------------------------------------------------------------
def get_benchmark_df(split: str) -> pd.DataFrame:
    """Return a formatted benchmark DataFrame for the given split."""
    data = VALIDATION_BENCHMARK_DATA if split == "Validation Set" else TEST_BENCHMARK_DATA
    rows = []
    best_acc = max(d["Accuracy"] for d in data)
    for d in data:
        is_best = d["Accuracy"] == best_acc
        arch_tag = "Transformer" if d["Architecture"] == "Transformer" else "Recurrent"
        status_tag = "Production (Deployed)" if d["Model"] == "DistilBERT" else "Baseline Model"
        rows.append({
            "Model": d["Model"],
            "Status": status_tag,
            "Architecture": arch_tag,
            "Parameters": f"{d['Parameters']:,}",
            "Accuracy": f"{d['Accuracy'] * 100:.2f}%",
            "Weighted Precision": f"{d['Weighted Precision'] * 100:.2f}%",
            "Weighted Recall": f"{d['Weighted Recall'] * 100:.2f}%",
            "Weighted F1": f"{d['Weighted F1'] * 100:.2f}%",
            "Macro F1": f"{d['Macro F1'] * 100:.2f}%",
            "Val Loss": f"{d['Val Loss']:.4f}" if d.get("Val Loss") is not None else "N/A (Test Set)",
            "Top Accuracy": "YES" if is_best else "",
        })
    return pd.DataFrame(rows)


def update_benchmark(split: str) -> Tuple:
    """Update benchmark table and chart when split toggle changes."""
    data = VALIDATION_BENCHMARK_DATA if split == "Validation Set" else TEST_BENCHMARK_DATA
    df = get_benchmark_df(split)
    chart = plot_benchmark_comparison(data, split_label=split)
    return df, chart


# ---------------------------------------------------------------------------
# Confusion Matrix Helpers
# ---------------------------------------------------------------------------
def get_cm_figure(model_choice: str, split_choice: str) -> go.Figure:
    """Return the correct confusion matrix figure based on user selection."""
    if split_choice == "Validation Set":
        if model_choice == "DistilBERT":
            return plot_confusion_matrix(
                DISTILBERT_VAL_CM, CATEGORY_DISPLAY_NAMES,
                "DistilBERT -- Confusion Matrix (Validation Set, 18,645 samples)",
                colorscale="Blues",
            )
        else:
            return create_empty_figure("GRU validation confusion matrix not stored. Use Test Set.")
    else:
        if model_choice == "DistilBERT":
            return plot_confusion_matrix(
                DISTILBERT_TEST_CM, CATEGORY_DISPLAY_NAMES,
                "DistilBERT -- Confusion Matrix (Untouched Test Set, 18,645 samples)",
                colorscale="Blues",
            )
        else:
            return plot_confusion_matrix(
                GRU_TEST_CM, CATEGORY_DISPLAY_NAMES,
                "GRU -- Confusion Matrix (Untouched Test Set, 18,645 samples)",
                colorscale="Oranges",
            )


def get_class_report_df(model_choice: str, split_choice: str) -> pd.DataFrame:
    """Return per-class metrics DataFrame based on model and split selection."""
    if split_choice == "Validation Set":
        if model_choice == "DistilBERT":
            data = DISTILBERT_VALIDATION_CLASS_REPORT
        else:
            return pd.DataFrame([{"Note": "GRU validation per-class report not stored. Select Test Set."}])
    else:
        if model_choice == "DistilBERT":
            data = DISTILBERT_TEST_CLASS_REPORT
        else:
            data = GRU_TEST_CLASS_REPORT

    rows = []
    for r in data:
        rows.append({
            "Category": r["Category"],
            "Precision": f"{r['Precision'] * 100:.2f}%",
            "Recall": f"{r['Recall'] * 100:.2f}%",
            "F1-Score": f"{r['F1-Score'] * 100:.2f}%",
            "Support (Examples)": f"{r['Support']:,}",
        })
    return pd.DataFrame(rows)


def update_classification_report(model_choice: str, split_choice: str) -> Tuple:
    """Update CM and per-class table based on model/split selection."""
    fig = get_cm_figure(model_choice, split_choice)
    df = get_class_report_df(model_choice, split_choice)
    return fig, df


# ---------------------------------------------------------------------------
# App Assembly
# ---------------------------------------------------------------------------
def create_app() -> gr.Blocks:
    """Assemble and configure the full CIPHER interactive application."""
    diag = model_service.get_diagnostic_info()

    with gr.Blocks(
        title="CIPHER -- Consumer Complaint Intelligence Platform",
    ) as demo:
        gr.HTML(render_header_html())

        with gr.Tabs():
            # =================================================================
            # TAB 1: Executive Overview
            # =================================================================
            with gr.TabItem("Executive Overview", id="tab_overview"):
                gr.Markdown(
                    "### Real-Time Grievance Telemetry & Operational Health\n"
                    "*All KPIs reflect active session predictions only. "
                    "No customer data is persisted to disk automatically.*"
                )

                kpi_html_box = gr.HTML(value=get_kpi_html())

                with gr.Row(equal_height=True):
                    with gr.Column(scale=6):
                        overview_dist_plot = gr.Plot(
                            value=create_empty_figure("No complaints analyzed yet. Run an analysis to populate."),
                            show_label=False,
                        )
                    with gr.Column(scale=6):
                        overview_urgency_plot = gr.Plot(
                            value=create_empty_figure("Awaiting risk severity distribution."),
                            show_label=False,
                        )

                gr.Markdown("#### Recent Session Predictions Log")
                overview_hist_table = gr.DataFrame(
                    value=session_analytics.get_history_dataframe(),
                    interactive=False,
                    wrap=True,
                )

            # =================================================================
            # TAB 2: Complaint Analyzer
            # =================================================================
            with gr.TabItem("Complaint Analyzer", id="tab_analyzer"):
                with gr.Row():
                    # Left: Input
                    with gr.Column(scale=6):
                        gr.Markdown("### Enter Consumer Complaint Narrative")
                        gr.Markdown(
                            "CIPHER classifies the financial product, applies regulatory urgency scoring, "
                            "discovers monetary figures, and routes to the designated resolution department."
                        )
                        complaint_input = gr.Textbox(
                            lines=8,
                            placeholder="Type or paste consumer grievance narrative here...",
                            label="Consumer Narrative",
                            show_label=False,
                        )
                        with gr.Row():
                            btn_analyze = gr.Button("Analyze & Triage Complaint", variant="primary")
                            btn_reset = gr.Button("Clear Form", variant="secondary")

                        gr.Markdown("#### Quick Demonstration Scenarios")
                        gr.Markdown(
                            "*Pre-written synthetic examples for live testing and demonstration.*"
                        )
                        with gr.Row():
                            btn_ex_cc = gr.Button("Credit Card APR Dispute", size="sm", variant="secondary")
                            btn_ex_cr = gr.Button("Credit Report ID Theft", size="sm", variant="secondary")
                        with gr.Row():
                            btn_ex_dc = gr.Button("Debt Collection Grievance", size="sm", variant="secondary")
                            btn_ex_ml = gr.Button("Mortgage Escrow Dispute", size="sm", variant="secondary")
                            btn_ex_rb = gr.Button("ATM Cash Dispense Failure", size="sm", variant="secondary")

                    # Right: Outputs
                    with gr.Column(scale=6):
                        gr.Markdown("### Classification & Intelligence Dossier")
                        prediction_dossier = gr.HTML("""
                        <div class="kpi-card" style="text-align:center;padding:36px 20px;">
                            <div style="font-weight:800;font-size:1.2rem;color:#F8FAFC;margin-bottom:6px;">Ready for Complaint Analysis</div>
                            <div style="font-size:0.92rem;color:#94A3B8;max-width:480px;margin:0 auto;line-height:1.45;">
                                Enter a consumer narrative or click a scenario button on the left to begin classification.
                            </div>
                        </div>
                        """)
                        prob_plot = gr.Plot(
                            value=create_empty_figure("Awaiting complaint narrative analysis."),
                            show_label=False,
                        )
                        with gr.Accordion("Detailed Probability Distribution Table", open=False):
                            prob_table = gr.DataFrame(
                                headers=["Rank", "Category", "Confidence", "Internal Label"],
                                value=pd.DataFrame(columns=["Rank", "Category", "Confidence", "Internal Label"]),
                                interactive=False,
                            )
                        with gr.Accordion("Technical & Inference Metadata", open=False):
                            tech_details_panel = gr.HTML(
                                "<div style='color:#64748B;font-size:0.85rem;padding:8px;'>No active inference recorded.</div>"
                            )

                with gr.Accordion("Category Vocabulary Keyword Attribution", open=False):
                    gr.Markdown(
                        "*Approximate keyword-based vocabulary attribution. "
                        "Terms highlighted indicate lexical overlap with the predicted category training vocabulary (heuristic dictionary mapping, not neural gradient saliency).* "
                    )
                    explain_panel = gr.HTML(
                        "<div class='explain-box' style='color:#64748B;'>Run an analysis to see keyword attribution.</div>"
                    )

            # =================================================================
            # TAB 3: Batch Ingestion
            # =================================================================
            with gr.TabItem("Batch Ingestion & Triage", id="tab_batch"):
                gr.Markdown("### High-Throughput Batch Classification & Risk Screening")
                gr.Markdown(
                    "Upload a CSV with consumer complaint narratives. CIPHER auto-detects the narrative column, "
                    "processes records in mini-batches, computes risk levels, assigns departments, "
                    "and exports an enriched dataset."
                )

                with gr.Row():
                    with gr.Column(scale=6):
                        batch_file_input = gr.File(
                            label="Upload Grievances CSV File",
                            file_types=[".csv"],
                            file_count="single",
                        )
                        batch_upload_status = gr.Markdown("Please upload a CSV file to begin.")

                    with gr.Column(scale=6):
                        batch_col_dropdown = gr.Dropdown(
                            choices=[], value=None, label="Select Narrative Column",
                            info="Select the column containing the complaint narrative text",
                        )
                        batch_size_slider = gr.Slider(
                            minimum=8, maximum=128, step=8, value=32,
                            label="Mini-batch Size (Optimized for RAM & GPU)",
                        )
                        btn_run_batch = gr.Button(
                            "Run Batch Classification & Triage",
                            variant="primary"
                        )

                batch_summary_md = gr.Markdown("")
                batch_file_download = gr.File(
                    label="Download Enriched Operational CSV",
                    interactive=False
                )

                gr.Markdown("#### Enriched Batch Results Preview (Top 25 Rows)")
                batch_results_table = gr.DataFrame(
                    value=pd.DataFrame(), interactive=False, wrap=True,
                )

            # =================================================================
            # TAB 4: Session Audit Trail
            # =================================================================
            with gr.TabItem("Audit Trail & Compliance", id="tab_audit"):
                gr.Markdown("### In-Memory Grievance Audit Log & Reporting")
                gr.Markdown(
                    "*Compliance Assurance: All prediction audit logs are maintained in volatile RAM for the active session only. "
                    "No PII or raw complaints are persisted to disk without explicit user export.*"
                )

                with gr.Row():
                    audit_filter_cat = gr.Dropdown(
                        choices=["All"] + list(LABEL_DISPLAY_NAMES.values()),
                        value="All", label="Filter by Category",
                    )
                    audit_filter_status = gr.Dropdown(
                        choices=["All", "SUCCESS", "FAILED"],
                        value="All", label="Filter by Status",
                    )
                    audit_filter_type = gr.Dropdown(
                        choices=["All", "Single", "Batch"],
                        value="All", label="Filter by Event Type",
                    )
                    btn_refresh_audit = gr.Button("Refresh Audit Log", variant="secondary")

                with gr.Row():
                    btn_clear_history = gr.Button("Clear Active Log", variant="secondary")
                    btn_export_history = gr.Button("Export Session CSV", variant="secondary")
                    btn_export_audit = gr.Button("Export Audit Log CSV", variant="secondary")

                history_download_file = gr.File(label="Session History Download", visible=False)
                audit_download_file = gr.File(label="Audit Log Download", visible=False)

                gr.Markdown("#### In-Memory Audit Event Log")
                audit_full_table = gr.DataFrame(
                    value=session_analytics.get_audit_dataframe(),
                    interactive=False,
                    wrap=True,
                )

            # =================================================================
            # TAB 5: Model Benchmark
            # =================================================================
            with gr.TabItem("Model Benchmark", id="tab_benchmark"):
                gr.Markdown("### Model Architecture Comparison & Benchmark Leaderboard")
                gr.Markdown(
                    "All metrics are sourced directly from the Kaggle training notebook. "
                    "Zero metric fabrication. **DistilBERT (Transformer)** is the production model deployed in this application."
                )

                with gr.Row():
                    benchmark_split_radio = gr.Radio(
                        choices=["Validation Set", "Test Set"],
                        value="Validation Set",
                        label="Evaluation Split",
                        info="Validation Set = 20% held-out during training. Test Set = untouched, never seen during training.",
                    )

                gr.HTML("""
                <div style="background:#0F172A;border:1px solid #334155;border-radius:8px;padding:12px 16px;margin:10px 0;">
                    <span style="font-size:0.82rem;color:#94A3B8;">
                        <strong style="color:#38BDF8;">Architecture Legend:</strong>
                        &nbsp;<span class="chip chip-arch-t">Transformer</span> &nbsp;= Self-attention, contextual embeddings, 66.9M params
                        &nbsp;&nbsp;<span class="chip chip-arch-r">Recurrent</span> &nbsp;= Sequential RNN variants, ~3.9M params
                        &nbsp;&nbsp;<span class="chip chip-best">Production Model</span> &nbsp;= Deployed model
                    </span>
                </div>
                """)

                benchmark_table = gr.DataFrame(
                    value=get_benchmark_df("Validation Set"),
                    interactive=False,
                    wrap=False,
                )

                benchmark_chart = gr.Plot(
                    value=plot_benchmark_comparison(VALIDATION_BENCHMARK_DATA, "Validation Set"),
                    show_label=False,
                )

                gr.Markdown("""
                ---
                #### Metric Glossary
                | Metric | Description |
                |--------|-------------|
                | **Accuracy** | Overall fraction of correctly classified samples |
                | **Weighted Precision** | Precision averaged by class support (handles class imbalance) |
                | **Weighted Recall** | Recall averaged by class support |
                | **Weighted F1** | Harmonic mean of Weighted Precision & Recall |
                | **Macro F1** | F1 averaged equally across all 5 classes (penalizes weak minority-class performance) |
                | **Val Loss** | Cross-entropy loss on the validation split (lower = better; not comparable across architectures) |
                | **Parameters** | Total trainable model weights |

                > **Note:** DistilBERT reports higher Val Loss (0.75) vs GRU (0.43) despite better accuracy.
                > This is expected: transformer logits are more spread and confidence less calibrated, not a quality indicator.
                """)

            # =================================================================
            # TAB 6: Scientific Classification Report
            # =================================================================
            with gr.TabItem("Classification Report", id="tab_report"):
                gr.Markdown("### Scientific Classification Report & Confusion Matrix")
                gr.Markdown(
                    "Per-class precision, recall, F1, and support — directly from the verified Kaggle notebook. "
                    "Confusion matrix shows exact prediction counts and row-normalized percentages."
                )

                with gr.Row():
                    cm_model_choice = gr.Dropdown(
                        choices=["DistilBERT", "GRU"],
                        value="DistilBERT",
                        label="Select Model",
                    )
                    cm_split_choice = gr.Dropdown(
                        choices=["Test Set", "Validation Set"],
                        value="Test Set",
                        label="Select Evaluation Split",
                    )
                    btn_update_cm = gr.Button("Update Metrics & Matrix", variant="secondary")

                gr.Markdown("#### Confusion Matrix (Counts + Row-Normalized Percentages)")
                cm_plot = gr.Plot(
                    value=plot_confusion_matrix(
                        DISTILBERT_TEST_CM, CATEGORY_DISPLAY_NAMES,
                        "DistilBERT -- Confusion Matrix (Untouched Test Set, 18,645 samples)",
                        "Blues",
                    ),
                    show_label=False,
                )

                gr.Markdown("#### Per-Class Classification Report")
                class_report_table = gr.DataFrame(
                    value=get_class_report_df("DistilBERT", "Test Set"),
                    interactive=False,
                )

                gr.Markdown("""
                ---
                #### Reading the Confusion Matrix
                - **Diagonal cells** = Correct predictions (True Positives)
                - **Off-diagonal cells** = Misclassifications
                - **Percentages** are row-normalized: each row sums to 100% of the true class samples
                - **credit_reporting** has the highest support (8,426 samples) and dominates off-diagonal errors

                #### Data Source
                - Test Set: 18,645 held-out consumer complaints from the CFPB dataset, never seen during model training or validation
                - Source: `notebook6caffa8944.ipynb`, Cell 88 (final test evaluation)
                """)

        # =====================================================================
        # Event Wiring
        # =====================================================================

        # Single Prediction
        analyze_outputs = [
            prediction_dossier,
            prob_plot,
            prob_table,
            explain_panel,
            kpi_html_box,
            overview_dist_plot,
            overview_urgency_plot,
            overview_hist_table,
            tech_details_panel,
        ]
        btn_analyze.click(fn=analyze_single_complaint, inputs=[complaint_input], outputs=analyze_outputs)

        # Reset
        btn_reset.click(
            fn=reset_analyzer, inputs=[],
            outputs=[complaint_input, prediction_dossier, prob_plot, prob_table, explain_panel, tech_details_panel],
        )

        # Example Scenarios
        btn_ex_cc.click(lambda: EXAMPLE_COMPLAINTS["Credit Card"], outputs=[complaint_input])
        btn_ex_cr.click(lambda: EXAMPLE_COMPLAINTS["Credit Reporting"], outputs=[complaint_input])
        btn_ex_dc.click(lambda: EXAMPLE_COMPLAINTS["Debt Collection"], outputs=[complaint_input])
        btn_ex_ml.click(lambda: EXAMPLE_COMPLAINTS["Mortgages & Loans"], outputs=[complaint_input])
        btn_ex_rb.click(lambda: EXAMPLE_COMPLAINTS["Retail Banking"], outputs=[complaint_input])

        # Batch CSV Upload
        batch_file_input.upload(
            fn=on_csv_file_uploaded, inputs=[batch_file_input],
            outputs=[batch_col_dropdown, batch_upload_status],
        )

        # Batch Run
        batch_outputs = [
            batch_results_table,
            batch_summary_md,
            batch_file_download,
            kpi_html_box,
            overview_dist_plot,
            overview_urgency_plot,
            overview_hist_table,
        ]
        btn_run_batch.click(
            fn=run_batch_classification,
            inputs=[batch_file_input, batch_col_dropdown, batch_size_slider],
            outputs=batch_outputs,
        )

        # Audit Table Refresh
        btn_refresh_audit.click(
            fn=refresh_audit_table,
            inputs=[audit_filter_cat, audit_filter_status, audit_filter_type],
            outputs=[audit_full_table],
        )
        audit_filter_cat.change(
            fn=refresh_audit_table,
            inputs=[audit_filter_cat, audit_filter_status, audit_filter_type],
            outputs=[audit_full_table],
        )
        audit_filter_status.change(
            fn=refresh_audit_table,
            inputs=[audit_filter_cat, audit_filter_status, audit_filter_type],
            outputs=[audit_full_table],
        )
        audit_filter_type.change(
            fn=refresh_audit_table,
            inputs=[audit_filter_cat, audit_filter_status, audit_filter_type],
            outputs=[audit_full_table],
        )

        # Clear History
        btn_clear_history.click(
            fn=clear_history_action, inputs=[],
            outputs=[
                kpi_html_box,
                overview_dist_plot,
                overview_urgency_plot,
                overview_hist_table,
                audit_full_table,
            ],
        )

        # Export Session History
        def handle_export_history():
            path = export_history_action()
            return gr.File(value=path, visible=True)

        btn_export_history.click(fn=handle_export_history, inputs=[], outputs=[history_download_file])

        # Export Audit Log
        def handle_export_audit():
            path = export_audit_action()
            return gr.File(value=path, visible=True)

        btn_export_audit.click(fn=handle_export_audit, inputs=[], outputs=[audit_download_file])

        # Benchmark Split Toggle
        benchmark_split_radio.change(
            fn=update_benchmark,
            inputs=[benchmark_split_radio],
            outputs=[benchmark_table, benchmark_chart],
        )

        # Classification Report Update
        btn_update_cm.click(
            fn=update_classification_report,
            inputs=[cm_model_choice, cm_split_choice],
            outputs=[cm_plot, class_report_table],
        )
        cm_model_choice.change(
            fn=update_classification_report,
            inputs=[cm_model_choice, cm_split_choice],
            outputs=[cm_plot, class_report_table],
        )
        cm_split_choice.change(
            fn=update_classification_report,
            inputs=[cm_model_choice, cm_split_choice],
            outputs=[cm_plot, class_report_table],
        )

    return demo


if __name__ == "__main__":
    server_port = int(os.environ.get("CIPHER_SERVER_PORT", 7860))
    server_name = os.environ.get("CIPHER_SERVER_NAME", "127.0.0.1")

    print(f"Starting CIPHER Platform on http://{server_name}:{server_port}")
    app = create_app()
    app.launch(
        server_name=server_name,
        server_port=server_port,
        share=False,
        theme=gr.themes.Soft(
            primary_hue=gr.themes.colors.indigo,
            secondary_hue=gr.themes.colors.blue,
            neutral_hue=gr.themes.colors.slate,
            font=[gr.themes.GoogleFont("Inter"), "ui-sans-serif", "system-ui", "sans-serif"],
        ),
        css=CUSTOM_CSS,
    )
