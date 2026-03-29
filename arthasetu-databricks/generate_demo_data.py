"""
Generate fake bank statement and loan slip PDFs for demo user Roshan Pandey,
then extract engineered features and call Databricks model endpoints.
"""

import csv
import json
import os
import random
import statistics
from collections import defaultdict
from datetime import datetime, timedelta
from io import BytesIO

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
import seaborn as sns

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm, inch
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
)

# ─── Configuration ───────────────────────────────────────────────────────────

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output", "demo_roshan")
os.makedirs(OUTPUT_DIR, exist_ok=True)

ACCOUNT_HOLDER = "Roshan Pandey"
ACCOUNT_NUMBER = "3201 4587 6923"
IFSC = "SBIN0012345"
BRANCH = "SBI Varanasi Rural Branch"
BANK_NAME = "State Bank of India"
STATEMENT_PERIOD = ("2023-07-01", "2024-01-01")

random.seed(42)

# ─── Generate realistic transaction data ─────────────────────────────────────

def generate_transactions():
    """Generate ~70 transactions over 6 months for a stable farmer."""
    transactions = []
    start = datetime(2023, 7, 1)
    balance = 26500.0  # opening balance

    # Monthly patterns for a stable farmer:
    # - 1-2 large credits per month (FCI/mandi sale, 15k-45k)
    # - 10-15 small debits per month (daily expenses)
    # - Occasional cash transactions

    descriptions_debit = [
        ("Groceries", "UPI"), ("Mobile Recharge", "UPI"), ("Electricity Bill", "UPI"),
        ("Pharmacy", "UPI"), ("Dairy Milk", "UPI"), ("Local Store", "UPI"),
        ("Fertilizer Purchase", "cash"), ("Seed Purchase", "cash"),
        ("Tractor Rental", "UPI"), ("Veterinary Services", "cash"),
        ("School Fees", "bank transfer"), ("Irrigation Pump Fuel", "cash"),
    ]

    descriptions_credit = [
        ("Agricultural Produce Sale", "bank transfer"),
        ("FCI Payment", "bank transfer"),
        ("Mandi Receipt", "bank transfer"),
        ("PM-KISAN Installment", "bank transfer"),
        ("Dairy Cooperative Payment", "UPI"),
    ]

    for month_offset in range(6):
        month_start = start + timedelta(days=month_offset * 30)

        # 1-2 large credits per month
        num_credits = random.choice([1, 2])
        for _ in range(num_credits):
            day_offset = random.randint(1, 28)
            txn_date = month_start + timedelta(days=day_offset)
            desc, channel = random.choice(descriptions_credit)
            amount = round(random.uniform(15000, 45000), 2)
            balance = round(balance + amount, 2)
            transactions.append({
                "date": txn_date,
                "type": "credit",
                "amount": amount,
                "balance": balance,
                "description": desc,
                "channel": channel,
            })

        # 10-14 small debits per month
        num_debits = random.randint(10, 14)
        for _ in range(num_debits):
            day_offset = random.randint(0, 29)
            txn_date = month_start + timedelta(days=day_offset)
            desc, channel = random.choice(descriptions_debit)
            if desc in ("Tractor Rental",):
                amount = round(random.uniform(3000, 8000), 2)
            elif desc in ("School Fees",):
                amount = round(random.uniform(2000, 5000), 2)
            elif desc in ("Fertilizer Purchase", "Seed Purchase"):
                amount = round(random.uniform(1500, 6000), 2)
            else:
                amount = round(random.uniform(100, 900), 2)
            balance = round(balance - amount, 2)
            if balance < 500:
                balance = round(balance + random.uniform(5000, 10000), 2)
            transactions.append({
                "date": txn_date,
                "type": "debit",
                "amount": amount,
                "balance": balance,
                "description": desc,
                "channel": channel,
            })

    transactions.sort(key=lambda t: t["date"])
    return transactions


# ─── Generate loan data ──────────────────────────────────────────────────────

def generate_loans():
    """Generate 2 loans for Roshan — one mostly repaid, one active."""
    return [
        {
            "loan_id": "RP_L01",
            "loan_amount": 50000,
            "loan_start_date": "2023-06-15",
            "loan_due_date": "2024-01-15",
            "interest_rate": 11.5,
            "repayment_type": "seasonal",
            "amount_repaid": 42000.0,
            "outstanding_amount": 10875.0,  # includes interest
            "missed_payments": 0,
            "days_past_due": 0,
            "default_flag": 0,
            "purpose": "Kharif crop input purchase (seeds, fertilizer)",
        },
        {
            "loan_id": "RP_L02",
            "loan_amount": 75000,
            "loan_start_date": "2023-09-01",
            "loan_due_date": "2024-06-01",
            "interest_rate": 12.75,
            "repayment_type": "EMI",
            "amount_repaid": 18000.0,
            "outstanding_amount": 62568.75,
            "missed_payments": 1,
            "days_past_due": 8,
            "default_flag": 0,
            "purpose": "Irrigation pump and drip system installation",
        },
    ]


