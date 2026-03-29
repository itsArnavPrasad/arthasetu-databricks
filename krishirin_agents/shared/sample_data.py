"""
Sample data for running the pipeline without Databricks Delta tables.
Represents a typical small farmer in Maharashtra applying for a KCC loan.
"""

SAMPLE_FARMER_PROFILE = {
    "farmer_id": "FARMER_001",
    "name": "Ramesh Patil",
    "age": 42,
    "gender": "Male",
    "district": "Nashik",
    "state": "Maharashtra",
    "land_holding_acres": 3.0,
    "land_type": "owned",
    "irrigation_type": "mixed",
    "crops": ["soybean", "onion", "wheat"],
    "existing_loans": [
        {
            "type": "crop_loan",
            "amount": 50000,
            "emi": 2500,
            "status": "active",
            "lender": "SBI",
        }
    ],
    "govt_schemes": ["PM-KISAN"],
    "bank_summary": {
        "months_available": 12,
        "avg_monthly_income": 18000,
        "bank_avg_monthly_credit": 16500,
        "avg_monthly_expense": 12000,
        "avg_monthly_savings": 4500,
        "savings_rate": 0.25,
        "income_variance": 0.35,
        "min_balance": 2200,
        "max_balance": 45000,
    },
    "aadhaar_last4": "7834",
    "documents_provided": ["aadhaar", "bank_statement", "land_record"],
}

SAMPLE_ML_SCORES = {
    "farmer_id": "FARMER_001",
    "grameen_score": 68.5,
    "risk_category": "B",
    "repayment_prob": 0.78,
    "risk_cluster": 1,
    "predicted_capacity": 200000,
    "top_positive_factors": [
        "Regular savings pattern (25% savings rate)",
        "12-month consistent banking history",
        "Land ownership provides collateral security",
        "PM-KISAN enrollment shows scheme awareness",
        "Mixed irrigation reduces drought risk",
    ],
    "top_negative_factors": [
        "Income seasonality (35% variance across months)",
        "Existing crop loan of ₹50,000 with SBI",
        "Single-district dependency (no geographic diversification)",
    ],
}

SAMPLE_DISTRICT_DATA = {
    "district": "Nashik",
    "state": "Maharashtra",
    "avg_yield_per_hectare": 12.5,
    "irrigation_pct": 45.0,
    "avg_rainfall_mm": 600,
    "rainfall_variability": 0.35,
    "crop_failure_rate": 0.12,
    "dominant_crops": ["onion", "grape", "soybean", "wheat", "tomato"],
    "soil_type": "Black cotton soil (Regur)",
    "agro_climatic_zone": "Western Plateau and Hills",
}

SAMPLE_CROP_CALENDAR = [
    {
        "crop": "soybean",
        "season": "Kharif",
        "sowing_start": "June 15",
        "sowing_end": "July 15",
        "harvest_start": "October 1",
        "harvest_end": "November 15",
        "water_requirement_mm": 450,
        "growing_days": 100,
    },
    {
        "crop": "onion",
        "season": "Rabi",
        "sowing_start": "October 15",
        "sowing_end": "November 30",
        "harvest_start": "February 15",
        "harvest_end": "March 31",
        "water_requirement_mm": 350,
        "growing_days": 120,
    },
    {
        "crop": "wheat",
        "season": "Rabi",
        "sowing_start": "November 1",
        "sowing_end": "December 15",
        "harvest_start": "March 15",
        "harvest_end": "April 30",
        "water_requirement_mm": 400,
        "growing_days": 135,
    },
]

SAMPLE_MSP_PRICES = [
    {"crop": "soybean", "msp_per_quintal": 4600, "year": "2025-26"},
    {"crop": "onion", "msp_per_quintal": None, "year": "2025-26", "note": "No MSP for onion, market-driven"},
    {"crop": "wheat", "msp_per_quintal": 2275, "year": "2025-26"},
    {"crop": "rice", "msp_per_quintal": 2320, "year": "2025-26"},
    {"crop": "cotton", "msp_per_quintal": 7121, "year": "2025-26"},
    {"crop": "gram", "msp_per_quintal": 5650, "year": "2025-26"},
    {"crop": "moong", "msp_per_quintal": 8682, "year": "2025-26"},
    {"crop": "groundnut", "msp_per_quintal": 6377, "year": "2025-26"},
    {"crop": "mustard", "msp_per_quintal": 5950, "year": "2025-26"},
    {"crop": "sugarcane", "msp_per_quintal": 315, "year": "2025-26"},
]

