from pydantic import BaseModel, Field
from typing import Optional


class RiskFlag(BaseModel):
    flag_id: str = Field(..., description="Short identifier e.g. 'HIGH_DTI', 'NO_INSURANCE'")
    severity: str = Field(..., description="critical / warning")
    description: str = Field(..., description="Specific description with numbers")
    recommendation: str = Field(..., description="What to do about it")


class RiskFlags(BaseModel):
    critical_flags: list[RiskFlag] = Field(
        default_factory=list,
        description="Blocking risk flags that may prevent loan approval",
    )
    warning_flags: list[RiskFlag] = Field(
        default_factory=list,
        description="Concerning flags that weaken the application but don't block it",
    )
    risk_score: int = Field(..., description="Overall risk score 0-100 (100 = highest risk)")
    risk_summary: str = Field(..., description="2-sentence plain-language risk summary")