# ─── PDF: Bank Statement ─────────────────────────────────────────────────────

def create_bank_statement_pdf(transactions, filepath):
    """Create a realistic Indian bank statement PDF."""
    doc = SimpleDocTemplate(filepath, pagesize=A4,
                            leftMargin=15*mm, rightMargin=15*mm,
                            topMargin=20*mm, bottomMargin=15*mm)
    styles = getSampleStyleSheet()
    elements = []

    # Header
    header_style = ParagraphStyle("Header", parent=styles["Title"],
                                  fontSize=16, textColor=colors.HexColor("#1a237e"))
    sub_style = ParagraphStyle("Sub", parent=styles["Normal"],
                               fontSize=10, textColor=colors.grey)
    bold_style = ParagraphStyle("Bold", parent=styles["Normal"],
                                fontSize=10, fontName="Helvetica-Bold")

    elements.append(Paragraph(BANK_NAME, header_style))
    elements.append(Paragraph(BRANCH, sub_style))
    elements.append(Spacer(1, 4*mm))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#1a237e")))
    elements.append(Spacer(1, 4*mm))

    # Account info
    info_data = [
        ["Account Holder:", ACCOUNT_HOLDER, "Account No:", ACCOUNT_NUMBER],
        ["Branch:", BRANCH, "IFSC:", IFSC],
        ["Statement Period:", f"{STATEMENT_PERIOD[0]} to {STATEMENT_PERIOD[1]}", "Currency:", "INR"],
    ]
    info_table = Table(info_data, colWidths=[90, 150, 80, 150])
    info_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 6*mm))
    elements.append(Paragraph("Transaction Statement", bold_style))
    elements.append(Spacer(1, 3*mm))

    # Transaction table
    header_row = ["Date", "Description", "Channel", "Debit (₹)", "Credit (₹)", "Balance (₹)"]
    table_data = [header_row]

    for txn in transactions:
        debit = f"{txn['amount']:,.2f}" if txn["type"] == "debit" else ""
        credit = f"{txn['amount']:,.2f}" if txn["type"] == "credit" else ""
        table_data.append([
            txn["date"].strftime("%Y-%m-%d"),
            txn["description"],
            txn["channel"],
            debit,
            credit,
            f"{txn['balance']:,.2f}",
        ])

    txn_table = Table(table_data, colWidths=[65, 130, 65, 65, 65, 75])
    txn_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a237e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 7.5),
        ("ALIGN", (3, 0), (5, -1), "RIGHT"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f5f5")]),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
    ]))
    elements.append(txn_table)

    # Summary
    elements.append(Spacer(1, 6*mm))
    total_credits = sum(t["amount"] for t in transactions if t["type"] == "credit")
    total_debits = sum(t["amount"] for t in transactions if t["type"] == "debit")
    closing_balance = transactions[-1]["balance"]

    summary_data = [
        ["Total Credits:", f"₹{total_credits:,.2f}",
         "Total Debits:", f"₹{total_debits:,.2f}"],
        ["Closing Balance:", f"₹{closing_balance:,.2f}", "", ""],
    ]
    summary_table = Table(summary_data, colWidths=[100, 120, 100, 120])
    summary_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 10*mm))
    elements.append(Paragraph(
        "This is a computer-generated statement and does not require a signature.",
        ParagraphStyle("Disclaimer", parent=styles["Normal"], fontSize=7, textColor=colors.grey)
    ))

    doc.build(elements)
    print(f"Bank statement saved: {filepath}")


# ─── PDF: Loan Slip ──────────────────────────────────────────────────────────

