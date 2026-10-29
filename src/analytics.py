"""Analytics, Intelligence Enrichment, and Session Management Module for CIPHER.

Provides executive risk analysis, urgency scoring, regulatory trigger extraction,
operational department routing, benchmark data, confusion matrix generation,
lightweight explainability, and high-contrast enterprise Plotly visualizations.
"""

import io
import logging
import re
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

import pandas as pd
import plotly.graph_objects as go

from src.model_service import LABEL_DISPLAY_NAMES, ModelService

logger = logging.getLogger("CIPHER.Analytics")

# ---------------------------------------------------------------------------
# Enterprise Theme Tokens
# ---------------------------------------------------------------------------
COLOR_BG_DARK = "#0B0F19"
COLOR_CARD_DARK = "#1E293B"
COLOR_CARD_BORDER = "#334155"
COLOR_TEXT_PRIMARY = "#FFFFFF"
COLOR_TEXT_SECONDARY = "#CBD5E1"
COLOR_TEXT_MUTED = "#94A3B8"

COLOR_CYAN_ACCENT = "#00F0FF"
COLOR_EMERALD_ACCENT = "#10B981"
COLOR_INDIGO_ACCENT = "#818CF8"
COLOR_AMBER_ACCENT = "#F59E0B"
COLOR_ROSE_ACCENT = "#F43F5E"
COLOR_GRID_LINE = "rgba(148, 163, 184, 0.15)"

CATEGORY_PALETTE = {
    "credit_card": "#00F0FF",
    "credit_reporting": "#818CF8",
    "debt_collection": "#F43F5E",
    "mortgages_and_loans": "#F59E0B",
    "retail_banking": "#10B981",
}

URGENCY_PALETTE = {
    "CRITICAL": "#F43F5E",
    "HIGH": "#F59E0B",
    "MODERATE": "#00F0FF",
    "STANDARD": "#10B981",
}

DEPARTMENT_ROUTING = {
    "credit_card": {
        "department": "Cardholder Dispute & Billing Operations",
        "code": "CARD-OPS-DISP",
        "standard_sla": "48-72 Hours",
        "actions": [
            "Verify promotional APR terms, billing cycle dates, and payment timestamps.",
            "Review merchant interchange codes for disputed or foreign transaction charges.",
            "Initiate immediate provisional credit if unauthorized usage is documented.",
        ],
    },
    "credit_reporting": {
        "department": "Bureau Liaison & Consumer Fraud Unit (SIU)",
        "code": "CR-FRAUD-SIU",
        "standard_sla": "24-48 Hours",
        "actions": [
            "Cross-reference trade-line data with Equifax, Experian, and TransUnion records.",
            "Scan for active identity theft affidavits, police incident reports, or FTC filings.",
            "Issue automated 30-day FCRA dispute resolution notice and submit correction e-OSCAR.",
        ],
    },
    "debt_collection": {
        "department": "Fair Debt & Regulatory Compliance Taskforce",
        "code": "DEBT-COMPL-FDCPA",
        "standard_sla": "24 Hours (Regulatory)",
        "actions": [
            "Validate debt chain-of-title, statute of limitations, and previous settlement receipts.",
            "Enforce immediate cease-and-desist on workplace and unauthorized third-party contacts.",
            "Issue written Debt Validation Notice under FDCPA S 809 within 5 business days.",
        ],
    },
    "mortgages_and_loans": {
        "department": "Mortgage Servicing & Escrow Resolution Group",
        "code": "MTG-ESCROW-APPL",
        "standard_sla": "48 Hours",
        "actions": [
            "Recalculate annual escrow analysis and verify certified county property tax receipts.",
            "Halt foreclosure or delinquent reporting clock pending loan audit review.",
            "Issue formal RESPA Notice of Error (NOE) acknowledgment to the borrower.",
        ],
    },
    "retail_banking": {
        "department": "Depository Services & EFT Dispute Division",
        "code": "BANK-EFT-PROV",
        "standard_sla": "24-48 Hours",
        "actions": [
            "Pull ATM hardware journal logs and cash dispenser sensor reconciliation files.",
            "Issue mandatory provisional credit under Regulation E within 10 business days.",
            "Review hold parameters on deposited cashier's checks against Expedited Funds Availability Act.",
        ],
    },
}

CRITICAL_TRIGGERS = [
    r"\blawyer\b", r"\battorney\b", r"\blawsuit\b", r"\bsue\b", r"\bcourt\b",
    r"\bcfpb\b", r"\bpolice\b", r"\bidentity theft\b", r"\bfraud\b", r"\bforeclosure\b",
    r"\brepossession\b", r"\bgarnishment\b", r"\bftc\b", r"\bbankruptcy\b",
]

HIGH_TRIGGERS = [
    r"\bharass(?:ment|ing)?\b", r"\bthreat(?:en|ening)?\b", r"\brepeatedly\b",
    r"\bbounced\b", r"\bruined\b", r"\billegal\b", r"\burgent\b", r"\bsupervisor\b",
    r"\bunauthorized\b", r"\bdelinquent\b",
]

CANDIDATE_TEXT_COLUMNS = [
    "narrative",
    "complaint",
    "complaint_text",
    "text",
    "consumer_complaint_narrative",
    "issue_description",
    "description",
    "consumer_narrative",
]

