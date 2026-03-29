import math
import logging
from google.adk.tools.tool_context import ToolContext

logger = logging.getLogger(__name__)


def interest_calculator(
    tool_context: ToolContext,
    amount: float,
    tenure_months: int,
    scheme: str = "KCC",
) -> dict:
    """Calculate loan interest, EMI, and total repayment based on scheme rules.

    Args:
        amount: Loan amount in INR
        tenure_months: Loan tenure in months
        scheme: Scheme type — KCC, MUDRA, TERM_LOAN
    """
    logger.info(f"Calculating interest for ₹{amount}, {tenure_months}mo, {scheme}")

    if scheme.upper() == "KCC":
        nominal_rate = 7.0
        # KCC subvention: 2% govt + 3% prompt repayment for ≤₹3L
        if amount <= 300000:
            govt_subvention = 2.0
            prompt_incentive = 3.0
            effective_rate = nominal_rate - govt_subvention - prompt_incentive  # 2%
        else:
            govt_subvention = 2.0
            prompt_incentive = 0.0
            effective_rate = nominal_rate - govt_subvention  # 5%
    elif scheme.upper() == "MUDRA":
        nominal_rate = 10.0
        effective_rate = 10.0
        govt_subvention = 0.0
        prompt_incentive = 0.0
    else:  # TERM_LOAN
        nominal_rate = 9.0
        effective_rate = 9.0
        govt_subvention = 0.0
        prompt_incentive = 0.0

    # Monthly EMI calculation (reducing balance)
    monthly_rate = effective_rate / 100 / 12
    if monthly_rate > 0:
        emi = amount * monthly_rate * math.pow(1 + monthly_rate, tenure_months) / (
            math.pow(1 + monthly_rate, tenure_months) - 1
        )
    else:
        emi = amount / tenure_months

    total_repayment = emi * tenure_months
    total_interest = total_repayment - amount

    return {
        "status": "success",
        "nominal_rate_pct": nominal_rate,
        "effective_rate_pct": effective_rate,
        "govt_subvention_pct": govt_subvention,
        "prompt_incentive_pct": prompt_incentive,
        "monthly_emi": round(emi, 2),
        "total_repayment": round(total_repayment, 2),
        "total_interest": round(total_interest, 2),
        "per_lakh_per_month": round((effective_rate / 100 / 12) * 100000, 2),
    }


def collateral_checker(
    tool_context: ToolContext,
    amount: float,
    land_acres: float,
    land_type: str = "owned",
) -> dict:
    """Check collateral requirements per RBI KCC guidelines.

    Args:
        amount: Loan amount in INR
        land_acres: Farmer's land holding in acres
        land_type: owned / leased / shared
    """
    logger.info(f"Checking collateral for ₹{amount}, {land_acres} acres {land_type}")

    # RBI KCC guidelines
    if amount <= 160000:
        requirement = "No collateral required (waived up to ₹1.6 lakh)"
        waiver = True
    elif amount <= 300000:
        requirement = "Hypothecation of crops only (no land mortgage for tied-up loans with crop insurance)"
        waiver = True
    else:
        requirement = f"Equitable mortgage of land required. Estimated land value: ₹{land_acres * 500000:,.0f} (approx ₹5L/acre)"
        waiver = False

    # Check if land type allows mortgage
    if land_type.lower() in ("leased", "shared") and not waiver:
        requirement += " WARNING: Leased/shared land may not be accepted for mortgage. Consider reducing loan amount to ₹3L or below."

    return {
        "status": "success",
        "collateral_required": not waiver,
        "requirement_detail": requirement,
        "waiver_applicable": waiver,
        "waiver_limit": 160000 if amount > 300000 else (300000 if amount > 160000 else amount),
        "land_value_estimate": land_acres * 500000,
    }