def create_loan_slip_pdf(loans, filepath):
    """Create a realistic loan summary / sanction slip PDF."""
    doc = SimpleDocTemplate(filepath, pagesize=A4,
                            leftMargin=15*mm, rightMargin=15*mm,
                            topMargin=20*mm, bottomMargin=15*mm)
    styles = getSampleStyleSheet()
    elements = []

    header_style = ParagraphStyle("Header", parent=styles["Title"],
                                  fontSize=16, textColor=colors.HexColor("#1a237e"))
    sub_style = ParagraphStyle("Sub", parent=styles["Normal"],
                               fontSize=10, textColor=colors.grey)
    bold_style = ParagraphStyle("Bold", parent=styles["Normal"],
                                fontSize=10, fontName="Helvetica-Bold")
    normal_style = ParagraphStyle("NormalCustom", parent=styles["Normal"], fontSize=9)

    elements.append(Paragraph(BANK_NAME, header_style))
    elements.append(Paragraph("Kisan Credit Card / Agricultural Loan Division", sub_style))
    elements.append(Spacer(1, 4*mm))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#1a237e")))
    elements.append(Spacer(1, 4*mm))

    elements.append(Paragraph("LOAN SUMMARY STATEMENT", bold_style))
    elements.append(Spacer(1, 3*mm))

    # Borrower info
    borrower_data = [
        ["Borrower Name:", ACCOUNT_HOLDER, "Account No:", ACCOUNT_NUMBER],
        ["Branch:", BRANCH, "IFSC:", IFSC],
        ["Address:", "Village Rampur, Block Chiraigaon, Varanasi, UP 221104", "", ""],
        ["Occupation:", "Farmer (Marginal - 2.5 acres)", "Crop:", "Rice, Wheat, Vegetables"],
    ]
    b_table = Table(borrower_data, colWidths=[95, 170, 70, 135])
    b_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(b_table)
    elements.append(Spacer(1, 6*mm))

    for i, loan in enumerate(loans):
        elements.append(Paragraph(f"Loan {i+1}: {loan['loan_id']}", bold_style))
        elements.append(Spacer(1, 2*mm))

        loan_data = [
            ["Loan ID", "Amount (₹)", "Start Date", "Due Date", "Interest Rate",
             "Repayment Type", "Purpose"],
            [loan["loan_id"], f"{loan['loan_amount']:,}", loan["loan_start_date"],
             loan["loan_due_date"], f"{loan['interest_rate']}%", loan["repayment_type"],
             loan["purpose"]],
        ]
        l_table = Table(loan_data, colWidths=[50, 60, 65, 65, 55, 65, 110])
        l_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8eaf6")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 7.5),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
        ]))
        elements.append(l_table)
        elements.append(Spacer(1, 2*mm))

        repay_data = [
            ["Amount Repaid (₹)", "Outstanding (₹)", "Missed Payments", "Days Past Due", "Default"],
            [f"{loan['amount_repaid']:,.2f}", f"{loan['outstanding_amount']:,.2f}",
             str(loan["missed_payments"]), str(loan["days_past_due"]),
             "No" if loan["default_flag"] == 0 else "Yes"],
        ]
        r_table = Table(repay_data, colWidths=[95, 95, 85, 85, 60])
        r_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8eaf6")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
        ]))
        elements.append(r_table)
        elements.append(Spacer(1, 6*mm))

    # Totals
    total_loan = sum(l["loan_amount"] for l in loans)
    total_repaid = sum(l["amount_repaid"] for l in loans)
    total_outstanding = sum(l["outstanding_amount"] for l in loans)

    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey))
    elements.append(Spacer(1, 3*mm))
    totals_data = [
        ["Total Loan Amount:", f"₹{total_loan:,}",
         "Total Repaid:", f"₹{total_repaid:,.2f}"],
        ["Total Outstanding:", f"₹{total_outstanding:,.2f}",
         "Number of Loans:", str(len(loans))],
    ]
    t_table = Table(totals_data, colWidths=[110, 110, 110, 110])
    t_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
    ]))
    elements.append(t_table)

    elements.append(Spacer(1, 10*mm))
    elements.append(Paragraph(
        "This is a system-generated loan summary. For disputes, contact your branch manager.",
        ParagraphStyle("Disclaimer", parent=styles["Normal"], fontSize=7, textColor=colors.grey)
    ))

    doc.build(elements)
    print(f"Loan slip saved: {filepath}")


# ─── Feature Engineering ─────────────────────────────────────────────────────

