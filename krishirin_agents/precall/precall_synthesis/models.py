from pydantic import BaseModel, Field
from typing import Optional


class PreCallAnalysis(BaseModel):
    farmer_id: str
    generated_at: str = Field(..., description="ISO-8601 timestamp")

    score_summary: dict = Field(
        ..., description="Grameen score, risk category, key strengths and risks"
    )
    risk_flags: dict = Field(
        ..., description="Critical and warning flags with risk score"
    )
    eligible_schemes: dict = Field(
        ..., description="Eligible schemes with recommended primary and benefits"
    )
    gaps_to_fix: dict = Field(
        ..., description="Critical gaps, warnings, and improvement suggestions"
    )
    loan_strategy: dict = Field(
        ..., description="Recommended loan product, amount, interest, repayment schedule"
    )
    market_insights: dict = Field(
        ..., description="Current market prices, disease alerts, scheme updates"
    )
    executive_summary: str = Field(
        ..., description="5-sentence overall recommendation for bank operator"
    )
    voice_agent_briefing: str = Field(
        ...,
        description=(
            "Condensed briefing for the voice agent system prompt. "
            "Key numbers, simple language, Hindi-translatable. "
            "Covers: score, loan terms, repayment plan, key advice points."
        ),
    )
