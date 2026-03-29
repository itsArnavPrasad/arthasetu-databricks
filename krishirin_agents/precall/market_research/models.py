from pydantic import BaseModel, Field
from typing import Optional


class CropMarketPrice(BaseModel):
    crop: str
    current_mandi_price: Optional[str] = None
    msp_price: Optional[str] = None
    price_trend: Optional[str] = Field(None, description="rising/stable/falling")
    source: Optional[str] = None


class MarketResearch(BaseModel):
    current_market_prices: list[CropMarketPrice] = Field(
        default_factory=list, description="Current mandi prices for farmer's crops"
    )
    disease_alerts: list[str] = Field(
        default_factory=list, description="Current crop disease or pest alerts for the district"
    )
    weather_advisory: Optional[str] = Field(
        None, description="Agricultural weather advisory for the region"
    )
    scheme_updates: list[str] = Field(
        default_factory=list, description="Recent government scheme announcements or changes"
    )
    market_trend_summary: str = Field(
        ..., description="2-3 sentence summary of current market conditions for the farmer"
    )