def compute_behavioral_features(transactions):
    """Compute the 16 behavioral features from raw transactions."""
    total_transactions = len(transactions)
    amounts = [t["amount"] for t in transactions]
    balances = [t["balance"] for t in transactions]

    avg_transaction_amount = statistics.mean(amounts)
    avg_balance = statistics.mean(balances)
    min_balance = min(balances)
    max_balance = max(balances)
    balance_std = statistics.stdev(balances) if len(balances) > 1 else 0.0

    # Monthly aggregations
    monthly_inflows = defaultdict(float)
    monthly_outflows = defaultdict(float)
    monthly_txn_counts = defaultdict(int)

    for t in transactions:
        month_key = t["date"].strftime("%Y-%m")
        monthly_txn_counts[month_key] += 1
        if t["type"] == "credit":
            monthly_inflows[month_key] += t["amount"]
        else:
            monthly_outflows[month_key] += t["amount"]

    num_months = len(set(monthly_txn_counts.keys()))
    monthly_inflow = statistics.mean(monthly_inflows.values()) if monthly_inflows else 0
    monthly_outflow = statistics.mean(monthly_outflows.values()) if monthly_outflows else 0
    inflow_variance = statistics.variance(monthly_inflows.values()) if len(monthly_inflows) > 1 else 0
    txn_frequency = total_transactions / max(num_months, 1)
    inflow_outflow_ratio = monthly_inflow / monthly_outflow if monthly_outflow > 0 else 0

    # Conditional counts
    small_credit_count = sum(1 for t in transactions if t["type"] == "credit" and t["amount"] < 5000)
    large_debit_count = sum(1 for t in transactions if t["type"] == "debit" and t["amount"] > 10000)

    # Channel ratio
    cash_count = sum(1 for t in transactions if t["channel"] == "cash")
    upi_count = sum(1 for t in transactions if t["channel"] == "UPI")
    cash_vs_upi_ratio = cash_count / upi_count if upi_count > 0 else 0

    # Time gaps: for each debit, compute hours since last credit (forward-fill approach)
    # This matches the training code exactly
    sorted_txns = sorted(transactions, key=lambda t: t["date"])
    last_credit_time = None
    gaps = []
    for t in sorted_txns:
        if t["type"] == "credit":
            last_credit_time = t["date"]
        elif t["type"] == "debit" and last_credit_time is not None:
            gap_hours = (t["date"] - last_credit_time).total_seconds() / 3600.0
            gaps.append(gap_hours)
    credit_debit_time_gap = statistics.mean(gaps) if gaps else 0

    # Consecutive zero balance days (balance < 1000)
    sorted_txns = sorted(transactions, key=lambda t: t["date"])
    max_zero_days = 0
    current_streak = 0
    prev_date = None
    for t in sorted_txns:
        if t["balance"] < 1000:
            if prev_date:
                current_streak += (t["date"] - prev_date).days
            else:
                current_streak = 1
            max_zero_days = max(max_zero_days, current_streak)
        else:
            current_streak = 0
            prev_date = None
            continue
        prev_date = t["date"]

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
        "consecutive_zero_balance_days": max_zero_days,
        "cash_vs_upi_ratio": round(cash_vs_upi_ratio, 3),
    }


def compute_debt_features(loans, monthly_inflow):
    """Compute the 10 debt features from loan data."""
    total_loan_amount = sum(l["loan_amount"] for l in loans)
    total_amount_repaid = sum(l["amount_repaid"] for l in loans)
    total_outstanding = sum(l["outstanding_amount"] for l in loans)
    missed_payment_count = sum(l["missed_payments"] for l in loans)
    avg_days_past_due = statistics.mean([l["days_past_due"] for l in loans])
    avg_interest_rate = statistics.mean([l["interest_rate"] for l in loans])
    num_loans = len(loans)

    # Derived ratios
    annual_income = monthly_inflow * 12
    debt_to_income_ratio = total_loan_amount / annual_income if annual_income > 0 else 0
    repayment_ratio = total_amount_repaid / total_loan_amount if total_loan_amount > 0 else 0

    # Need avg_balance for outstanding_to_balance_ratio — will be passed separately
    # For now compute what we can
    expected_outstanding = total_loan_amount - total_amount_repaid
    debt_growth_rate = ((total_outstanding - expected_outstanding) / expected_outstanding
                        if expected_outstanding > 0 else 0)

    return {
        "debt_to_income_ratio": round(debt_to_income_ratio, 2),
        "repayment_ratio": round(repayment_ratio, 2),
        "missed_payment_count": missed_payment_count,
        "avg_days_past_due": round(avg_days_past_due, 2),
        "debt_growth_rate": round(debt_growth_rate, 2),
        "total_loan_amount": total_loan_amount,
        "total_outstanding": round(total_outstanding, 2),
        "avg_interest_rate": round(avg_interest_rate, 2),
        "num_loans": num_loans,
    }


