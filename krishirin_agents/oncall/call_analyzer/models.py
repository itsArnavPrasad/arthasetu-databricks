from pydantic import BaseModel, Field
from typing import Optional


class CallInsights(BaseModel):
    farmer_id: str
    stated_requirement: str = Field(..., description="Farmer's stated loan amount, purpose, urgency")
    concerns: list[str] = Field(default_factory=list, description="Farmer's worries: interest, collateral, repayment")
    additional_info: dict = Field(default_factory=dict, description="New info from call: cattle count, irrigation plans, extra income")
    crop_preferences: list[str] = Field(default_factory=list, description="Crops farmer wants to grow")
    constraints: list[str] = Field(default_factory=list, description="Farmer's constraints: water, labor, land limits")
    acceptance_status: str = Field(..., description="accepted / negotiating / rejected")
    call_summary: str = Field(..., description="3-sentence summary of the call")
