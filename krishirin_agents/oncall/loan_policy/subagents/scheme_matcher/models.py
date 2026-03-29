from pydantic import BaseModel, Field
from typing import Optional


class SchemeMatch(BaseModel):
    scheme_name: str
    eligibility_met: bool
    interest_rate: str
    subvention: Optional[str] = None
    max_amount: str
    tenure: str
    collateral_rule: str
    application_process: str
    processing_time_days: int
    special_conditions: Optional[str] = None


class SchemeMatches(BaseModel):
    matches: list[SchemeMatch] = Field(..., description="All applicable government schemes")
    best_scheme: str = Field(..., description="Name of the best-fit scheme")
    rationale: str = Field(..., description="Why this scheme is the best fit")
