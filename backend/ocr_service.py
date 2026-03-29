"""
OCR Service — GPT-4o-mini Vision API for document extraction.

Processes uploaded farmer documents (bank statement, loan slip, land record,
Aadhaar, crop receipt) and returns structured JSON per document type.
"""

import base64
import json
import logging
import os
from pathlib import Path

from openai import OpenAI

logger = logging.getLogger(__name__)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

MODEL = "gpt-4o-mini"


# ── Per-document extraction prompts ──────────────────────────────────────────

_PROMPTS = {
    "aadhaar": """Extract the following fields from this Aadhaar card image.
Return ONLY a JSON object with these fields:
{
  "name": "Full name as printed",
  "aadhaar_last4": "Last 4 digits of Aadhaar number",
  "address": "Full address if visible",
  "district": "District name",
  "state": "State name",
  "gender": "Male/Female if visible",
  "dob": "Date of birth if visible (DD/MM/YYYY)"
}
If a field is not visible or unreadable, set it to null.
Return ONLY valid JSON, no markdown or explanation.""",

    "bank_statement": """Extract transaction data from this bank statement image/PDF page.
Return ONLY a JSON object with these fields:
{
  "account_holder": "Account holder name",
  "bank_name": "Bank name",
  "account_number_last4": "Last 4 digits of account number",
  "period_start": "Statement start date (YYYY-MM-DD)",
  "period_end": "Statement end date (YYYY-MM-DD)",
  "transactions": [
    {
      "date": "YYYY-MM-DD",
      "description": "Transaction narration/description",
      "credit": null or amount as number,
      "debit": null or amount as number,
      "balance": balance after transaction as number,
      "channel_hint": "UPI/NEFT/cash/ATM/cheque/other — infer from description"
    }
  ],
  "summary": {
    "total_credits": total credit amount,
    "total_debits": total debit amount,
    "avg_balance": approximate average balance,
    "opening_balance": opening balance if visible,
    "closing_balance": closing balance if visible
  }
}
IMPORTANT: Extract ALL visible transactions. Parse amounts as numbers (remove commas).
Infer channel_hint from description: "UPI" if contains UPI/GPay/PhonePe, "NEFT" for NEFT/RTGS,
"cash" for cash deposit/withdrawal, "ATM" for ATM, "cheque" for cheque/CHQ.
Return ONLY valid JSON, no markdown or explanation.""",

    "land_record": """Extract details from this Indian land record (7/12 extract, 8A, or similar).
Return ONLY a JSON object with these fields:
{
  "owner_name": "Land owner name(s)",
  "district": "District name",
  "taluka": "Taluka/Tehsil name",
  "village": "Village name",
  "survey_number": "Survey/Gat number",
  "area_acres": area in acres as number (convert from hectares if needed: 1 ha = 2.47 acres),
  "land_type": "owned/leased/shared — infer from document type",
  "irrigation_source": "well/borewell/canal/rainfed/mixed — if mentioned",
  "soil_type": "Soil type if mentioned",
  "crops_mentioned": ["List of crops if mentioned in the record"]
}
If a field is not visible, set it to null. Convert all areas to acres.
Return ONLY valid JSON, no markdown or explanation.""",

    "loan_slip": """Extract loan details from this loan document (sanction letter, passbook, receipt).
Return ONLY a JSON object with these fields:
{
  "lender": "Bank/institution name",
  "loan_type": "crop_loan/term_loan/KCC/gold_loan/personal/other",
  "loan_amount": principal amount as number,
  "interest_rate": annual interest rate as number (e.g. 7.0),
  "emi_amount": EMI amount if mentioned as number,
  "outstanding_amount": outstanding/due amount if visible as number,
  "amount_repaid": amount already repaid if visible as number,
  "disbursement_date": "YYYY-MM-DD if visible",
  "tenure_months": loan tenure in months as number,
  "status": "active/closed/overdue — infer from document"
}
If a field is not visible, set it to null.
Return ONLY valid JSON, no markdown or explanation.""",

    "crop_receipt": """Extract details from this crop sale receipt / mandi slip.
Return ONLY a JSON object with these fields:
{
  "crop_name": "Name of crop sold",
  "quantity_quintals": quantity in quintals as number,
  "price_per_quintal": price per quintal in Rs as number,
  "total_amount": total sale amount in Rs as number,
  "mandi_name": "Market/Mandi name",
  "date": "YYYY-MM-DD",
  "buyer_name": "Buyer/trader name if visible"
}
If a field is not visible, set it to null.
Return ONLY valid JSON, no markdown or explanation.""",
}


