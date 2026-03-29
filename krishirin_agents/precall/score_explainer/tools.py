"""
ML model tools for the score_explainer agent.

These tools read OCR-extracted bank/loan data directly from session state
(not from the LLM's text output) to avoid data loss from LLM truncation.
"""

import json
import logging
import os

import requests
from google.adk.tools.tool_context import ToolContext

from krishirin_agents.shared.feature_engineering import (
    compute_behavioral_features,
    compute_debt_features,
)

logger = logging.getLogger(__name__)

# Databricks serving endpoint config
DATABRICKS_INSTANCE = os.getenv(
    "DATABRICKS_SERVING_HOST",
    os.getenv("DATABRICKS_HOST", "dbc-0e37dbb2-9279.cloud.databricks.com"),
)
if DATABRICKS_INSTANCE.startswith("https://"):
    DATABRICKS_INSTANCE = DATABRICKS_INSTANCE[len("https://"):]
if DATABRICKS_INSTANCE.startswith("http://"):
    DATABRICKS_INSTANCE = DATABRICKS_INSTANCE[len("http://"):]

DATABRICKS_TOKEN = os.getenv("DATABRICKS_TOKEN", "")

BEHAVIORAL_ENDPOINT = "behavioral_classifier_rf"
DEFAULT_ENDPOINT = "default_predictor_xgboost"

BEHAVIORAL_COLS = [
    "total_transactions", "txn_frequency", "avg_transaction_amount",
    "monthly_inflow", "monthly_outflow", "inflow_outflow_ratio",
    "inflow_variance", "avg_balance", "min_balance", "max_balance",
    "balance_std", "small_credit_count", "large_debit_count",
    "credit_debit_time_gap", "consecutive_zero_balance_days", "cash_vs_upi_ratio",
]

DEFAULT_COLS = BEHAVIORAL_COLS + [
    "debt_to_income_ratio", "repayment_ratio", "missed_payment_count",
    "avg_days_past_due", "debt_growth_rate", "outstanding_to_balance_ratio",
    "total_loan_amount", "total_outstanding", "avg_interest_rate", "num_loans",
]


def _call_databricks_endpoint(endpoint_name: str, columns: list[str], features: dict) -> dict:
    """Call a Databricks Model Serving endpoint."""
    if not DATABRICKS_TOKEN:
        return {"status": "error", "error": "DATABRICKS_TOKEN not configured"}

    url = f"https://{DATABRICKS_INSTANCE}/serving-endpoints/{endpoint_name}/invocations"
    headers = {
        "Authorization": f"Bearer {DATABRICKS_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "dataframe_split": {
            "columns": columns,
            "data": [[features.get(c, 0) for c in columns]],
        }
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=90)
        resp.raise_for_status()
        return {"status": "success", "response": resp.json()}
    except requests.exceptions.RequestException as e:
        logger.error(f"Databricks endpoint {endpoint_name} error: {e}")
        return {"status": "error", "error": str(e)}


def _get_transactions_from_state(tool_context: ToolContext) -> list[dict]:
    """Extract raw transactions from session state (set by data_loader from OCR data)."""
    # Primary: read from ocr_farmer_data (set by server.py before pipeline starts)
    ocr_data = tool_context.state.get("ocr_farmer_data", {})
    if isinstance(ocr_data, dict):
        txns = ocr_data.get("_raw_transactions", [])
        if txns:
            logger.info(f"Found {len(txns)} transactions in ocr_farmer_data._raw_transactions")
            return txns

    # Fallback: check ocr_results directly
    ocr_results = tool_context.state.get("ocr_results", {})
    if isinstance(ocr_results, dict):
        bank = ocr_results.get("bank_statement", {})
        if isinstance(bank, list):
            # Multiple bank statements
            all_txns = []
            for b in bank:
                if isinstance(b, dict):
                    all_txns.extend(b.get("extracted_data", {}).get("transactions", []))
            if all_txns:
                logger.info(f"Found {len(all_txns)} transactions in ocr_results (multi)")
                return all_txns
        elif isinstance(bank, dict):
            txns = bank.get("extracted_data", {}).get("transactions", [])
            if txns:
                logger.info(f"Found {len(txns)} transactions in ocr_results")
                return txns

    logger.warning("No transactions found in session state")
    return []


