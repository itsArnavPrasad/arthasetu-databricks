from pydantic import BaseModel, Field
from typing import Optional


class FarmerProfile(BaseModel):
    farmer_id: str
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    land_holding_acres: Optional[float] = None
    land_type: Optional[str] = Field(None, description="owned/leased/shared")
    irrigation_type: Optional[str] = Field(None, description="irrigated/rainfed/mixed")
    crops: Optional[list[str]] = None
    existing_loans: Optional[list[dict]] = None
    govt_schemes: Optional[list[str]] = None
    bank_summary: Optional[dict] = Field(None, description="Monthly income/expense aggregates")
    aadhaar_last4: Optional[str] = None
    documents_provided: Optional[list[str]] = None


class MLScores(BaseModel):
    farmer_id: str
    grameen_score: Optional[float] = Field(None, description="0-100 composite score")
    risk_category: Optional[str] = Field(None, description="A/B/C/D")
    repayment_prob: Optional[float] = None
    risk_cluster: Optional[int] = None
    predicted_capacity: Optional[float] = Field(None, description="Max serviceable loan amount in INR")
    top_positive_factors: Optional[list[str]] = None
    top_negative_factors: Optional[list[str]] = None


class DistrictData(BaseModel):
    district: Optional[str] = None
    avg_yield_per_hectare: Optional[float] = None
    irrigation_pct: Optional[float] = None
    avg_rainfall_mm: Optional[float] = None
    rainfall_variability: Optional[float] = None
    crop_failure_rate: Optional[float] = None
    dominant_crops: Optional[list[str]] = None
    soil_type: Optional[str] = None


class WeatherData(BaseModel):
    district: Optional[str] = None
    current: Optional[dict] = None
    forecast: Optional[list[dict]] = None
    error: Optional[str] = None


class FarmerContext(BaseModel):
    farmer_id: str
    profile: Optional[FarmerProfile] = None
    ml_scores: Optional[MLScores] = None
    district_data: Optional[DistrictData] = None
    crop_calendar: Optional[list[dict]] = None
    msp_prices: Optional[list[dict]] = None
    weather: Optional[WeatherData] = None
