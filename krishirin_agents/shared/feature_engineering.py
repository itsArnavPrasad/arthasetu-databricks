"""
Feature engineering from OCR-extracted transaction and loan data.

Computes the 26 features needed for Databricks ML serving endpoints:
- 16 behavioral features (for Random Forest behavioral classifier)
- 10 debt features (added for XGBoost default predictor)

Logic mirrors example_transaction_loan_train.py, adapted for single-user
inference from OCR-extracted data (not batch training).
"""

import logging
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)


def compute_behavioral_features(transactions: list[dict]) -> dict:
    """Compute 16 behavioral features from OCR-extracted bank transactions.

    Args:
        transactions: List of dicts with keys: date, description, credit, debit, balance, channel_hint.
                      credit/debit are floats or None. balance is float.

    Returns:
        Dict of 16 features matching BEHAVIORAL_COLS in call_databricks_api.py.
    """
    if not transactions:
        logger.warning("No transactions provided for feature engineering")
        return _default_behavioral_features()

    # Parse and clean transactions
    parsed = []
    for t in transactions:
        try:
            credit = float(t.get("credit") or 0)
            debit = float(t.get("debit") or 0)
            balance = float(t.get("balance") or 0)
            channel = (t.get("channel_hint") or "other").lower()
            date_str = t.get("date", "")

            # Parse date
            dt = None
            for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"):
                try:
                    dt = datetime.strptime(date_str, fmt)
                    break
                except ValueError:
                    continue

            txn_type = "credit" if credit > 0 else "debit"
            amount = credit if credit > 0 else debit

            parsed.append({
                "date": dt,
                "amount": amount,
                "balance": balance,
                "txn_type": txn_type,
                "channel": channel,
                "credit": credit,
                "debit": debit,
            })
        except (ValueError, TypeError) as e:
            logger.debug(f"Skipping unparseable transaction: {e}")
            continue

    if not parsed:
        return _default_behavioral_features()

    # Sort by date
    parsed.sort(key=lambda x: x["date"] or datetime.min)

    # --- Basic aggregates ---
    total_transactions = len(parsed)
    amounts = [t["amount"] for t in parsed]
    balances = [t["balance"] for t in parsed]
    avg_transaction_amount = sum(amounts) / total_transactions if total_transactions else 0

    avg_balance = sum(balances) / len(balances) if balances else 0
    min_balance = min(balances) if balances else 0
    max_balance = max(balances) if balances else 0

    # Balance std
    if len(balances) > 1:
        mean_bal = avg_balance
        balance_std = (sum((b - mean_bal) ** 2 for b in balances) / (len(balances) - 1)) ** 0.5
    else:
        balance_std = 0

    # --- Monthly aggregates ---
    monthly_credits = defaultdict(float)
    monthly_debits = defaultdict(float)
    monthly_txn_counts = defaultdict(int)

    for t in parsed:
        if t["date"]:
            ym = t["date"].strftime("%Y-%m")
            if t["txn_type"] == "credit":
                monthly_credits[ym] += t["amount"]
            else:
                monthly_debits[ym] += t["amount"]
            monthly_txn_counts[ym] += 1

    months_present = set(monthly_credits.keys()) | set(monthly_debits.keys())
    num_months = max(len(months_present), 1)

    monthly_inflow = sum(monthly_credits.values()) / num_months
    monthly_outflow = sum(monthly_debits.values()) / num_months
    inflow_outflow_ratio = monthly_inflow / max(monthly_outflow, 1)

    # Inflow variance
    inflows = list(monthly_credits.values())
    if len(inflows) > 1:
        mean_inflow = sum(inflows) / len(inflows)
        inflow_variance = sum((x - mean_inflow) ** 2 for x in inflows) / (len(inflows) - 1)
    else:
        inflow_variance = 0

    txn_frequency = sum(monthly_txn_counts.values()) / num_months

    # --- Conditional features ---
    credits = [t for t in parsed if t["txn_type"] == "credit"]
    debits = [t for t in parsed if t["txn_type"] == "debit"]

    small_credit_count = sum(1 for t in credits if t["amount"] < 5000)
    large_debit_count = sum(1 for t in debits if t["amount"] > 10000)

    # Cash vs UPI ratio
    cash_count = sum(1 for t in parsed if t["channel"] in ("cash", "atm"))
    upi_count = sum(1 for t in parsed if "upi" in t["channel"])
    cash_vs_upi_ratio = cash_count / max(upi_count, 1)

    # --- Credit-debit time gap ---
    credit_debit_gaps = []
    last_credit_time = None
    for t in parsed:
        if t["txn_type"] == "credit" and t["date"]:
            last_credit_time = t["date"]
        elif t["txn_type"] == "debit" and t["date"] and last_credit_time:
            gap_hrs = (t["date"] - last_credit_time).total_seconds() / 3600.0
            if gap_hrs >= 0:
                credit_debit_gaps.append(gap_hrs)
    credit_debit_time_gap = sum(credit_debit_gaps) / len(credit_debit_gaps) if credit_debit_gaps else 0

    # --- Consecutive zero/low balance days ---
    consecutive_zero_balance_days = 0
    if len(balances) > 1:
        current_streak = 0
        max_streak = 0
        for b in balances:
            if b < 1000:
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 0
        consecutive_zero_balance_days = max_streak

    return {
        "total_transactions": total_transactions,
        "txn_frequency": round(txn_frequency, 2),
        "avg_transaction_amount": round(avg_transaction_amount, 2),
        "monthly_inflow": round(monthly_inflow, 2),
        "monthly_outflow": round(monthly_outflow, 2),
        "inflow_outflow_ratio": round(inflow_outflow_ratio, 2),
        "inflow_variance": round(inflow_variance, 2),
        "avg_balance": round(avg_balance, 2),
        "min_balance": round(min_balance, 2),
        "max_balance": round(max_balance, 2),
        "balance_std": round(balance_std, 2),
        "small_credit_count": small_credit_count,
        "large_debit_count": large_debit_count,
        "credit_debit_time_gap": round(credit_debit_time_gap, 2),
        "consecutive_zero_balance_days": consecutive_zero_balance_days,
        "cash_vs_upi_ratio": round(cash_vs_upi_ratio, 3),
    }


