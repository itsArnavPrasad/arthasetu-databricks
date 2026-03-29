from pydantic import BaseModel, Field
from typing import Optional


class CreditAssessment(BaseModel):
    grameen_score: float = Field(..., description="0-100 Grameen Credit Score")
    risk_category: str = Field(..., description="A (Low) / B (Moderate) / C (Elevated) / D (High)")
    plain_language_explanation: str = Field(
        ..., description="5-line plain-language explanation of the score for a farmer audience"
    )
    top_3_strengths: list[str] = Field(..., description="Top 3 positive factors driving the score")
    top_3_risks: list[str] = Field(..., description="Top 3 risk factors pulling the score down")
    improvement_actions: list[str] = Field(
        ..., description="2 concrete steps the farmer can take to improve their score"
    )
    district_comparison: Optional[str] = Field(
        None, description="How this farmer compares to district averages"
    )