def _get_loans_from_state(tool_context: ToolContext) -> list[dict]:
    """Extract raw loan data from session state."""
    ocr_data = tool_context.state.get("ocr_farmer_data", {})
    if isinstance(ocr_data, dict):
        raw = ocr_data.get("_raw_loan_data", [])
        if raw:
            return raw if isinstance(raw, list) else [raw]
        loans = ocr_data.get("existing_loans", [])
        if loans:
            return loans

    ocr_results = tool_context.state.get("ocr_results", {})
    if isinstance(ocr_results, dict):
        loan = ocr_results.get("loan_slip", {})
        if isinstance(loan, list):
            return [l.get("extracted_data", {}) for l in loan if isinstance(l, dict)]
        elif isinstance(loan, dict):
            data = loan.get("extracted_data", {})
            return [data] if data else []

    return []


def run_behavioral_classifier(tool_context: ToolContext) -> str:
    """Run the Random Forest behavioral classifier on the farmer's bank transactions.

    Reads transaction data directly from session state (OCR-extracted bank statement data).
    No arguments needed — data comes from the pipeline state automatically.

    Returns:
        JSON string with behavioral classification result and computed features.
    """
    transactions = _get_transactions_from_state(tool_context)

    if not transactions:
        return json.dumps({
            "status": "no_data",
            "error": "No bank transaction data available in session state",
            "classification": "unknown",
            "note": "Bank statement may not have been uploaded or OCR could not extract transactions.",
        })

    # Compute behavioral features
    features = compute_behavioral_features(transactions)
    logger.info(f"Behavioral features computed from {len(transactions)} transactions")

    # Call Databricks endpoint
    result = _call_databricks_endpoint(BEHAVIORAL_ENDPOINT, BEHAVIORAL_COLS, features)

    if result["status"] == "success":
        predictions = result["response"].get("predictions", [])
        classification = predictions[0] if predictions else "unknown"
        return json.dumps({
            "status": "success",
            "classification": classification,
            "features_computed": features,
            "data_points": len(transactions),
        })
    else:
        return json.dumps({
            "status": "endpoint_error",
            "error": result.get("error", "Unknown error"),
            "classification": "unknown",
            "features_computed": features,
            "note": "Databricks endpoint call failed but features were computed successfully.",
        })


def run_default_predictor(tool_context: ToolContext) -> str:
    """Run the XGBoost default predictor on the farmer's bank and loan data.

    Reads both transaction and loan data directly from session state.
    No arguments needed — data comes from the pipeline state automatically.

    Returns:
        JSON string with default probability, risk tier, and computed features.
    """
    transactions = _get_transactions_from_state(tool_context)
    loans = _get_loans_from_state(tool_context)

    # Compute features
    behavioral = compute_behavioral_features(transactions)
    debt = compute_debt_features(loans, behavioral.get("monthly_inflow", 0))

    all_features = {**behavioral, **debt}

    # Call Databricks endpoint
    result = _call_databricks_endpoint(DEFAULT_ENDPOINT, DEFAULT_COLS, all_features)

    if result["status"] == "success":
        predictions = result["response"].get("predictions", [])
        prob = predictions[0] if predictions else None

        if prob is not None:
            risk_tier = "low_risk" if prob < 0.3 else ("medium_risk" if prob < 0.6 else "high_risk")
        else:
            risk_tier = "unknown"

        return json.dumps({
            "status": "success",
            "default_probability": round(prob, 4) if prob is not None else None,
            "risk_tier": risk_tier,
            "behavioral_features": behavioral,
            "debt_features": debt,
            "has_loan_data": len(loans) > 0,
            "has_bank_data": len(transactions) > 0,
            "note": "" if loans else "No loan document uploaded. Scoring based on behavioral patterns only.",
        })
    else:
        return json.dumps({
            "status": "endpoint_error",
            "error": result.get("error", "Unknown error"),
            "default_probability": None,
            "risk_tier": "unknown",
            "behavioral_features": behavioral,
            "debt_features": debt,
            "note": "Databricks endpoint call failed but features were computed successfully.",
        })