def _encode_image(file_path: str) -> tuple[str, str]:
    """Read an image file and return (base64_data, media_type)."""
    ext = Path(file_path).suffix.lower()
    media_map = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }
    media_type = media_map.get(ext, "image/jpeg")
    with open(file_path, "rb") as f:
        data = base64.b64encode(f.read()).decode("utf-8")
    return data, media_type


def _pdf_to_images(file_path: str) -> list[tuple[str, str]]:
    """Convert a PDF to a list of (base64_data, media_type) per page.

    Uses pdf2image (poppler) to render each page as a JPEG image.
    """
    from pdf2image import convert_from_path
    import io

    images = convert_from_path(file_path, dpi=200, fmt="jpeg")
    results = []
    for page_img in images:
        buf = io.BytesIO()
        page_img.save(buf, format="JPEG", quality=90)
        b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
        results.append((b64, "image/jpeg"))
    return results


def _build_image_content(file_path: str) -> list[dict]:
    """Build the image content blocks for the OpenAI Vision API.

    For images: returns a single image block.
    For PDFs: converts each page to an image and returns multiple image blocks.
    """
    ext = Path(file_path).suffix.lower()

    if ext == ".pdf":
        pages = _pdf_to_images(file_path)
        logger.info(f"Converted PDF to {len(pages)} page images")
        return [
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:{media_type};base64,{b64_data}",
                    "detail": "high",
                },
            }
            for b64_data, media_type in pages
        ]
    else:
        b64_data, media_type = _encode_image(file_path)
        return [
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:{media_type};base64,{b64_data}",
                    "detail": "high",
                },
            }
        ]


def _call_vision(image_blocks: list[dict], prompt: str, retries: int = 2) -> dict:
    """Call GPT-4o-mini Vision API and return parsed JSON.

    Uses response_format=json_object to guarantee valid JSON output.
    Retries on failure.
    """
    # Wrap prompt in a system message that enforces JSON, plus the user message with images
    messages = [
        {
            "role": "system",
            "content": "You are a document OCR extraction assistant. You MUST respond with valid JSON only. No markdown, no explanation, no text outside the JSON object.",
        },
        {
            "role": "user",
            "content": image_blocks + [{"type": "text", "text": prompt}],
        },
    ]

    last_error = None
    for attempt in range(retries + 1):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                max_tokens=16384,
                temperature=0.1,
                response_format={"type": "json_object"},
            )

            raw_text = response.choices[0].message.content.strip()
            return json.loads(raw_text)

        except json.JSONDecodeError as e:
            last_error = e
            logger.warning(f"Vision API returned invalid JSON (attempt {attempt + 1}): {e}")
            # On retry, add a nudge
            if attempt < retries:
                messages.append({"role": "assistant", "content": raw_text})
                messages.append({
                    "role": "user",
                    "content": "Your previous response was not valid JSON. Please respond with ONLY a valid JSON object matching the requested schema. Make sure all strings are properly closed and all brackets are matched.",
                })
        except Exception as e:
            last_error = e
            logger.warning(f"Vision API error (attempt {attempt + 1}): {e}")
            if attempt >= retries:
                raise

    raise last_error


def _process_bank_statement_pdf(file_path: str, farmer_id: str) -> dict:
    """Process a multi-page bank statement PDF page-by-page and merge results.

    Bank statements can have hundreds of transactions across multiple pages.
    Processing all pages in one API call can exceed output token limits.
    Instead, process each page separately and merge the transaction lists.
    """
    prompt = _PROMPTS["bank_statement"]
    pages = _pdf_to_images(file_path)
    logger.info(f"Processing bank statement: {len(pages)} pages for {farmer_id}")

    all_transactions = []
    header_info = {}  # account_holder, bank_name, etc. — from first page

    for i, (b64_data, media_type) in enumerate(pages):
        page_prompt = prompt + f"\n\nThis is page {i + 1} of {len(pages)} of the bank statement."
        if i > 0:
            page_prompt += " Focus on extracting the transactions table rows on this page. The account header info may not be repeated — that's fine, set header fields to null."

        image_block = [{
            "type": "image_url",
            "image_url": {"url": f"data:{media_type};base64,{b64_data}", "detail": "high"},
        }]

        try:
            page_data = _call_vision(image_block, page_prompt)

            # Collect header info from first page (or any page that has it)
            for key in ("account_holder", "bank_name", "account_number_last4", "period_start", "period_end"):
                if page_data.get(key) and not header_info.get(key):
                    header_info[key] = page_data[key]

            # Collect transactions
            page_txns = page_data.get("transactions", [])
            all_transactions.extend(page_txns)
            logger.info(f"  Page {i + 1}: {len(page_txns)} transactions extracted")

            # Collect summary if present
            if page_data.get("summary") and not header_info.get("summary"):
                header_info["summary"] = page_data["summary"]

        except Exception as e:
            logger.warning(f"  Page {i + 1} OCR failed: {e}")
            continue

    if not all_transactions and not header_info:
        return {
            "status": "error",
            "doc_type": "bank_statement",
            "error": "Could not extract any data from any page",
            "extracted_data": {},
        }

    # Compute summary from transactions if not provided
    summary = header_info.get("summary", {})
    if all_transactions:
        total_credits = sum(t.get("credit") or 0 for t in all_transactions)
        total_debits = sum(t.get("debit") or 0 for t in all_transactions)
        balances = [t.get("balance") for t in all_transactions if t.get("balance") is not None]
        avg_balance = sum(balances) / len(balances) if balances else 0
        summary = {
            "total_credits": round(total_credits, 2),
            "total_debits": round(total_debits, 2),
            "avg_balance": round(avg_balance, 2),
            "opening_balance": balances[0] if balances else None,
            "closing_balance": balances[-1] if balances else None,
        }

    extracted = {
        **header_info,
        "transactions": all_transactions,
        "summary": summary,
    }

    total_fields = len(extracted)
    non_null = sum(1 for v in extracted.values() if v is not None and v != "" and v != [])
    confidence = round(non_null / max(total_fields, 1), 2)

    logger.info(
        f"OCR [bank_statement] for {farmer_id}: {len(all_transactions)} total transactions "
        f"from {len(pages)} pages (confidence={confidence})"
    )

    return {
        "status": "success",
        "doc_type": "bank_statement",
        "extracted_data": extracted,
        "confidence": confidence,
    }


