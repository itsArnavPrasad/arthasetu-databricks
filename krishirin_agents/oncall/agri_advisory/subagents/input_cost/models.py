from pydantic import BaseModel, Field
from typing import Optional


class CropCost(BaseModel):
    crop: str
    area_acres: float
    seeds_cost: float
    fertilizer_cost: float
    pesticide_cost: float
    labor_cost: float
    irrigation_cost: float
    total_cost: float
    reduction_tips: list[str] = Field(..., description="Specific cost reduction advice for this crop")
    reduced_total: float = Field(..., description="Estimated cost after applying reduction tips")
    savings_pct: float


class InputCosts(BaseModel):
    crop_costs: list[CropCost]
    total_cultivation_cost: float
    total_after_reduction: float
    overall_savings_pct: float
    key_savings_opportunities: list[str] = Field(..., description="Top 3 biggest savings opportunities")
