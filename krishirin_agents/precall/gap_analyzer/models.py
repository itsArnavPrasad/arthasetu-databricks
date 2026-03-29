from pydantic import BaseModel, Field
from typing import Optional


class Gap(BaseModel):
    gap_id: str = Field(..., description="Short identifier e.g. 'MISSING_LAND_RECORD'")
    severity: str = Field(..., description="critical / warning / suggestion")
    description: str = Field(..., description="Specific description with actionable detail")
    action: str = Field(..., description="Exact step the farmer should take to fix this")


class GapAnalysis(BaseModel):
    critical_gaps: list[Gap] = Field(
        default_factory=list,
        description="Blocking issues that prevent loan approval",
    )
    warnings: list[Gap] = Field(
        default_factory=list,
        description="Issues that weaken the application",
    )
    improvement_suggestions: list[Gap] = Field(
        default_factory=list,
        description="Actionable steps to strengthen the application",
    )
    application_ready: bool = Field(
        ..., description="True if no critical gaps exist"
    )
    readiness_score: int = Field(
        ..., description="0-100 overall readiness score"
    )