def compute_debt_features(loans: list[dict], monthly_inflow: float) -> dict:
    """Compute 10 debt features from OCR-extracted loan data.

    Args:
        loans: List of loan dicts with keys: loan_amount, amount_repaid, outstanding_amount,
               interest_rate, emi_amount, tenure_months, status.
               Missing fields default to sensible values.
        monthly_inflow: Average monthly income (from behavioral features).

    Returns:
        Dict of 10 features matching DEFAULT_COLS debt portion in call_databricks_api.py.
    """
    if not loans:
        return _default_debt_features()

    total_loan_amount = 0
    total_amount_repaid = 0
    total_outstanding = 0
    missed_payment_count = 0
    days_past_due_list = []
    interest_rates = []
    num_loans = len(loans)

    for loan in loans:
        amount = float(loan.get("loan_amount") or loan.get("amount") or 0)
        repaid = float(loan.get("amount_repaid") or 0)
        outstanding = float(loan.get("outstanding_amount") or loan.get("outstanding") or 0)
        rate = float(loan.get("interest_rate") or 0)

        # If outstanding not provided, estimate from amount - repaid
        if outstanding == 0 and amount > 0 and repaid > 0:
            outstanding = max(amount - repaid, 0)

        # If repaid not provided, estimate from amount - outstanding
        if repaid == 0 and amount > 0 and outstanding > 0:
            repaid = max(amount - outstanding, 0)

        total_loan_amount += amount
        total_amount_repaid += repaid
        total_outstanding += outstanding
        if rate > 0:
            interest_rates.append(rate)

        # Missed payments: infer from status
        status = (loan.get("status") or "active").lower()
        if status in ("overdue", "defaulted", "npa"):
            missed_payment_count += 2  # conservative estimate
            days_past_due_list.append(30)  # conservative estimate
        else:
            missed_payment_count += int(loan.get("missed_payments", 0))
            days_past_due_list.append(float(loan.get("days_past_due", 0)))

    avg_days_past_due = sum(days_past_due_list) / len(days_past_due_list) if days_past_due_list else 0
    avg_interest_rate = sum(interest_rates) / len(interest_rates) if interest_rates else 0

    # Derived features
    debt_to_income_ratio = (total_loan_amount / max(monthly_inflow, 1)) / 12
    repayment_ratio = total_amount_repaid / max(total_loan_amount, 1)

    avg_balance = monthly_inflow * 0.3  # rough proxy if not provided separately
    outstanding_to_balance_ratio = total_outstanding / max(avg_balance, 1)

    net_owed = total_loan_amount - total_amount_repaid
    debt_growth_rate = (total_outstanding - net_owed) / max(abs(net_owed), 1)

    return {
        "debt_to_income_ratio": round(debt_to_income_ratio, 2),
        "repayment_ratio": round(repayment_ratio, 2),
        "missed_payment_count": missed_payment_count,
        "avg_days_past_due": round(avg_days_past_due, 2),
        "debt_growth_rate": round(debt_growth_rate, 2),
        "outstanding_to_balance_ratio": round(outstanding_to_balance_ratio, 2),
        "total_loan_amount": round(total_loan_amount, 2),
        "total_outstanding": round(total_outstanding, 2),
        "avg_interest_rate": round(avg_interest_rate, 2),
        "num_loans": num_loans,
    }


def _default_behavioral_features() -> dict:
    """Return zeroed behavioral features when no transaction data is available."""
    return {
        "total_transactions": 0,
        "txn_frequency": 0,
        "avg_transaction_amount": 0,
        "monthly_inflow": 0,
        "monthly_outflow": 0,
        "inflow_outflow_ratio": 0,
        "inflow_variance": 0,
        "avg_balance": 0,
        "min_balance": 0,
        "max_balance": 0,
        "balance_std": 0,
        "small_credit_count": 0,
        "large_debit_count": 0,
        "credit_debit_time_gap": 0,
        "consecutive_zero_balance_days": 0,
        "cash_vs_upi_ratio": 0,
    }


def _default_debt_features() -> dict:
    """Return zeroed debt features when no loan data is available."""
    return {
        "debt_to_income_ratio": 0,
        "repayment_ratio": 0,
        "missed_payment_count": 0,
        "avg_days_past_due": 0,
        "debt_growth_rate": 0,
        "outstanding_to_balance_ratio": 0,
        "total_loan_amount": 0,
        "total_outstanding": 0,
        "avg_interest_rate": 0,
        "num_loans": 0,
    }