# ---------------------------------------------------------------------------
# Keyword Explainability — Category-Specific Keyword Banks
# ---------------------------------------------------------------------------
CATEGORY_KEYWORDS: Dict[str, List[str]] = {
    "credit_card": [
        "credit card", "apr", "interest rate", "balance", "statement", "billing",
        "annual fee", "cash advance", "rewards", "points", "minimum payment",
        "chargeback", "dispute", "unauthorized charge", "merchant", "cashback",
        "promotional rate", "promo", "finance charge", "penalty", "card",
    ],
    "credit_reporting": [
        "credit report", "credit bureau", "equifax", "experian", "transunion",
        "credit score", "fico", "trade line", "derogatory", "collection account",
        "late payment", "inaccurate", "dispute", "investigation", "fcra",
        "identity theft", "fraud alert", "freeze", "verification", "credit history",
    ],
    "debt_collection": [
        "debt collector", "collection agency", "collection call", "debt",
        "fdcpa", "cease and desist", "validation", "garnishment", "wage",
        "harassment", "threatening", "called repeatedly", "third party",
        "medical bill", "original creditor", "charged off", "zombie debt",
        "statute of limitations", "settlement",
    ],
    "mortgages_and_loans": [
        "mortgage", "loan", "escrow", "foreclosure", "refinance", "servicer",
        "payment", "property tax", "insurance", "lender", "borrower",
        "modification", "forbearance", "underwater", "heloc", "home equity",
        "interest rate", "amortization", "principal", "deed", "title",
    ],
    "retail_banking": [
        "bank account", "checking", "savings", "atm", "withdrawal", "deposit",
        "overdraft", "direct deposit", "wire transfer", "ach", "electronic",
        "debit card", "transaction", "hold", "regulation e", "funds availability",
        "branch", "teller", "zelle", "venmo", "mobile banking",
    ],
}


def _generate_request_id() -> str:
    """Generate a unique request reference ID."""
    return f"CIPHER-REQ-{uuid.uuid4().hex[:10].upper()}"


def _generate_event_id() -> str:
    """Generate a unique audit event ID."""
    return f"CIPHER-EVT-{uuid.uuid4().hex[:10].upper()}"


def explain_prediction(text: str, predicted_category: str) -> Dict[str, Any]:
    """Lightweight keyword-based approximate attribution for a prediction.

    This is a transparent heuristic approach, not neural saliency or SHAP.
    Matched keywords from the predicted category vocabulary are highlighted.

    Returns:
        dict with matched_keywords, highlight_html, method_note.
    """
    text_lower = text.lower()
    words = CATEGORY_KEYWORDS.get(predicted_category, [])
    matched = []
    for kw in words:
        if kw in text_lower:
            matched.append(kw)

    truncated = text[:600] + ("..." if len(text) > 600 else "")
    highlighted = truncated
    for kw in matched[:8]:
        pattern = re.compile(re.escape(kw), re.IGNORECASE)
        highlighted = pattern.sub(
            '<mark style="background:#1E4D6B;color:#67E8F9;padding:1px 3px;border-radius:3px;">' + kw + '</mark>',
            highlighted,
        )

    return {
        "matched_keywords": matched[:10],
        "highlight_html": highlighted,
        "method_note": (
            "Approximate attribution via keyword vocabulary matching "
            "- not neural saliency. Highlighted terms are associated with the predicted category."
        ),
    }