def process_document(file_path: str, doc_type: str, farmer_id: str) -> dict:
    """Process an uploaded document via GPT-4o-mini Vision API.

    Supports images (JPG, PNG) and PDFs (multi-page).
    Bank statement PDFs are processed page-by-page to avoid token limit truncation.

    Args:
        file_path: Path to the saved file on disk.
        doc_type: One of 'aadhaar', 'bank_statement', 'land_record', 'loan_slip', 'crop_receipt'.
        farmer_id: Farmer identifier for logging.

    Returns:
        dict with keys: 'status' ('success'|'error'), 'doc_type', 'extracted_data', 'confidence'.
    """
    prompt = _PROMPTS.get(doc_type)
    if not prompt:
        return {
            "status": "error",
            "doc_type": doc_type,
            "error": f"Unknown document type: {doc_type}",
            "extracted_data": {},
        }

    # Bank statement PDFs get special page-by-page processing
    ext = Path(file_path).suffix.lower()
    if doc_type == "bank_statement" and ext == ".pdf":
        try:
            return _process_bank_statement_pdf(file_path, farmer_id)
        except Exception as e:
            logger.error(f"Bank statement PDF processing failed: {e}", exc_info=True)
            return {"status": "error", "doc_type": doc_type, "error": str(e), "extracted_data": {}}

    try:
        image_blocks = _build_image_content(file_path)
        extracted = _call_vision(image_blocks, prompt)

        # Compute a simple confidence indicator based on null fields
        total_fields = len(extracted)
        non_null = sum(1 for v in extracted.values() if v is not None and v != "" and v != [])
        confidence = round(non_null / max(total_fields, 1), 2)

        logger.info(
            f"OCR [{doc_type}] for {farmer_id}: extracted {non_null}/{total_fields} fields "
            f"(confidence={confidence})"
        )

        return {
            "status": "success",
            "doc_type": doc_type,
            "extracted_data": extracted,
            "confidence": confidence,
        }

    except Exception as e:
        logger.error(f"OCR error for {doc_type}/{farmer_id}: {e}", exc_info=True)
        return {
            "status": "error",
            "doc_type": doc_type,
            "error": str(e),
            "extracted_data": {},
        }


def _get_ocr_items(ocr_results: dict, key: str) -> list[dict]:
    """Get OCR results for a key, normalizing single dicts and lists."""
    val = ocr_results.get(key)
    if val is None:
        return []
    if isinstance(val, list):
        return [v for v in val if isinstance(v, dict) and v.get("status") == "success"]
    if isinstance(val, dict) and val.get("status") == "success":
        return [val]
    return []