def call_databricks_endpoints(features):
    """Call both Databricks model serving endpoints and return predictions."""
    import requests

    DATABRICKS_INSTANCE = "dbc-0e37dbb2-9279.cloud.databricks.com"
    DATABRICKS_TOKEN = "<YOUR_DATABRICKS_TOKEN>"

    behavioral_features = {k: features[k] for k in [
        "total_transactions", "txn_frequency", "avg_transaction_amount",
        "monthly_inflow", "monthly_outflow", "inflow_outflow_ratio",
        "inflow_variance", "avg_balance", "min_balance", "max_balance",
        "balance_std", "small_credit_count", "large_debit_count",
        "credit_debit_time_gap", "consecutive_zero_balance_days", "cash_vs_upi_ratio",
    ]}

    all_features = {k: features[k] for k in [
        "total_transactions", "txn_frequency", "avg_transaction_amount",
        "monthly_inflow", "monthly_outflow", "inflow_outflow_ratio",
        "inflow_variance", "avg_balance", "min_balance", "max_balance",
        "balance_std", "small_credit_count", "large_debit_count",
        "credit_debit_time_gap", "consecutive_zero_balance_days", "cash_vs_upi_ratio",
        "debt_to_income_ratio", "repayment_ratio", "missed_payment_count",
        "avg_days_past_due", "debt_growth_rate", "outstanding_to_balance_ratio",
        "total_loan_amount", "total_outstanding", "avg_interest_rate", "num_loans",
    ]}

    headers = {
        "Authorization": f"Bearer {DATABRICKS_TOKEN}",
        "Content-Type": "application/json",
    }

    results = {}

    # 1) Behavioral classifier
    print("\n--- Calling Behavioral Classifier (Random Forest) ---")
    try:
        resp = requests.post(
            f"https://{DATABRICKS_INSTANCE}/serving-endpoints/behavioral_classifier_rf/invocations",
            headers=headers,
            json={"dataframe_records": [behavioral_features]},
            timeout=90,
        )
        resp.raise_for_status()
        results["behavioral_class"] = resp.json()["predictions"][0]
        print(f"  Classification: {results['behavioral_class']}")
    except Exception as e:
        print(f"  Error: {e}")
        results["behavioral_class"] = "ERROR"

    # 2) Default predictor
    print("\n--- Calling Default Predictor (XGBoost) ---")
    try:
        resp = requests.post(
            f"https://{DATABRICKS_INSTANCE}/serving-endpoints/default_predictor_xgboost/invocations",
            headers=headers,
            json={"dataframe_records": [all_features]},
            timeout=90,
        )
        resp.raise_for_status()
        prob = resp.json()["predictions"][0]
        results["default_probability"] = prob
        if prob < 0.3:
            results["risk_tier"] = "low_risk"
        elif prob < 0.6:
            results["risk_tier"] = "medium_risk"
        else:
            results["risk_tier"] = "high_risk"
        print(f"  Default Probability: {prob:.4f}")
        print(f"  Risk Tier: {results['risk_tier']}")
    except Exception as e:
        print(f"  Error: {e}")
        results["default_probability"] = "ERROR"
        results["risk_tier"] = "ERROR"

    return results


# ─── Save raw data as CSV (for reference) ────────────────────────────────────

def save_transactions_csv(transactions, filepath):
    with open(filepath, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "user_id", "date", "transaction_type", "amount", "balance",
            "description", "channel"
        ])
        writer.writeheader()
        for t in transactions:
            writer.writerow({
                "user_id": "ROSHAN01",
                "date": t["date"].strftime("%Y-%m-%d %H:%M:%S"),
                "transaction_type": t["type"],
                "amount": t["amount"],
                "balance": t["balance"],
                "description": t["description"],
                "channel": t["channel"],
            })
    print(f"Transactions CSV saved: {filepath}")


def save_loans_csv(loans, filepath):
    with open(filepath, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "user_id", "loan_id", "loan_amount", "loan_start_date", "loan_due_date",
            "interest_rate", "repayment_type", "amount_repaid", "outstanding_amount",
            "missed_payments", "days_past_due", "default_flag"
        ])
        writer.writeheader()
        for l in loans:
            writer.writerow({
                "user_id": "ROSHAN01",
                "loan_id": l["loan_id"],
                "loan_amount": l["loan_amount"],
                "loan_start_date": l["loan_start_date"],
                "loan_due_date": l["loan_due_date"],
                "interest_rate": l["interest_rate"],
                "repayment_type": l["repayment_type"],
                "amount_repaid": l["amount_repaid"],
                "outstanding_amount": l["outstanding_amount"],
                "missed_payments": l["missed_payments"],
                "days_past_due": l["days_past_due"],
                "default_flag": l["default_flag"],
            })
    print(f"Loans CSV saved: {filepath}")


# ─── Per-User Diagnostic Visualization ────────────────────────────────────────

