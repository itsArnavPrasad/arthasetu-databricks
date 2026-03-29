import sys, os; _d = os.path.dirname; sys.path.insert(0, _d(_d(_d(_d(os.path.abspath(__file__))))))
import json
import logging
from google.adk.tools.tool_context import ToolContext
from krishirin_agents.shared.config import USE_SAMPLE_DATA
from krishirin_agents.shared.sample_data import (
    SAMPLE_FARMER_PROFILE,
    SAMPLE_ML_SCORES,
    SAMPLE_DISTRICT_DATA,
    SAMPLE_CROP_CALENDAR,
    SAMPLE_MSP_PRICES,
    SAMPLE_WEATHER,
)

logger = logging.getLogger(__name__)


def load_farmer_profile(tool_context: ToolContext, farmer_id: str) -> dict:
    """Load farmer profile — prefers OCR-extracted data from session state, falls back to Delta table."""
    logger.info(f"Loading farmer profile for {farmer_id}")

    # Check if OCR-extracted data is available in session state
    ocr_data = tool_context.state.get("ocr_farmer_data")
    if ocr_data and isinstance(ocr_data, dict) and ocr_data.get("name"):
        logger.info(f"Using OCR-extracted farmer profile for {farmer_id}")
        # Enrich with farmer_id
        profile = {**ocr_data, "farmer_id": farmer_id}
        return {"status": "success", "source": "ocr", "data": profile}

    if USE_SAMPLE_DATA:
        return {"status": "success", "source": "sample", "data": SAMPLE_FARMER_PROFILE}
    from krishirin_agents.shared import delta_client
    from krishirin_agents.shared.config import TABLE_FARMER_PROFILE
    row = delta_client.query_one(
        f"SELECT * FROM {TABLE_FARMER_PROFILE} WHERE farmer_id = '{farmer_id}'"
    )
    if row is None:
        return {"status": "error", "message": f"Farmer {farmer_id} not found"}
    return {"status": "success", "source": "delta", "data": row}


def load_ml_scores(tool_context: ToolContext, farmer_id: str) -> dict:
    """Load pre-computed ML scores from scored_profiles Delta table.

    NOTE: With the new pipeline, ML scoring is done by the score_explainer agent
    using Databricks serving endpoints. This tool now returns a placeholder if
    OCR data is present (scores will be computed by score_explainer agent).
    Falls back to Delta table or sample data for legacy flow.
    """
    logger.info(f"Loading ML scores for {farmer_id}")

    # If OCR data exists, ML scores will be computed by score_explainer agent
    ocr_data = tool_context.state.get("ocr_farmer_data")
    if ocr_data and isinstance(ocr_data, dict) and ocr_data.get("name"):
        return {
            "status": "pending",
            "message": "ML scores will be computed by score_explainer agent using OCR-extracted data.",
            "data": {
                "farmer_id": farmer_id,
                "grameen_score": None,
                "risk_category": None,
                "repayment_prob": None,
                "risk_cluster": None,
                "predicted_capacity": None,
                "scoring_status": "pending_score_explainer",
                "top_positive_factors": [],
                "top_negative_factors": [],
            },
        }

    if USE_SAMPLE_DATA:
        return {"status": "success", "source": "sample", "data": SAMPLE_ML_SCORES}
    from krishirin_agents.shared import delta_client
    from krishirin_agents.shared.config import TABLE_SCORED_PROFILES
    row = delta_client.query_one(
        f"SELECT * FROM {TABLE_SCORED_PROFILES} WHERE farmer_id = '{farmer_id}'"
    )
    if row is None:
        return {"status": "error", "message": f"ML scores not found for {farmer_id}"}
    return {"status": "success", "source": "delta", "data": row}


def load_district_data(tool_context: ToolContext, district: str) -> dict:
    """Load district agricultural features from silver_district_features Delta table."""
    logger.info(f"Loading district data for {district}")
    if USE_SAMPLE_DATA:
        return {"status": "success", "data": SAMPLE_DISTRICT_DATA}
    from krishirin_agents.shared import delta_client
    from krishirin_agents.shared.config import TABLE_DISTRICT_FEATURES
    row = delta_client.query_one(
        f"SELECT * FROM {TABLE_DISTRICT_FEATURES} WHERE LOWER(district) = LOWER('{district}')"
    )
    if row is None:
        return {"status": "not_found", "message": f"No district data for {district}", "data": {}}
    return {"status": "success", "data": row}


def load_crop_calendar(tool_context: ToolContext, district: str, crops: str) -> dict:
    """Load sowing/harvest calendar for farmer's crops and zone.

    Args:
        district: Farmer's district name
        crops: Comma-separated crop names (e.g., "soybean,cotton,wheat")
    """
    logger.info(f"Loading crop calendar for {district}, crops: {crops}")
    if USE_SAMPLE_DATA:
        crop_list = [c.strip().lower() for c in crops.split(",")]
        filtered = [c for c in SAMPLE_CROP_CALENDAR if c["crop"].lower() in crop_list]
        return {"status": "success", "data": filtered if filtered else SAMPLE_CROP_CALENDAR}
    from krishirin_agents.shared import delta_client
    from krishirin_agents.shared.config import TABLE_CROP_CALENDAR
    crop_list = [c.strip().lower() for c in crops.split(",")]
    placeholders = ",".join(f"'{c}'" for c in crop_list)
    rows = delta_client.query_all(
        f"SELECT * FROM {TABLE_CROP_CALENDAR} WHERE LOWER(crop) IN ({placeholders})"
    )
    return {"status": "success", "data": rows}


def load_msp_prices(tool_context: ToolContext) -> dict:
    """Load current MSP prices for all crops."""
    logger.info("Loading MSP prices")
    if USE_SAMPLE_DATA:
        return {"status": "success", "data": SAMPLE_MSP_PRICES}
    from krishirin_agents.shared import delta_client
    from krishirin_agents.shared.config import TABLE_MSP_PRICES
    rows = delta_client.query_all(f"SELECT * FROM {TABLE_MSP_PRICES} ORDER BY crop")
    return {"status": "success", "data": rows}


def fetch_weather_data(tool_context: ToolContext, district: str) -> dict:
    """Fetch current weather, 7-day forecast, and 30-day historical weather for farmer's district.

    Combines OpenWeatherMap (current + forecast) with NASA POWER API (30-day historical).
    """
    logger.info(f"Fetching weather for {district}")
    if USE_SAMPLE_DATA:
        return {"status": "success", "data": SAMPLE_WEATHER}
    from krishirin_agents.shared.weather_client import fetch_complete_weather
    weather = fetch_complete_weather(district)
    return {"status": "success", "data": weather}
