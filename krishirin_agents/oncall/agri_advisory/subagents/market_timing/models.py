from pydantic import BaseModel, Field
from typing import Optional


class WeatherGuidance(BaseModel):
    sowing_timing: str = Field(..., description="When to sow based on weather/monsoon")
    fertilizer_timing: str = Field(..., description="When to apply, avoid before rain")
    spray_timing: str = Field(..., description="When to spray pesticide, avoid before rain")
    irrigation_timing: str = Field(..., description="When to irrigate, skip if rain forecast")
    early_warnings: list[str] = Field(default_factory=list)


class CropSellingStrategy(BaseModel):
    crop: str
    msp_price: Optional[str] = None
    msp_procurement_window: Optional[str] = None
    mandi_price_pattern: str = Field(..., description="Price dip at harvest, recovery in 1-2 months")
    storage_advice: str = Field(..., description="Can store or must sell quickly")
    selling_recommendation: str = Field(..., description="Phased selling strategy")


class MarketStrategy(BaseModel):
    weather_guidance: WeatherGuidance
    selling_strategies: list[CropSellingStrategy]
    fpo_linkage: Optional[str] = Field(None, description="FPO recommendation if available in district")
    key_market_insight: str = Field(..., description="Most important market advice for this farmer")