def extract_complaint_intelligence(text: str, prediction: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze complaint narrative for urgency, key financial triggers, and departmental routing."""
    text_lower = text.lower()

    matched_critical = [t.strip(r"\b") for t in CRITICAL_TRIGGERS if re.search(t, text_lower)]
    matched_high = [t.strip(r"\b") for t in HIGH_TRIGGERS if re.search(t, text_lower)]

    if matched_critical:
        urgency_level = "CRITICAL"
        urgency_badge = "CRITICAL RISK"
        urgency_color = "#F43F5E"
        sla_window = "< 24 Hours (Regulatory Flag)"
    elif matched_high:
        urgency_level = "HIGH"
        urgency_badge = "HIGH PRIORITY"
        urgency_color = "#F59E0B"
        sla_window = "< 48 Hours"
    elif prediction.get("top_probability", 0) > 0.85:
        urgency_level = "MODERATE"
        urgency_badge = "MODERATE"
        urgency_color = "#00F0FF"
        sla_window = "3 - 5 Business Days"
    else:
        urgency_level = "STANDARD"
        urgency_badge = "STANDARD"
        urgency_color = "#10B981"
        sla_window = "5 - 7 Business Days"

    monetary_matches = re.findall(r"\$\s?[0-9,]+(?:\.[0-9]{2})?", text)
    monetary_entities = list(dict.fromkeys(monetary_matches))[:3]

    found_triggers = list(dict.fromkeys(matched_critical + matched_high))[:5]
    if not found_triggers:
        found_triggers = ["standard_consumer_inquiry"]

    cat_key = prediction.get("predicted_category", "retail_banking")
    dept_info = DEPARTMENT_ROUTING.get(cat_key, DEPARTMENT_ROUTING["retail_banking"])

    probs = prediction.get("probabilities", {})
    sorted_probs = sorted(probs.items(), key=lambda item: item[1], reverse=True)
    ambiguity_flag = False
    secondary_category = None
    if len(sorted_probs) >= 2:
        top_diff = sorted_probs[0][1] - sorted_probs[1][1]
        if top_diff < 0.18 and sorted_probs[1][1] > 0.20:
            ambiguity_flag = True
            sec_key = sorted_probs[1][0]
            secondary_category = LABEL_DISPLAY_NAMES.get(sec_key, sec_key)

    top_prob = prediction.get("top_probability", 1.0)
    requires_human_review = urgency_level == "CRITICAL" or top_prob < 0.60 or ambiguity_flag
    human_review_reasons = []
    if urgency_level == "CRITICAL":
        human_review_reasons.append("Critical regulatory triggers detected")
    if top_prob < 0.60:
        human_review_reasons.append(f"Low model confidence ({top_prob * 100:.1f}%)")
    if ambiguity_flag:
        human_review_reasons.append(f"Cross-department ambiguity with {secondary_category}")

    return {
        "urgency_level": urgency_level,
        "urgency_badge": urgency_badge,
        "urgency_color": urgency_color,
        "sla_window": sla_window,
        "monetary_entities": monetary_entities,
        "key_triggers": found_triggers,
        "department": dept_info["department"],
        "dept_code": dept_info["code"],
        "recommended_actions": dept_info["actions"],
        "ambiguity_flag": ambiguity_flag,
        "secondary_category": secondary_category,
        "requires_human_review": requires_human_review,
        "human_review_reason": "; ".join(human_review_reasons) if human_review_reasons else None,
    }


# ---------------------------------------------------------------------------
# Verified Benchmark Data (extracted from Kaggle notebook, zero fabrication)
# ---------------------------------------------------------------------------
CATEGORIES = ["credit_card", "credit_reporting", "debt_collection", "mortgages_and_loans", "retail_banking"]

VALIDATION_BENCHMARK_DATA = [
    {
        "Model": "DistilBERT", "Architecture": "Transformer", "Parameters": 66957317,
        "Accuracy": 0.8685, "Weighted Precision": 0.8679, "Weighted Recall": 0.8685,
        "Weighted F1": 0.8679, "Macro F1": 0.8537, "Val Loss": 0.7502,
    },
    {
        "Model": "GRU", "Architecture": "Recurrent", "Parameters": 3877573,
        "Accuracy": 0.8575, "Weighted Precision": 0.8572, "Weighted Recall": 0.8575,
        "Weighted F1": 0.8571, "Macro F1": 0.8401, "Val Loss": 0.4250,
    },
    {
        "Model": "LSTM", "Architecture": "Recurrent", "Parameters": 3889733,
        "Accuracy": 0.8424, "Weighted Precision": 0.8422, "Weighted Recall": 0.8424,
        "Weighted F1": 0.8418, "Macro F1": 0.8211, "Val Loss": 0.4788,
    },
    {
        "Model": "SimpleRNN", "Architecture": "Recurrent", "Parameters": 3852677,
        "Accuracy": 0.7707, "Weighted Precision": 0.7691, "Weighted Recall": 0.7707,
        "Weighted F1": 0.7693, "Macro F1": 0.7361, "Val Loss": 0.6776,
    },
]

TEST_BENCHMARK_DATA = [
    {
        "Model": "DistilBERT", "Architecture": "Transformer", "Parameters": 66957317,
        "Accuracy": 0.8650, "Weighted Precision": 0.8648, "Weighted Recall": 0.8650,
        "Weighted F1": 0.8647, "Macro F1": 0.8521, "Val Loss": None,
    },
    {
        "Model": "GRU", "Architecture": "Recurrent", "Parameters": 3877573,
        "Accuracy": 0.8521, "Weighted Precision": 0.8520, "Weighted Recall": 0.8521,
        "Weighted F1": 0.8519, "Macro F1": 0.8362, "Val Loss": None,
    },
]

DISTILBERT_TEST_CLASS_REPORT = [
    {"Category": "Credit Card",       "Precision": 0.8042, "Recall": 0.8361, "F1-Score": 0.8198, "Support": 2245},
    {"Category": "Credit Reporting",  "Precision": 0.8909, "Recall": 0.9055, "F1-Score": 0.8982, "Support": 8426},
    {"Category": "Debt Collection",   "Precision": 0.8210, "Recall": 0.7790, "F1-Score": 0.7994, "Support": 3149},
    {"Category": "Mortgages & Loans", "Precision": 0.8747, "Recall": 0.8460, "F1-Score": 0.8601, "Support": 2805},
    {"Category": "Retail Banking",    "Precision": 0.8773, "Recall": 0.8886, "F1-Score": 0.8829, "Support": 2020},
]

GRU_TEST_CLASS_REPORT = [
    {"Category": "Credit Card",       "Precision": 0.8009, "Recall": 0.7742, "F1-Score": 0.7873, "Support": 2245},
    {"Category": "Credit Reporting",  "Precision": 0.8832, "Recall": 0.8947, "F1-Score": 0.8889, "Support": 8426},
    {"Category": "Debt Collection",   "Precision": 0.7936, "Recall": 0.7971, "F1-Score": 0.7953, "Support": 3149},
    {"Category": "Mortgages & Loans", "Precision": 0.8738, "Recall": 0.8292, "F1-Score": 0.8509, "Support": 2805},
    {"Category": "Retail Banking",    "Precision": 0.8396, "Recall": 0.8787, "F1-Score": 0.8587, "Support": 2020},
]

DISTILBERT_VALIDATION_CLASS_REPORT = [
    {"Category": "Credit Card",       "Precision": 0.8146, "Recall": 0.8182, "F1-Score": 0.8164, "Support": 2244},
    {"Category": "Credit Reporting",  "Precision": 0.8926, "Recall": 0.9170, "F1-Score": 0.9046, "Support": 8426},
    {"Category": "Debt Collection",   "Precision": 0.8264, "Recall": 0.7844, "F1-Score": 0.8049, "Support": 3150},
    {"Category": "Mortgages & Loans", "Precision": 0.8784, "Recall": 0.8367, "F1-Score": 0.8570, "Support": 2805},
    {"Category": "Retail Banking",    "Precision": 0.8745, "Recall": 0.8970, "F1-Score": 0.8856, "Support": 2020},
]

# Test set confusion matrices (extracted from Cell 88 plot)
DISTILBERT_TEST_CM = [
    [1877, 153,  42,  25, 148],
    [ 191, 7630, 393, 178,  34],
    [ 104,  469, 2453, 102,  21],
    [  32,  275,  77, 2373,  48],
    [ 130,   37,  23,  35, 1795],
]

GRU_TEST_CM = [
    [1738, 205,  61,  16, 225],
    [ 191, 7539, 487, 185,  24],
    [  76,  446, 2510,  93,  24],
    [  34,  309,  70, 2326,  66],
    [ 131,   37,  35,  42, 1775],
]

DISTILBERT_VAL_CM = [
    [1836, 180,  46,  26, 156],
    [ 165, 7727, 354, 147,  33],
    [  89,  445, 2471, 115,  30],
    [  41,  271, 105, 2347,  41],
    [ 123,   34,  14,  37, 1812],
]

CATEGORY_DISPLAY_NAMES = [
    "Credit Card", "Credit Reporting", "Debt Collection",
    "Mortgages & Loans", "Retail Banking",
]


# ---------------------------------------------------------------------------
# Session Analytics
# ---------------------------------------------------------------------------
class SessionAnalytics:
    """Manages in-memory complaint prediction history and session-wide metrics."""

    def __init__(self):
        self.history: List[Dict[str, Any]] = []
        self._audit_log: List[Dict[str, Any]] = []

    def add_record(
        self,
        complaint_text: str,
        prediction: Dict[str, Any],
        source: str = "single",
    ) -> str:
        """Add an enriched prediction result to the in-memory session history.

        Returns:
            The unique request_id for this record.
        """
        request_id = prediction.get("request_id") or _generate_request_id()
        event_id = _generate_event_id()

        if not prediction.get("success"):
            self._audit_log.append({
                "event_id": event_id,
                "request_id": request_id,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "event_type": "Single" if source == "single" else "Batch",
                "model_name": "DistilBERT-base-uncased (fine-tuned)",
                "model_version": "v1.0",
                "category": "---",
                "confidence": "---",
                "status": "FAILED",
                "latency_ms": prediction.get("latency_ms", 0.0),
                "requires_human_review": False,
                "human_review_reason": "---",
            })
            return request_id

        preview = complaint_text.strip().replace("\n", " ")
        if len(preview) > 130:
            preview = preview[:127] + "..."

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        intel = extract_complaint_intelligence(complaint_text, prediction)

        record = {
            "request_id": request_id,
            "event_id": event_id,
            "timestamp": timestamp,
            "preview": preview,
            "full_text": complaint_text.strip(),
            "predicted_category": prediction["predicted_category"],
            "display_name": prediction["display_name"],
            "top_probability": round(prediction["top_probability"], 4),
            "latency_ms": prediction["latency_ms"],
            "probabilities": prediction["probabilities"],
            "urgency_level": intel["urgency_level"],
            "department": intel["department"],
            "sla_window": intel["sla_window"],
            "source": source,
            "requires_human_review": intel["requires_human_review"],
            "human_review_reason": intel.get("human_review_reason"),
        }
        self.history.append(record)

        self._audit_log.append({
            "event_id": event_id,
            "request_id": request_id,
            "timestamp": timestamp,
            "event_type": "Single" if source == "single" else "Batch",
            "model_name": "DistilBERT-base-uncased (fine-tuned)",
            "model_version": "v1.0",
            "category": prediction["display_name"],
            "confidence": f"{prediction['top_probability'] * 100:.2f}%",
            "status": "SUCCESS",
            "latency_ms": prediction["latency_ms"],
            "requires_human_review": intel["requires_human_review"],
            "human_review_reason": intel.get("human_review_reason") or "---",
        })

        return request_id

    def get_summary_metrics(self) -> Dict[str, Any]:
        """Compute aggregate summary metrics across the current session."""
        total = len(self.history)
        failed_count = len([a for a in self._audit_log if a.get("status") == "FAILED"])

        if total == 0:
            return {
                "total_analyzed": 0,
                "distinct_categories": 0,
                "avg_top_probability": "---",
                "avg_latency_ms": "---",
                "critical_count": 0,
                "human_review_count": 0,
                "success_count": 0,
                "failed_count": failed_count,
            }

        distinct = len(set(r["predicted_category"] for r in self.history))
        avg_prob = sum(r["top_probability"] for r in self.history) / total
        avg_lat = sum(r["latency_ms"] for r in self.history) / total
        critical_count = sum(1 for r in self.history if r.get("urgency_level") == "CRITICAL")
        human_review_count = sum(1 for r in self.history if r.get("requires_human_review"))

        return {
            "total_analyzed": total,
            "distinct_categories": distinct,
            "avg_top_probability": f"{avg_prob * 100:.1f}%",
            "avg_latency_ms": f"{avg_lat:.1f} ms",
            "critical_count": critical_count,
            "human_review_count": human_review_count,
            "success_count": total,
            "failed_count": failed_count,
        }

    def get_category_counts(self) -> Dict[str, int]:
        """Return counts of each predicted category."""
        counts = {cat: 0 for cat in LABEL_DISPLAY_NAMES}
        for record in self.history:
            cat = record["predicted_category"]
            if cat in counts:
                counts[cat] += 1
            else:
                counts[cat] = 1
        return counts

    def get_urgency_counts(self) -> Dict[str, int]:
        """Return counts of each urgency category."""
        counts = {"CRITICAL": 0, "HIGH": 0, "MODERATE": 0, "STANDARD": 0}
        for record in self.history:
            u = record.get("urgency_level", "STANDARD")
            if u in counts:
                counts[u] += 1
        return counts

    def get_history_dataframe(self) -> pd.DataFrame:
        """Return a formatted DataFrame of recent session predictions."""
        if not self.history:
            return pd.DataFrame(columns=[
                "Timestamp", "Complaint Preview", "Predicted Category",
                "Risk Level", "Target Department", "Confidence", "Latency",
            ])

        rows = []
        for r in reversed(self.history):
            rows.append({
                "Timestamp": r["timestamp"],
                "Complaint Preview": r["preview"],
                "Predicted Category": r["display_name"],
                "Risk Level": r.get("urgency_level", "STANDARD"),
                "Target Department": r.get("department", "Operations"),
                "Confidence": f"{r['top_probability'] * 100:.2f}%",
                "Latency": f"{r['latency_ms']:.1f} ms",
            })
        return pd.DataFrame(rows)

    def get_audit_dataframe(
        self,
        filter_category: Optional[str] = None,
        filter_status: Optional[str] = None,
        filter_type: Optional[str] = None,
    ) -> pd.DataFrame:
        """Return structured audit trail as DataFrame with optional filters."""
        empty_cols = [
            "Event ID", "Request ID", "Timestamp", "Event Type",
            "Model", "Category", "Confidence", "Status", "Latency (ms)", "Human Review",
        ]
        if not self._audit_log:
            return pd.DataFrame(columns=empty_cols)

        rows = []
        for a in reversed(self._audit_log):
            if filter_category and filter_category != "All" and a.get("category") != filter_category:
                continue
            if filter_status and filter_status != "All" and a.get("status") != filter_status:
                continue
            if filter_type and filter_type != "All" and a.get("event_type") != filter_type:
                continue
            rows.append({
                "Event ID": a["event_id"],
                "Request ID": a["request_id"],
                "Timestamp": a["timestamp"],
                "Event Type": a.get("event_type", "Single"),
                "Model": "DistilBERT v1.0",
                "Category": a.get("category", "---"),
                "Confidence": a.get("confidence", "---"),
                "Status": a.get("status", "---"),
                "Latency (ms)": a.get("latency_ms", 0.0),
                "Human Review": "Required" if a.get("requires_human_review") else "---",
            })

        if not rows:
            return pd.DataFrame(columns=empty_cols)
        return pd.DataFrame(rows)

    def export_csv(self) -> str:
        """Export session history as a CSV formatted string."""
        if not self.history:
            return ""

        rows = []
        for r in self.history:
            row_dict = {
                "request_id": r.get("request_id", ""),
                "timestamp": r["timestamp"],
                "predicted_category": r["predicted_category"],
                "category_display_name": r["display_name"],
                "top_probability": r["top_probability"],
                "risk_urgency": r.get("urgency_level", "STANDARD"),
                "assigned_department": r.get("department", "Operations"),
                "sla_window": r.get("sla_window", "48h"),
                "latency_ms": r["latency_ms"],
                "requires_human_review": r.get("requires_human_review", False),
                "complaint_text": r["full_text"],
            }
            for cat, prob in r["probabilities"].items():
                row_dict[f"prob_{cat}"] = round(prob, 4)
            rows.append(row_dict)

        df = pd.DataFrame(rows)
        return df.to_csv(index=False)

    def export_audit_csv(self) -> str:
        """Export audit log as CSV string."""
        df = self.get_audit_dataframe()
        return df.to_csv(index=False)

    def clear(self) -> None:
        """Clear the in-memory session history and audit log."""
        self.history.clear()
        self._audit_log.clear()


# ---------------------------------------------------------------------------
# Plotly Visualizations
# ---------------------------------------------------------------------------
def create_empty_figure(message: str) -> go.Figure:
    """Return a styled empty Plotly figure displaying a helpful state message."""
    fig = go.Figure()
    fig.add_annotation(
        text=f"<b>{message}</b>",
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.5,
        showarrow=False,
        font=dict(size=14, color=COLOR_TEXT_MUTED, family="Inter, system-ui, sans-serif"),
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        margin=dict(l=20, r=20, t=30, b=20),
        height=260,
    )
    return fig


def plot_probability_bars(
    probabilities: Dict[str, float], predicted_category: Optional[str] = None
) -> go.Figure:
    """Create a high-contrast horizontal bar chart of the 5 class probabilities."""
    if not probabilities:
        return create_empty_figure("No probability data available.")

    sorted_items = sorted(probabilities.items(), key=lambda item: item[1])
    categories = [k for k, _ in sorted_items]
    display_labels = [
        "<b>" + LABEL_DISPLAY_NAMES.get(k, k.replace("_", " ").title()) + "</b>"
        for k in categories
    ]
    values = [v for _, v in sorted_items]

    colors = []
    for cat in categories:
        if cat == predicted_category:
            colors.append(COLOR_CYAN_ACCENT)
        else:
            colors.append("rgba(129, 140, 248, 0.45)")

    text_labels = [f"<b>{v * 100:.1f}%</b>" for v in values]

    fig = go.Figure(
        go.Bar(
            x=values,
            y=display_labels,
            orientation="h",
            marker=dict(
                color=colors,
                line=dict(color="#38BDF8" if predicted_category else "rgba(255,255,255,0.2)", width=1.5),
                cornerradius=6,
            ),
            text=text_labels,
            textposition="outside",
            textfont=dict(color=COLOR_TEXT_PRIMARY, size=13, family="Inter, system-ui, sans-serif"),
            cliponaxis=False,
            hoverinfo="y+text",
        )
    )

    max_val = max(values) if values else 1.0
    x_range = [0, max(1.10, max_val * 1.25)]

    fig.update_layout(
        title=dict(
            text="<b>Classification Probabilities</b>  (Softmax Output, Uncalibrated)",
            font=dict(color="#F8FAFC", size=15, family="Inter, system-ui, sans-serif"),
            x=0.02,
            y=0.96,
        ),
        paper_bgcolor="#1E293B",
        plot_bgcolor="#0F172A",
        xaxis=dict(
            title="<b>Uncalibrated Probability Distribution</b>",
            title_font=dict(color="#CBD5E1", size=12),
            tickfont=dict(color="#CBD5E1", size=11),
            showgrid=True,
            gridcolor="rgba(255, 255, 255, 0.08)",
            zeroline=True,
            zerolinecolor="rgba(255, 255, 255, 0.08)",
            range=x_range,
            tickformat=".0%",
        ),
        yaxis=dict(
            tickfont=dict(color="#F8FAFC", size=13, family="Inter, system-ui, sans-serif"),
            showgrid=False,
        ),
        margin=dict(l=150, r=40, t=50, b=40),
        height=270,
    )
    return fig


def plot_category_distribution(counts: Dict[str, int]) -> go.Figure:
    """Create a high-contrast bar chart showing session category distribution."""
    total = sum(counts.values())
    if total == 0:
        return create_empty_figure("No prediction records logged yet.")

    cats = list(counts.keys())
    display_names = [
        "<b>" + LABEL_DISPLAY_NAMES.get(c, c.replace("_", " ").title()) + "</b>"
        for c in cats
    ]
    values = [counts[c] for c in cats]
    colors = [CATEGORY_PALETTE.get(c, COLOR_CYAN_ACCENT) for c in cats]

    fig = go.Figure(
        go.Bar(
            x=display_names,
            y=values,
            marker=dict(
                color=colors,
                cornerradius=6,
                line=dict(color="rgba(255,255,255,0.15)", width=1),
            ),
            text=[
                f"<b>{v} ({v / total * 100:.1f}%)</b>" if total > 0 else f"{v}"
                for v in values
            ],
            textposition="outside",
            textfont=dict(color=COLOR_TEXT_PRIMARY, size=12, family="Inter, system-ui, sans-serif"),
            cliponaxis=False,
        )
    )

    max_val = max(values) if values else 1
    y_range = [0, max(max_val * 1.30, 4)]

    fig.update_layout(
        title=dict(
            text="<b>Session Category Distribution</b>",
            font=dict(color="#F8FAFC", size=15, family="Inter, system-ui, sans-serif"),
            x=0.02,
        ),
        paper_bgcolor="#1E293B",
        plot_bgcolor="#0F172A",
        xaxis=dict(
            tickfont=dict(color="#F8FAFC", size=12, family="Inter, system-ui, sans-serif"),
            showgrid=False,
        ),
        yaxis=dict(
            title="<b>Complaints Count</b>",
            title_font=dict(color="#CBD5E1", size=12),
            tickfont=dict(color="#CBD5E1", size=11),
            showgrid=True,
            gridcolor="rgba(255, 255, 255, 0.08)",
            range=y_range,
        ),
        margin=dict(l=40, r=20, t=50, b=40),
        height=280,
    )
    return fig


def plot_urgency_distribution(counts: Dict[str, int]) -> go.Figure:
    """Create a clean donut chart showing Risk and Urgency breakdown."""
    total = sum(counts.values())
    if total == 0:
        return create_empty_figure("No batch risk data available.")

    labels = ["Critical Risk", "High Priority", "Moderate", "Standard"]
    keys = ["CRITICAL", "HIGH", "MODERATE", "STANDARD"]
    values = [counts.get(k, 0) for k in keys]
    colors = [URGENCY_PALETTE[k] for k in keys]

    filtered_labels = [labels[i] for i, v in enumerate(values) if v > 0]
    filtered_values = [v for v in values if v > 0]
    filtered_colors = [colors[i] for i, v in enumerate(values) if v > 0]

    if not filtered_values:
        return create_empty_figure("No active risk distributions.")

    fig = go.Figure(
        data=[
            go.Pie(
                labels=filtered_labels,
                values=filtered_values,
                hole=0.55,
                marker=dict(colors=filtered_colors, line=dict(color="#1E293B", width=2)),
                textinfo="label+percent",
                textfont=dict(color="#F8FAFC", size=12, family="Inter, system-ui, sans-serif"),
                hoverinfo="label+value+percent",
            )
        ]
    )

    fig.update_layout(
        title=dict(
            text="<b>Risk Severity and Regulatory Escalations</b>",
            font=dict(color="#F8FAFC", size=15, family="Inter, system-ui, sans-serif"),
            x=0.02,
        ),
        paper_bgcolor="#1E293B",
        plot_bgcolor="#0F172A",
        showlegend=True,
        legend=dict(
            font=dict(color="#F8FAFC", size=11),
            orientation="h",
            yanchor="bottom",
            y=-0.2,
            xanchor="center",
            x=0.5,
        ),
        margin=dict(l=20, r=20, t=50, b=30),
        height=280,
    )
    return fig


def plot_benchmark_comparison(data: List[Dict], split_label: str = "Validation Set") -> go.Figure:
    """Create grouped bar chart comparing model benchmark metrics."""
    models = [d["Model"] for d in data]
    metrics_info = [
        ("Accuracy", "Accuracy", "#38BDF8"),
        ("Weighted F1", "Weighted F1", "#818CF8"),
        ("Macro F1", "Macro F1", "#F59E0B"),
    ]

    fig = go.Figure()

    for metric_label, metric_key, color in metrics_info:
        vals = [d.get(metric_key, d.get("Weighted F1", 0)) for d in data]
        fig.add_trace(
            go.Bar(
                name=metric_label,
                x=models,
                y=vals,
                marker=dict(color=color, cornerradius=4),
                text=[f"<b>{v * 100:.2f}%</b>" for v in vals],
                textposition="outside",
                textfont=dict(color="#F8FAFC", size=11),
                cliponaxis=False,
            )
        )

    fig.update_layout(
        title=dict(
            text=f"<b>Model Comparison  {split_label}</b>",
            font=dict(color="#F8FAFC", size=15, family="Inter, system-ui, sans-serif"),
            x=0.02,
        ),
        barmode="group",
        paper_bgcolor="#1E293B",
        plot_bgcolor="#0F172A",
        xaxis=dict(
            tickfont=dict(color="#F8FAFC", size=13, family="Inter, system-ui, sans-serif"),
            showgrid=False,
        ),
        yaxis=dict(
            title="<b>Score</b>",
            title_font=dict(color="#CBD5E1", size=12),
            tickfont=dict(color="#CBD5E1", size=11),
            showgrid=True,
            gridcolor="rgba(255,255,255,0.08)",
            range=[0.70, 0.92],
            tickformat=".0%",
        ),
        legend=dict(
            font=dict(color="#F8FAFC", size=12),
            bgcolor="rgba(0,0,0,0)",
        ),
        margin=dict(l=50, r=20, t=55, b=40),
        height=320,
    )
    return fig


def plot_confusion_matrix(
    cm: List[List[int]],
    labels: List[str],
    title: str,
    colorscale: str = "Blues",
) -> go.Figure:
    """Create an annotated Plotly heatmap confusion matrix with counts and normalized percentages."""
    n = len(labels)
    row_sums = [sum(cm[i]) for i in range(n)]

    annotations_text = []
    for i in range(n):
        row_texts = []
        for j in range(n):
            count = cm[i][j]
            pct = (count / row_sums[i] * 100) if row_sums[i] > 0 else 0
            row_texts.append(f"{count}<br>({pct:.1f}%)")
        annotations_text.append(row_texts)

    fig = go.Figure(
        data=go.Heatmap(
            z=cm,
            x=labels,
            y=labels,
            colorscale=colorscale,
            showscale=True,
            text=annotations_text,
            texttemplate="%{text}",
            textfont=dict(size=10, color="#0F172A", family="Inter, system-ui, sans-serif"),
            hovertemplate="True: %{y}<br>Predicted: %{x}<br>Count: %{z}<extra></extra>",
            reversescale=False,
        )
    )

    fig.update_layout(
        title=dict(
            text=f"<b>{title}</b>",
            font=dict(color="#F8FAFC", size=14, family="Inter, system-ui, sans-serif"),
            x=0.02,
        ),
        paper_bgcolor="#1E293B",
        plot_bgcolor="#0F172A",
        xaxis=dict(
            title="<b>Predicted Label</b>",
            title_font=dict(color="#CBD5E1", size=12),
            tickfont=dict(color="#F8FAFC", size=11),
            tickangle=-30,
            side="bottom",
        ),
        yaxis=dict(
            title="<b>True Label</b>",
            title_font=dict(color="#CBD5E1", size=12),
            tickfont=dict(color="#F8FAFC", size=11),
            autorange="reversed",
        ),
        margin=dict(l=160, r=40, t=60, b=130),
        height=450,
    )
    return fig


# ---------------------------------------------------------------------------
# Batch File Ingestion and Processing
# ---------------------------------------------------------------------------
def parse_and_validate_csv(
    file_path_or_bytes: Union[str, bytes],
) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """Load and validate an uploaded CSV file."""
    try:
        if isinstance(file_path_or_bytes, bytes):
            df = pd.read_csv(io.BytesIO(file_path_or_bytes))
        else:
            df = pd.read_csv(file_path_or_bytes)

        if df.empty:
            return None, "The uploaded CSV file contains no data rows."

        if len(df.columns) == 0:
            return None, "No columns detected in the uploaded file."

        return df, None
    except Exception as e:
        logger.error(f"Failed to parse CSV: {e}")
        return None, f"Failed to parse CSV file: {str(e)}"


def detect_text_column(df: pd.DataFrame) -> Tuple[str, List[str]]:
    """Identify the most likely text narrative column and return all candidates."""
    all_cols = list(df.columns)

    for candidate in CANDIDATE_TEXT_COLUMNS:
        for col in all_cols:
            if str(col).strip().lower() == candidate:
                return col, all_cols

    for col in all_cols:
        col_lower = str(col).strip().lower()
        if "text" in col_lower or "narrative" in col_lower or "complaint" in col_lower:
            return col, all_cols

    for col in all_cols:
        if pd.api.types.is_string_dtype(df[col]):
            return col, all_cols

    return all_cols[0], all_cols


def process_batch(
    df: pd.DataFrame,
    text_column: str,
    model_service: ModelService,
    batch_size: int = 32,
    progress_callback: Optional[Any] = None,
) -> Tuple[Optional[pd.DataFrame], Dict[str, Any], Optional[str]]:
    """Process a DataFrame of complaints with model inference and risk intelligence."""
    if text_column not in df.columns:
        return None, {}, f"Selected column '{text_column}' does not exist in the dataset."

    texts = df[text_column].fillna("").astype(str).tolist()
    total = len(texts)

    if total == 0:
        return None, {}, "No rows to process."

    logger.info(
        f"Processing batch of {total} rows with column '{text_column}' "
        f"and batch_size={batch_size}"
    )
    results = model_service.predict_batch(
        texts, batch_size=batch_size, progress_callback=progress_callback
    )

    enriched_df = df.copy()

    pred_categories: List[Optional[str]] = []
    display_names: List[Optional[str]] = []
    top_probs: List[float] = []
    latencies: List[float] = []
    urgencies: List[str] = []
    departments: List[str] = []
    sla_windows: List[str] = []
    request_ids: List[str] = []

    prob_cols: Dict[str, List[float]] = {cat: [] for cat in LABEL_DISPLAY_NAMES}

    success_count = 0
    fail_count = 0
    critical_count = 0

    for i, res in enumerate(results):
        raw_text = texts[i]
        req_id = _generate_request_id()
        request_ids.append(req_id)

        if res.get("success"):
            success_count += 1
            cat_key = res["predicted_category"]
            pred_categories.append(cat_key)
            display_names.append(res["display_name"])
            top_probs.append(round(res["top_probability"], 4))
            latencies.append(res["latency_ms"])

            intel = extract_complaint_intelligence(raw_text, res)
            urgencies.append(intel["urgency_level"])
            departments.append(intel["department"])
            sla_windows.append(intel["sla_window"])

            if intel["urgency_level"] == "CRITICAL":
                critical_count += 1

            for cat in LABEL_DISPLAY_NAMES:
                prob_cols[cat].append(round(res["probabilities"].get(cat, 0.0), 4))
        else:
            fail_count += 1
            pred_categories.append(None)
            display_names.append("Failed / Empty")
            top_probs.append(0.0)
            latencies.append(0.0)
            urgencies.append("STANDARD")
            departments.append("Unassigned")
            sla_windows.append("---")
            for cat in LABEL_DISPLAY_NAMES:
                prob_cols[cat].append(0.0)

    enriched_df["request_id"] = request_ids
    enriched_df["predicted_category"] = pred_categories
    enriched_df["predicted_category_name"] = display_names
    enriched_df["risk_urgency"] = urgencies
    enriched_df["assigned_department"] = departments
    enriched_df["resolution_sla"] = sla_windows
    enriched_df["top_probability"] = top_probs
    enriched_df["inference_duration_ms"] = latencies

    for cat in LABEL_DISPLAY_NAMES:
        col_name = f"prob_{cat}"
        enriched_df[col_name] = prob_cols[cat]

    summary = {
        "total_rows": total,
        "successful_predictions": success_count,
        "failed_or_blank_rows": fail_count,
        "critical_count": critical_count,
        "avg_top_probability": (
            round(float(pd.Series(top_probs).mean()), 4) if success_count > 0 else 0.0
        ),
        "total_latency_ms": round(sum(latencies), 2),
    }

    return enriched_df, summary, None
