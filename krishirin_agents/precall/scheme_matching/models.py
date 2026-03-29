from pydantic import BaseModel, Field
from typing import Optional


class EligibleScheme(BaseModel):
    scheme_name: str
    eligible: bool
    match_pct: int = Field(..., description="0-100 match percentage")
    missing_requirements: list[str] = Field(default_factory=list)
    estimated_benefit: Optional[str] = None
    action_needed: Optional[str] = None
    source: Optional[str] = Field(None, description="rag/web/rules — how this was determined")


class EligibilityReport(BaseModel):
    eligible_schemes: list[EligibleScheme] = Field(
        ..., description="All evaluated schemes with eligibility status"
    )
    recommended_primary: Optional[str] = Field(
        None, description="Best-fit scheme name for this farmer"
    )
    total_available_benefits: Optional[str] = Field(
        None, description="Estimated total benefits across all eligible schemes"
    )
    key_findings: str = Field(
        ..., description="2-3 sentence summary of scheme eligibility findings"
    )
