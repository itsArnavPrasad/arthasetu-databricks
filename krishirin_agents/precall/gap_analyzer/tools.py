import logging
from google.adk.tools.tool_context import ToolContext

logger = logging.getLogger(__name__)


def profile_validator(tool_context: ToolContext, farmer_context_json: str) -> dict:
    """Rule-based validation of farmer profile completeness and data consistency.

    Args:
        farmer_context_json: JSON string of the farmer_context from state.
            May be a flat object or nested under 'profile' key.
    """
    import json
    try:
        ctx = json.loads(farmer_context_json)
    except (json.JSONDecodeError, TypeError):
        return {"status": "error", "message": "Invalid farmer context JSON"}

    if not isinstance(ctx, dict):
        return {"status": "error", "message": "Expected dict for farmer context"}

    # Handle both flat format and nested {profile: {...}} format
    profile = ctx.get("profile", ctx) if isinstance(ctx, dict) else {}

    issues = []

    # --- Document completeness checks ---
    # Check data_completeness (set by OCR pipeline) OR documents_provided (legacy)
    data_completeness = profile.get("data_completeness") or ctx.get("data_completeness") or {}
    docs_provided = profile.get("documents_provided") or []

    # If data_completeness exists (OCR pipeline), use it
    if data_completeness:
        doc_map = {
            "aadhaar": "Aadhaar Card",
            "bank_statement": "Bank Statement",
            "land_record": "Land Record (7/12 extract)",
        }
        for doc_key, doc_name in doc_map.items():
            if not data_completeness.get(doc_key, False):
                issues.append({
                    "type": "warning",
                    "id": f"MISSING_{doc_key.upper()}",
                    "detail": f"{doc_name} not provided — recommended for stronger application",
                })
    elif docs_provided:
        # Legacy format: list of document type strings
        required_docs = ["aadhaar", "bank_statement", "land_record"]
        for doc in required_docs:
            if not any(doc.lower() in d.lower() for d in docs_provided):
                issues.append({
                    "type": "warning",
                    "id": f"MISSING_{doc.upper()}",
                    "detail": f"{doc.replace('_', ' ').title()} not provided",
                })

    # --- Bank history check ---
    bank = profile.get("bank_summary") or ctx.get("bank_summary") or {}
    months = bank.get("months_of_history") or bank.get("months_available") or 0
    if isinstance(months, (int, float)) and 0 < months < 6:
        issues.append({
            "type": "warning",
            "id": "SHORT_BANK_HISTORY",
            "detail": f"Bank statement covers {int(months)} months (6+ recommended for stronger score)",
        })

    # --- Aadhaar linkage ---
    aadhaar = profile.get("aadhaar_last4") or ctx.get("aadhaar_last4")
    if not aadhaar:
        issues.append({
            "type": "warning",
            "id": "AADHAAR_NOT_LINKED",
            "detail": "Aadhaar number not linked to profile",
        })

    # --- Income consistency ---
    stated_income = bank.get("avg_monthly_income", 0) or 0
    if stated_income > 0:
        bank_avg = bank.get("bank_avg_monthly_credit", 0) or 0
        if bank_avg > 0 and abs(stated_income - bank_avg) / bank_avg > 0.3:
            issues.append({
                "type": "warning",
                "id": "INCOME_MISMATCH",
                "detail": f"Stated income ₹{stated_income:,.0f} differs from bank average ₹{bank_avg:,.0f} by >30%",
            })

    # --- Existing defaults ---
    loans = profile.get("existing_loans") or ctx.get("existing_loans") or []
    for loan in loans:
        if isinstance(loan, dict) and loan.get("status", "").lower() in ("default", "npa", "overdue"):
            issues.append({
                "type": "critical",
                "id": "EXISTING_DEFAULT",
                "detail": f"Existing loan ({loan.get('type', 'unknown')}) in {loan.get('status')} status",
            })

    # --- DTI check ---
    if stated_income > 0:
        total_emi = sum(
            (loan.get("emi", 0) or 0) for loan in loans if isinstance(loan, dict)
        )
        dti = total_emi / stated_income if stated_income > 0 else 0
        if dti > 0.5:
            issues.append({
                "type": "critical",
                "id": "HIGH_DTI",
                "detail": f"DTI ratio {dti:.2f} exceeds 0.50 — EMI ₹{total_emi:,.0f} vs income ₹{stated_income:,.0f}",
            })

    # --- Land holding check ---
    land = profile.get("land_holding_acres") or ctx.get("land_holding_acres") or 0
    if isinstance(land, (int, float)) and land <= 0:
        issues.append({
            "type": "warning",
            "id": "NO_LAND_DATA",
            "detail": "Land holding information not available — upload land record for better assessment",
        })

    return {"status": "success", "issues": issues, "total_issues": len(issues)}
