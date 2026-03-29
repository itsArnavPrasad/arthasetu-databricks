from pydantic import BaseModel, Field
from typing import Optional


class AgriAdvisory(BaseModel):
    land_assessment: str
    sowing_plan: dict = Field(..., description="Crop allocations with yield and revenue")
    input_cost_plan: dict = Field(..., description="Per-crop costs and reduction strategies")
    weather_guidance: dict = Field(..., description="Weather-aware timing for farming operations")
    market_strategy: dict = Field(..., description="Selling strategy per crop")
    income_diversification: list[str] = Field(..., description="Allied income opportunities with ₹ estimates")
    total_expected_revenue: float
    total_expected_costs: float
    net_expected_income: float
    advisory_summary: str = Field(..., description="3-sentence overall agricultural recommendation")