# Population means and stds computed from training data (1000 users)
# These let us compute z-scores without re-reading all training CSVs each run.
POP_STATS = {
    "total_transactions":          {"mean": 77.8,  "std": 24.5},
    "txn_frequency":               {"mean": 12.9,  "std": 3.2},
    "avg_transaction_amount":      {"mean": 3200,  "std": 1800},
    "monthly_inflow":              {"mean": 25000, "std": 14000},
    "monthly_outflow":             {"mean": 12000, "std": 7000},
    "inflow_outflow_ratio":        {"mean": 2.1,   "std": 1.2},
    "inflow_variance":             {"mean": 2e8,   "std": 3e8},
    "avg_balance":                 {"mean": 55000, "std": 40000},
    "min_balance":                 {"mean": 8000,  "std": 12000},
    "max_balance":                 {"mean": 110000,"std": 60000},
    "balance_std":                 {"mean": 30000, "std": 18000},
    "small_credit_count":          {"mean": 2.5,   "std": 4.0},
    "large_debit_count":           {"mean": 1.0,   "std": 2.5},
    "credit_debit_time_gap":       {"mean": 300,   "std": 180},
    "consecutive_zero_balance_days":{"mean": 3,    "std": 8},
    "cash_vs_upi_ratio":           {"mean": 0.3,   "std": 0.6},
    "debt_to_income_ratio":        {"mean": 0.6,   "std": 0.8},
    "repayment_ratio":             {"mean": 0.45,  "std": 0.3},
    "missed_payment_count":        {"mean": 2.5,   "std": 3.0},
    "avg_days_past_due":           {"mean": 12,    "std": 15},
    "debt_growth_rate":            {"mean": 0.15,  "std": 0.2},
    "outstanding_to_balance_ratio":{"mean": 1.5,   "std": 1.8},
    "total_loan_amount":           {"mean": 100000,"std": 60000},
    "total_outstanding":           {"mean": 70000, "std": 55000},
    "avg_interest_rate":           {"mean": 13.5,  "std": 2.5},
    "num_loans":                   {"mean": 2.0,   "std": 0.8},
}

# Feature importance weights from the XGBoost default predictor
FEATURE_IMPORTANCE = {
    "credit_debit_time_gap": 0.2805,
    "missed_payment_count": 0.0713,
    "debt_to_income_ratio": 0.0542,
    "num_loans": 0.0369,
    "small_credit_count": 0.0341,
    "cash_vs_upi_ratio": 0.0330,
    "avg_days_past_due": 0.0310,
    "balance_std": 0.0295,
    "inflow_variance": 0.0280,
    "outstanding_to_balance_ratio": 0.0270,
    "repayment_ratio": 0.0260,
    "total_outstanding": 0.0250,
    "monthly_inflow": 0.0240,
    "avg_balance": 0.0230,
    "max_balance": 0.0220,
    "debt_growth_rate": 0.0210,
    "total_loan_amount": 0.0200,
    "avg_interest_rate": 0.0190,
    "inflow_outflow_ratio": 0.0180,
    "monthly_outflow": 0.0170,
    "min_balance": 0.0160,
    "total_transactions": 0.0150,
    "txn_frequency": 0.0140,
    "avg_transaction_amount": 0.0130,
    "large_debit_count": 0.0120,
    "consecutive_zero_balance_days": 0.0110,
    "electricity_bill": 0.0100,
}


