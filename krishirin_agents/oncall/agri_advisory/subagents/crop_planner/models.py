from pydantic import BaseModel, Field
from typing import Optional


class CropAllocation(BaseModel):
    crop: str
    season: str = Field(..., description="Kharif/Rabi/Zaid")
    area_acres: float
    expected_yield_quintals: float
    expected_revenue: float = Field(..., description="yield × MSP in ₹")
    sowing_window: str = Field(..., description="e.g., 'June 15 - July 15'")
    harvest_window: str
    water_requirement: str = Field(..., description="e.g., '450mm' or 'low/medium/high'")


class CropPlan(BaseModel):
    land_assessment: str = Field(..., description="2-3 sentence land and district summary")
    allocations: list[CropAllocation]
    total_annual_revenue: float = Field(..., description="Sum of all crop revenues in ₹")
    diversification_note: str = Field(..., description="Why this mix reduces risk")
