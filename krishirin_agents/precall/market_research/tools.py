"""
ML model tools for the market_research agent.

Provides two tools that run local crop prediction models:
1. predict_crop_prices — LinearRegression on seasonal price data (Kharif + Rabi)
2. predict_crop_yields — LinearRegression on district-level historical yield data

Both models run inference locally (no Databricks). They load static CSV reference
data and fit simple linear regressions, same logic as the example scripts.
"""

import json
import logging
import os

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from google.adk.tools.tool_context import ToolContext

logger = logging.getLogger(__name__)

# Data paths — relative to the project root
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
SEASONAL_PRICE_CSV = os.path.join(_PROJECT_ROOT, "arthasetu-databricks", "raw_data", "seasonalPrice", "Season_Price_Arrival_5_years.csv")
CROP_DISTRICT_CSV = os.path.join(_PROJECT_ROOT, "arthasetu-databricks", "raw_data", "cropData", "CropDistrictLevelData.csv")


def predict_crop_prices(tool_context: ToolContext, crops_json: str) -> str:
    """Predict Kharif and Rabi season crop prices for the upcoming year using linear regression.

    Loads 5-year historical seasonal price data and fits a linear trend per commodity
    to forecast the next year's prices.

    Args:
        crops_json: JSON string — either a list of crop names like '["soybean", "wheat"]'
                    or a JSON object with a 'crops' key.

    Returns:
        JSON string with predicted prices per crop for both Kharif and Rabi seasons,
        including trend direction and confidence.
    """
    # Parse crop list
    try:
        data = json.loads(crops_json)
        if isinstance(data, list):
            crop_names = data
        elif isinstance(data, dict):
            crop_names = data.get("crops", [])
        else:
            crop_names = []
    except json.JSONDecodeError:
        crop_names = [c.strip() for c in crops_json.split(",") if c.strip()]

    if not crop_names:
        return json.dumps({"status": "error", "error": "No crop names provided"})

    # Load data
    if not os.path.exists(SEASONAL_PRICE_CSV):
        return json.dumps({
            "status": "error",
            "error": f"Seasonal price data not found at {SEASONAL_PRICE_CSV}",
        })

    try:
        df = pd.read_csv(SEASONAL_PRICE_CSV)
    except Exception as e:
        return json.dumps({"status": "error", "error": f"Failed to load price data: {e}"})

    # Build time index
    unique_years = sorted(df["Year"].unique())
    year_map = {y: i + 1 for i, y in enumerate(unique_years)}
    df["Time_Index"] = df["Year"].map(year_map)
    target_time_index = len(unique_years) + 1
    target_year = _next_year_str(unique_years[-1]) if unique_years else "2026-27"

    results = []
    crop_names_lower = [c.lower().strip() for c in crop_names]

    def _fuzzy_match(commodity_lower: str, crop_list: list[str]) -> bool:
        """Match crop names flexibly: soybean↔soyabean, gram↔chana, paddy↔rice etc."""
        for cn in crop_list:
            if cn in commodity_lower or commodity_lower in cn:
                return True
            # Check if first 3+ chars overlap (soy↔soya, ground↔groundnut)
            min_len = min(len(cn), len(commodity_lower))
            prefix = min(min_len, max(3, min_len // 2))
            if cn[:prefix] == commodity_lower[:prefix]:
                return True
        return False

    for commodity in df["Commodity"].unique():
        # Check if this commodity matches any requested crop
        commodity_lower = commodity.lower()
        # Also strip parenthetical alternate names for matching
        commodity_base = commodity_lower.split("(")[0].strip()
        matched = _fuzzy_match(commodity_base, crop_names_lower) or _fuzzy_match(commodity_lower, crop_names_lower)
        if not matched:
            continue

        comp_df = df[df["Commodity"] == commodity].sort_values("Time_Index")

        prediction = {"commodity": commodity}

        # Kharif prediction
        kharif_df = comp_df.dropna(subset=["Kharif_Season_Price_Rs_Per_Quintal"])
        if len(kharif_df) >= 2:
            X = kharif_df[["Time_Index"]].values
            y = kharif_df["Kharif_Season_Price_Rs_Per_Quintal"].values
            lr = LinearRegression().fit(X, y)
            pred = max(lr.predict([[target_time_index]])[0], 0)
            slope = lr.coef_[0]
            prediction["kharif_predicted_price"] = round(pred, 2)
            prediction["kharif_trend"] = "increasing" if slope > 0 else ("decreasing" if slope < 0 else "flat")
            prediction["kharif_last_known_price"] = round(y[-1], 2)
        else:
            prediction["kharif_predicted_price"] = None
            prediction["kharif_trend"] = "insufficient_data"

        # Rabi prediction
        rabi_df = comp_df.dropna(subset=["Rabi_Season_Price_Rs_Per_Quintal"])
        if len(rabi_df) >= 2:
            X = rabi_df[["Time_Index"]].values
            y = rabi_df["Rabi_Season_Price_Rs_Per_Quintal"].values
            lr = LinearRegression().fit(X, y)
            pred = max(lr.predict([[target_time_index]])[0], 0)
            slope = lr.coef_[0]
            prediction["rabi_predicted_price"] = round(pred, 2)
            prediction["rabi_trend"] = "increasing" if slope > 0 else ("decreasing" if slope < 0 else "flat")
            prediction["rabi_last_known_price"] = round(y[-1], 2)
        else:
            prediction["rabi_predicted_price"] = None
            prediction["rabi_trend"] = "insufficient_data"

        # MSP for comparison
        msp = comp_df["MSP_Rs_Per_Quintal"].dropna()
        if not msp.empty:
            prediction["current_msp"] = round(msp.iloc[-1], 2)

        results.append(prediction)

    return json.dumps({
        "status": "success",
        "target_year": target_year,
        "predictions": results,
        "crops_requested": crop_names,
        "crops_found": len(results),
        "note": "Prices in Rs per Quintal. Predictions based on 5-year linear trend.",
    })


def predict_crop_yields(tool_context: ToolContext, district: str, crops_json: str) -> str:
    """Predict crop yields for a specific district using historical linear trends.

    Loads district-level crop yield data (ICRISAT format) and fits linear regression
    per crop to forecast expected yields.

    Args:
        district: District name (e.g., "Nashik", "Wardha").
        crops_json: JSON string — list of crop names like '["soybean", "wheat"]'
                    or a JSON object with a 'crops' key.

    Returns:
        JSON string with predicted yields per crop for the district.
    """
    # Parse crop list
    try:
        data = json.loads(crops_json)
        if isinstance(data, list):
            crop_names = data
        elif isinstance(data, dict):
            crop_names = data.get("crops", [])
        else:
            crop_names = []
    except json.JSONDecodeError:
        crop_names = [c.strip() for c in crops_json.split(",") if c.strip()]

    if not os.path.exists(CROP_DISTRICT_CSV):
        return json.dumps({
            "status": "error",
            "error": f"Crop district data not found at {CROP_DISTRICT_CSV}",
        })

    try:
        df = pd.read_csv(CROP_DISTRICT_CSV)
    except Exception as e:
        return json.dumps({"status": "error", "error": f"Failed to load crop data: {e}"})

    # Filter for district (case-insensitive, with fuzzy fallback)
    district_clean = district.lower().strip()
    dist_df = df[df["Dist Name"].str.lower() == district_clean]
    if dist_df.empty:
        # Fuzzy match: check if district name starts with or contains the input
        all_districts = df["Dist Name"].unique()
        for d in all_districts:
            d_lower = d.lower()
            # Match Nashik↔Nasik, Aurangabad↔Aurangabad etc.
            if (d_lower.startswith(district_clean[:3]) and
                abs(len(d_lower) - len(district_clean)) <= 2):
                dist_df = df[df["Dist Name"] == d]
                if not dist_df.empty:
                    break
    if dist_df.empty:
        return json.dumps({
            "status": "not_found",
            "error": f"No data for district '{district}'",
            "available_districts_sample": df["Dist Name"].unique()[:20].tolist(),
        })

    # Use recent years for trend (last 5 years of available data)
    max_year = dist_df["Year"].max()
    dist_df = dist_df[dist_df["Year"] >= max_year - 4]

    # Extract yield columns
    yield_cols = [c for c in df.columns if "YIELD (Kg per ha)" in c]

    # Map requested crop names to column names (fuzzy matching)
    crop_col_map = {}
    for crop in crop_names:
        crop_lower = crop.lower().strip()
        for col in yield_cols:
            col_crop = col.replace(" YIELD (Kg per ha)", "").lower().strip()
            # Exact or substring match
            if crop_lower in col_crop or col_crop in crop_lower:
                crop_col_map[crop] = col
                break
            # Prefix match (soy→soyabean, ground→groundnut)
            prefix = min(len(crop_lower), len(col_crop), max(3, len(crop_lower) // 2))
            if crop_lower[:prefix] == col_crop[:prefix]:
                crop_col_map[crop] = col
                break

    target_year = max_year + 1
    results = []

    for crop_name, col_name in crop_col_map.items():
        crop_data = dist_df[["Year", col_name]].copy()
        crop_data[col_name] = crop_data[col_name].replace(-1.0, np.nan)
        crop_data = crop_data.dropna()

        if len(crop_data) >= 2:
            X = crop_data[["Year"]].values
            y = crop_data[col_name].values
            lr = LinearRegression().fit(X, y)
            pred = max(lr.predict([[target_year]])[0], 0)
            slope = lr.coef_[0]

            results.append({
                "crop": crop_name,
                "predicted_yield_kg_per_ha": round(pred, 2),
                "historical_avg_yield": round(y.mean(), 2),
                "trend": "increasing" if slope > 0 else ("decreasing" if slope < 0 else "flat"),
                "trend_slope": round(slope, 2),
                "data_points": len(crop_data),
            })
        else:
            results.append({
                "crop": crop_name,
                "predicted_yield_kg_per_ha": None,
                "note": "Insufficient data for prediction",
            })

    # Also report crops not found
    not_found = [c for c in crop_names if c not in crop_col_map]

    return json.dumps({
        "status": "success",
        "district": district,
        "target_year": int(target_year),
        "predictions": results,
        "crops_not_found": not_found,
        "note": "Yields in Kg per hectare. Based on linear trend of recent 5 years of ICRISAT data.",
    })


def _next_year_str(current: str) -> str:
    """Convert '2025-26' to '2026-27'."""
    try:
        parts = current.split("-")
        start = int(parts[0]) + 1
        end = int(parts[1]) + 1
        return f"{start}-{end:02d}"
    except (ValueError, IndexError):
        return "2026-27"
