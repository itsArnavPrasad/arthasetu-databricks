from pydantic import BaseModel, Field
from typing import Optional


class SchemeEligibility(BaseModel):
    scheme_name: str
    eligible: bool
    match_pct: int = Field(..., description="0-100 match percentage")
    met_criteria: list[str] = Field(default_factory=list, description="Criteria the farmer meets")
    missing_criteria: list[str] = Field(
        default_factory=list, description="Criteria the farmer does NOT meet"
    )
    estimated_benefit: Optional[str] = Field(
        None, description="Estimated benefit if eligible, e.g. 'Loan up to ₹3L at 4% effective'"
    )
    action_needed: Optional[str] = Field(
        None, description="What the farmer needs to do to apply or become eligible"
    )


class EligibilityEvaluation(BaseModel):
    evaluations: list[SchemeEligibility] = Field(
        ..., description="Eligibility assessment for each scheme"
    )
    best_fit_scheme: Optional[str] = Field(
        None, description="Name of the scheme that best fits this farmer"
    )