def create_diagnostic_visualization(transactions, features, predictions, user_id, name, filepath):
    """Create a per-user diagnostic visualization matching the visualizer.py style."""
    sns.set_theme(style="whitegrid", rc={"axes.facecolor": "#f8f9fa"})

    fig = plt.figure(figsize=(18, 13))
    gs = fig.add_gridspec(2, 2, height_ratios=[1.2, 1], hspace=0.35, wspace=0.3)
    ax_time = fig.add_subplot(gs[0, :])
    ax_anom = fig.add_subplot(gs[1, 0])
    ax_text = fig.add_subplot(gs[1, 1])

    # ── Panel 1: Financial Timeline ──────────────────────────────────────────
    dates = [t["date"] for t in transactions]
    balances = [t["balance"] for t in transactions]
    ax_time.plot(dates, balances, color="#2C3E50", lw=2, zorder=1, label="Balance")

    credits = [t for t in transactions if t["type"] == "credit"]
    debits = [t for t in transactions if t["type"] == "debit"]

    if credits:
        c_dates = [t["date"] for t in credits]
        c_bals = [t["balance"] for t in credits]
        c_amts = np.array([t["amount"] for t in credits])
        c_sizes = (c_amts / c_amts.max()) * 400 + 40
        ax_time.scatter(c_dates, c_bals, s=c_sizes, color="#27AE60", alpha=0.7,
                        zorder=2, label="Credit", edgecolor="white", lw=0.5)
    if debits:
        d_dates = [t["date"] for t in debits]
        d_bals = [t["balance"] for t in debits]
        d_amts = np.array([t["amount"] for t in debits])
        d_sizes = (d_amts / d_amts.max()) * 400 + 40
        ax_time.scatter(d_dates, d_bals, s=d_sizes, color="#E74C3C", alpha=0.7,
                        zorder=2, label="Debit", edgecolor="white", lw=0.5)

    ax_time.axhline(0, color="black", lw=1, ls="--", alpha=0.4)
    behav_class = predictions.get("behavioral_class", "?").upper()
    ax_time.set_title(f"Financial Timeline: {name} ({user_id}) — {behav_class}",
                      fontsize=18, fontweight="bold", pad=15)
    ax_time.set_ylabel("Balance (INR)", fontsize=13, fontweight="bold")
    ax_time.set_xlabel("")
    ax_time.legend(loc="upper left", fontsize=11)
    ax_time.tick_params(axis="x", rotation=20)

    # ── Panel 2: Top 5 Risk Drivers (Z-Score) ────────────────────────────────
    all_cols = [
        "total_transactions", "txn_frequency", "avg_transaction_amount",
        "monthly_inflow", "monthly_outflow", "inflow_outflow_ratio",
        "inflow_variance", "avg_balance", "min_balance", "max_balance",
        "balance_std", "small_credit_count", "large_debit_count",
        "credit_debit_time_gap", "consecutive_zero_balance_days", "cash_vs_upi_ratio",
        "debt_to_income_ratio", "repayment_ratio", "missed_payment_count",
        "avg_days_past_due", "debt_growth_rate", "outstanding_to_balance_ratio",
        "total_loan_amount", "total_outstanding", "avg_interest_rate", "num_loans",
    ]

    reasons = []
    for feat in all_cols:
        val = features.get(feat, 0)
        m = POP_STATS.get(feat, {}).get("mean", 0)
        s = POP_STATS.get(feat, {}).get("std", 1)
        z = (val - m) / s if s > 0 else 0
        imp = FEATURE_IMPORTANCE.get(feat, 0.01)
        score = abs(z) * imp
        reasons.append({"feature": feat, "score": score, "val": val, "mean": m, "z": z})
    top_reasons = sorted(reasons, key=lambda x: x["score"], reverse=True)[:5]

    feat_names = [r["feature"].replace("_", " ").title() for r in top_reasons]
    z_scores = [r["z"] for r in top_reasons]
    bar_colors = ["#E74C3C" if z > 0 else "#3498DB" for z in z_scores]
    y_pos = np.arange(len(feat_names))

    ax_anom.barh(y_pos, z_scores, align="center", color=bar_colors, edgecolor="white")
    ax_anom.set_yticks(y_pos)
    ax_anom.set_yticklabels(feat_names, fontsize=11)
    ax_anom.invert_yaxis()
    ax_anom.set_xlabel("Z-Score vs Population", fontsize=12, fontweight="bold")
    ax_anom.set_title("Top 5 Risk Drivers", fontsize=15, fontweight="bold")
    ax_anom.axvline(0, color="black", lw=1)

    # ── Panel 3: Risk Summary Card ───────────────────────────────────────────
    ax_text.axis("off")

    prob = predictions.get("default_probability", 0)
    prob = prob if isinstance(prob, (int, float)) else 0
    tier = predictions.get("risk_tier", "unknown").upper().replace("_", " ")
    tier_color = {"LOW RISK": "#27AE60", "MEDIUM RISK": "#F39C12", "HIGH RISK": "#E74C3C"}.get(tier, "#95A5A6")

    ax_text.text(0.5, 0.98, f"RISK TIER: {tier}", color=tier_color, fontsize=22,
                 fontweight="bold", ha="center", transform=ax_text.transAxes)

    info = (
        f"User ID: {user_id}\n"
        f"Name:    {name}\n\n"
        f"--- MODEL PREDICTIONS ---\n"
        f"  Behavior Class:  {behav_class}\n"
        f"  Default Prob:    {prob:.4f} ({prob*100:.1f}%)\n"
        f"  Risk Tier:       {tier}\n\n"
        f"--- LOAN SUMMARY ---\n"
        f"  Loan Amount:     INR {features.get('total_loan_amount',0):,.0f}\n"
        f"  Outstanding:     INR {features.get('total_outstanding',0):,.0f}\n"
        f"  Repayment Ratio: {features.get('repayment_ratio',0):.2f}\n"
        f"  Missed Payments: {int(features.get('missed_payment_count',0))}\n"
        f"  Avg Days Past Due: {features.get('avg_days_past_due',0):.0f}\n\n"
        f"[DIAGNOSTIC INSIGHTS]\n"
    )
    for i, r in enumerate(top_reasons):
        direction = "Higher" if r["z"] > 0 else "Lower"
        info += (
            f"{i+1}. {r['feature'].replace('_',' ').title()}:\n"
            f"   Actual: {r['val']:.1f}  |  Pop Mean: {r['mean']:.1f}\n"
            f"   {direction} than average (Z: {r['z']:+.2f})\n"
        )

    ax_text.text(0.05, 0.88, info, transform=ax_text.transAxes, fontsize=9.5,
                 verticalalignment="top", family="monospace",
                 bbox=dict(boxstyle="round,pad=1", facecolor="#FEF9E7",
                           edgecolor="#D4AC0D", alpha=0.8))

    plt.savefig(filepath, dpi=200, bbox_inches="tight")
    plt.close()
    print(f"Diagnostic visualization saved: {filepath}")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print(f"  Generating demo data for: {ACCOUNT_HOLDER}")
    print("=" * 60)

    # Generate raw data
    transactions = generate_transactions()
    loans = generate_loans()

    # Save CSVs
    save_transactions_csv(transactions, os.path.join(OUTPUT_DIR, "roshan_transactions.csv"))
    save_loans_csv(loans, os.path.join(OUTPUT_DIR, "roshan_loans.csv"))

    # Generate PDFs
    create_bank_statement_pdf(transactions, os.path.join(OUTPUT_DIR, "Roshan_Pandey_Bank_Statement.pdf"))
    create_loan_slip_pdf(loans, os.path.join(OUTPUT_DIR, "Roshan_Pandey_Loan_Slip.pdf"))

    # Compute features
    print("\n--- Computing Engineered Features ---")
    behavioral = compute_behavioral_features(transactions)
    debt = compute_debt_features(loans, behavioral["monthly_inflow"])

    # outstanding_to_balance_ratio needs avg_balance
    outstanding_to_balance_ratio = round(
        debt["total_outstanding"] / behavioral["avg_balance"]
        if behavioral["avg_balance"] > 0 else 0, 2
    )

    all_features = {**behavioral, **debt, "outstanding_to_balance_ratio": outstanding_to_balance_ratio}

    print("\nAll 26 engineered features:")
    print("-" * 40)
    for k, v in all_features.items():
        print(f"  {k:35s}: {v}")

    # Save features JSON
    features_path = os.path.join(OUTPUT_DIR, "roshan_features.json")
    with open(features_path, "w") as f:
        json.dump({"user_id": "ROSHAN01", "name": ACCOUNT_HOLDER, "features": all_features}, f, indent=2)
    print(f"\nFeatures saved: {features_path}")

    # Call Databricks endpoints
    print("\n" + "=" * 60)
    print("  Calling Databricks Model Endpoints")
    print("=" * 60)
    predictions = call_databricks_endpoints(all_features)

    # Save final results
    result = {
        "user_id": "ROSHAN01",
        "name": ACCOUNT_HOLDER,
        "features": all_features,
        "predictions": predictions,
    }
    result_path = os.path.join(OUTPUT_DIR, "roshan_prediction_result.json")
    with open(result_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\nFull result saved: {result_path}")

    # Generate diagnostic visualization
    create_diagnostic_visualization(
        transactions, all_features, predictions,
        user_id="ROSHAN01", name=ACCOUNT_HOLDER,
        filepath=os.path.join(OUTPUT_DIR, "Roshan_Pandey_Diagnostic.png"),
    )

    print("\n" + "=" * 60)
    print("  Generated files:")
    print(f"    📄 {os.path.join(OUTPUT_DIR, 'Roshan_Pandey_Bank_Statement.pdf')}")
    print(f"    📄 {os.path.join(OUTPUT_DIR, 'Roshan_Pandey_Loan_Slip.pdf')}")
    print(f"    📊 {os.path.join(OUTPUT_DIR, 'roshan_transactions.csv')}")
    print(f"    📊 {os.path.join(OUTPUT_DIR, 'roshan_loans.csv')}")
    print(f"    🔧 {os.path.join(OUTPUT_DIR, 'roshan_features.json')}")
    print(f"    🎯 {os.path.join(OUTPUT_DIR, 'roshan_prediction_result.json')}")
    print(f"    📈 {os.path.join(OUTPUT_DIR, 'Roshan_Pandey_Diagnostic.png')}")
    print("=" * 60)


if __name__ == "__main__":
    main()