SAMPLE_WEATHER = {
    "district": "Nashik",
    "current": {
        "temp_c": 32.5,
        "humidity": 45,
        "description": "partly cloudy",
        "wind_speed_mps": 3.2,
        "rain_mm": 0,
    },
    "forecast": [
        {"date": "2026-03-28", "temp_max": 34, "temp_min": 20, "humidity": 42, "description": "clear sky", "rain_mm": 0},
        {"date": "2026-03-29", "temp_max": 35, "temp_min": 21, "humidity": 38, "description": "clear sky", "rain_mm": 0},
        {"date": "2026-03-30", "temp_max": 33, "temp_min": 22, "humidity": 55, "description": "scattered clouds", "rain_mm": 0},
        {"date": "2026-03-31", "temp_max": 31, "temp_min": 21, "humidity": 65, "description": "light rain", "rain_mm": 5},
        {"date": "2026-04-01", "temp_max": 30, "temp_min": 20, "humidity": 70, "description": "moderate rain", "rain_mm": 12},
        {"date": "2026-04-02", "temp_max": 32, "temp_min": 21, "humidity": 50, "description": "partly cloudy", "rain_mm": 0},
        {"date": "2026-04-03", "temp_max": 33, "temp_min": 22, "humidity": 45, "description": "clear sky", "rain_mm": 0},
    ],
}

# ── Sample OCR-extracted data (for testing without actual document uploads) ────

SAMPLE_OCR_BANK_STATEMENT = {
    "account_holder": "Ramesh Patil",
    "bank_name": "State Bank of India",
    "account_number_last4": "7834",
    "period_start": "2025-04-01",
    "period_end": "2026-03-15",
    "transactions": [
        {"date": "2025-04-05", "description": "NEFT-Mandi Sale", "credit": 18000, "debit": None, "balance": 22000, "channel_hint": "NEFT"},
        {"date": "2025-04-10", "description": "ATM Withdrawal", "credit": None, "debit": 5000, "balance": 17000, "channel_hint": "ATM"},
        {"date": "2025-04-15", "description": "UPI-Fertilizer Shop", "credit": None, "debit": 3500, "balance": 13500, "channel_hint": "UPI"},
        {"date": "2025-05-01", "description": "PM-KISAN Transfer", "credit": 2000, "debit": None, "balance": 15500, "channel_hint": "NEFT"},
        {"date": "2025-05-10", "description": "Cash Deposit", "credit": 8000, "debit": None, "balance": 23500, "channel_hint": "cash"},
        {"date": "2025-05-20", "description": "SBI Crop Loan EMI", "credit": None, "debit": 2500, "balance": 21000, "channel_hint": "other"},
        {"date": "2025-06-01", "description": "NEFT-Seed Purchase", "credit": None, "debit": 6000, "balance": 15000, "channel_hint": "NEFT"},
        {"date": "2025-06-15", "description": "UPI-Labour Payment", "credit": None, "debit": 4000, "balance": 11000, "channel_hint": "UPI"},
        {"date": "2025-07-01", "description": "PM-KISAN Transfer", "credit": 2000, "debit": None, "balance": 13000, "channel_hint": "NEFT"},
        {"date": "2025-07-20", "description": "Cash Deposit-Dairy", "credit": 3000, "debit": None, "balance": 16000, "channel_hint": "cash"},
        {"date": "2025-08-05", "description": "UPI-Pesticide", "credit": None, "debit": 2000, "balance": 14000, "channel_hint": "UPI"},
        {"date": "2025-08-20", "description": "SBI Crop Loan EMI", "credit": None, "debit": 2500, "balance": 11500, "channel_hint": "other"},
        {"date": "2025-09-10", "description": "Cash Deposit", "credit": 5000, "debit": None, "balance": 16500, "channel_hint": "cash"},
        {"date": "2025-10-15", "description": "NEFT-Soybean Sale", "credit": 32000, "debit": None, "balance": 48500, "channel_hint": "NEFT"},
        {"date": "2025-10-20", "description": "SBI Crop Loan EMI", "credit": None, "debit": 2500, "balance": 46000, "channel_hint": "other"},
        {"date": "2025-11-01", "description": "PM-KISAN Transfer", "credit": 2000, "debit": None, "balance": 48000, "channel_hint": "NEFT"},
        {"date": "2025-11-10", "description": "NEFT-Onion Seed Purchase", "credit": None, "debit": 4500, "balance": 43500, "channel_hint": "NEFT"},
        {"date": "2025-12-01", "description": "UPI-Irrigation Pump Repair", "credit": None, "debit": 3000, "balance": 40500, "channel_hint": "UPI"},
        {"date": "2026-01-15", "description": "Cash Deposit-Dairy", "credit": 3500, "debit": None, "balance": 44000, "channel_hint": "cash"},
        {"date": "2026-02-20", "description": "SBI Crop Loan EMI", "credit": None, "debit": 2500, "balance": 41500, "channel_hint": "other"},
        {"date": "2026-03-10", "description": "NEFT-Onion Sale", "credit": 28000, "debit": None, "balance": 69500, "channel_hint": "NEFT"},
    ],
    "summary": {
        "total_credits": 103500,
        "total_debits": 36000,
        "avg_balance": 28500,
        "opening_balance": 4000,
        "closing_balance": 69500,
    },
}