def merge_ocr_into_farmer_data(farmer_data: dict, ocr_results: dict) -> dict:
    """Merge OCR-extracted data from all documents into the farmer_data dict.

    Supports multiple documents per type (e.g., multiple land records, loan slips).
    """
    merged = {**farmer_data}

    # --- Aadhaar (single) ---
    for item in _get_ocr_items(ocr_results, "aadhaar"):
        aadhaar = item.get("extracted_data", {})
        if aadhaar.get("name"):
            merged["name"] = aadhaar["name"]
        if aadhaar.get("aadhaar_last4"):
            merged["aadhaar_last4"] = aadhaar["aadhaar_last4"]
        if aadhaar.get("district"):
            merged.setdefault("district", aadhaar["district"])
        if aadhaar.get("state"):
            merged.setdefault("state", aadhaar["state"])

    # --- Land Records (multiple → accumulate acreage) ---
    total_acres = 0
    for item in _get_ocr_items(ocr_results, "land_record"):
        land = item.get("extracted_data", {})
        if land.get("area_acres"):
            total_acres += float(land["area_acres"])
        if land.get("land_type"):
            merged["land_type"] = land["land_type"]
        if land.get("district"):
            merged["district"] = land["district"]
        if land.get("taluka"):
            merged["taluka"] = land["taluka"]
        if land.get("village"):
            merged["village"] = land["village"]
        if land.get("irrigation_source"):
            merged["irrigation_type"] = land["irrigation_source"]
        if land.get("crops_mentioned"):
            existing_crops = set(c.lower() for c in merged.get("crops", []))
            for crop in land["crops_mentioned"]:
                if crop.lower() not in existing_crops:
                    merged.setdefault("crops", []).append(crop)
                    existing_crops.add(crop.lower())
    if total_acres > 0:
        merged["land_holding_acres"] = total_acres

    # --- Bank Statements (multiple → merge transactions) ---
    all_transactions = []
    header_info = {}
    for item in _get_ocr_items(ocr_results, "bank_statement"):
        bank = item.get("extracted_data", {})
        txns = bank.get("transactions", [])
        all_transactions.extend(txns)
        for key in ("account_holder", "bank_name", "period_start", "period_end"):
            if bank.get(key) and not header_info.get(key):
                header_info[key] = bank[key]

    if all_transactions or header_info:
        total_credits = sum(t.get("credit", 0) or 0 for t in all_transactions)
        total_debits = sum(t.get("debit", 0) or 0 for t in all_transactions)
        balances = [t.get("balance") for t in all_transactions if t.get("balance") is not None]
        avg_balance = sum(balances) / len(balances) if balances else 0

        # Estimate months from transaction date range
        months = 1
        dates = [t["date"] for t in all_transactions if t.get("date")]
        if len(dates) >= 2:
            from datetime import datetime
            try:
                d_start = datetime.strptime(min(dates), "%Y-%m-%d")
                d_end = datetime.strptime(max(dates), "%Y-%m-%d")
                months = max((d_end - d_start).days / 30, 1)
            except ValueError:
                months = max(len(all_transactions) / 10, 1)

        merged["bank_summary"] = {
            **header_info,
            "total_credits": round(total_credits, 2),
            "total_debits": round(total_debits, 2),
            "avg_balance": round(avg_balance, 2),
            "transaction_count": len(all_transactions),
            "avg_monthly_income": round(total_credits / months),
            "avg_monthly_expense": round(total_debits / months),
            "months_of_history": round(months),
        }
        merged["_raw_transactions"] = all_transactions

    # --- Loan Slips (multiple → append each as separate loan) ---
    merged["existing_loans"] = []
    merged["_raw_loan_data"] = []
    for item in _get_ocr_items(ocr_results, "loan_slip"):
        loan = item.get("extracted_data", {})
        merged["existing_loans"].append({
            "type": loan.get("loan_type", "unknown"),
            "amount": loan.get("loan_amount"),
            "outstanding": loan.get("outstanding_amount"),
            "amount_repaid": loan.get("amount_repaid"),
            "emi": loan.get("emi_amount"),
            "interest_rate": loan.get("interest_rate"),
            "tenure_months": loan.get("tenure_months"),
            "status": loan.get("status", "active"),
            "lender": loan.get("lender"),
        })
        merged["_raw_loan_data"].append(loan)

    # --- Crop Receipts (multiple → append each) ---
    merged.setdefault("crop_sales_history", [])
    for item in _get_ocr_items(ocr_results, "crop_receipt"):
        receipt = item.get("extracted_data", {})
        merged["crop_sales_history"].append(receipt)
        crop_name = receipt.get("crop_name")
        if crop_name:
            existing_crops = set(c.lower() for c in merged.get("crops", []))
            if crop_name.lower() not in existing_crops:
                merged.setdefault("crops", []).append(crop_name)

    # --- Data completeness tracker ---
    def _has_success(key: str) -> bool:
        return len(_get_ocr_items(ocr_results, key)) > 0

    merged["data_completeness"] = {
        doc_type: _has_success(doc_type)
        for doc_type in ["aadhaar", "bank_statement", "land_record", "loan_slip", "crop_receipt"]
    }

    return merged