SAMPLE_OCR_LOAN_SLIP = {
    "lender": "State Bank of India",
    "loan_type": "crop_loan",
    "loan_amount": 50000,
    "interest_rate": 7.0,
    "emi_amount": 2500,
    "outstanding_amount": 25000,
    "amount_repaid": 25000,
    "disbursement_date": "2025-03-01",
    "tenure_months": 24,
    "status": "active",
}


SAMPLE_SCHEME_CHUNKS = [
    {
        "text": "Kisan Credit Card (KCC): All farmers including tenant farmers and sharecroppers are eligible. Loan limit up to ₹3 lakh for crop cultivation. Interest rate 7% p.a. with 2% Government subvention and 3% prompt repayment incentive, effective rate 2% for loans up to ₹3 lakh repaid on time. Collateral waived for loans up to ₹1.6 lakh. Card valid for 5 years with annual review.",
        "source": "KCC_Guidelines_RBI_2024.pdf",
        "scheme_name": "KCC",
    },
    {
        "text": "PM-KISAN: Income support of ₹6,000 per year in 3 installments of ₹2,000 each to all landholding farmer families. Exclusions: institutional landholders, former/present holders of constitutional posts, income tax payers, professionals. Registration through CSC or PM-KISAN portal with Aadhaar, bank account, and land records.",
        "source": "PMKISAN_Scheme_Details.pdf",
        "scheme_name": "PM-KISAN",
    },
    {
        "text": "PMFBY (Pradhan Mantri Fasal Bima Yojana): Crop insurance for all farmers growing notified crops in notified areas. Premium: 2% for Kharif crops, 1.5% for Rabi crops, 5% for commercial/horticulture crops. Covers: prevented sowing, standing crop loss, post-harvest losses (up to 14 days), localized calamities. Claim settlement through crop cutting experiments and remote sensing.",
        "source": "PMFBY_Guidelines_2023.pdf",
        "scheme_name": "PMFBY",
    },
    {
        "text": "MUDRA Yojana: Loans for micro/small enterprises and allied activities. Three categories: Shishu (up to ₹50,000), Kishore (₹50,000 to ₹5 lakh), Tarun (₹5 lakh to ₹10 lakh). No collateral required for Shishu loans. Interest rates vary by bank (typically 10-12% p.a.). Applicable for dairy, poultry, fishery, food processing, and other allied agricultural activities.",
        "source": "MUDRA_Scheme_SIDBI.pdf",
        "scheme_name": "MUDRA",
    },
    {
        "text": "Maharashtra Shetkari Sanman Yojana: State-level scheme providing ₹12,000 per year income support to farmer families with land up to 5 hectares in Maharashtra. This supplements the PM-KISAN scheme. Requires Aadhaar linkage, land records (7/12 extract), and bank account in Maharashtra.",
        "source": "Maharashtra_Agriculture_Dept_2024.pdf",
        "scheme_name": "Maharashtra Shetkari Sanman",
    },
]
