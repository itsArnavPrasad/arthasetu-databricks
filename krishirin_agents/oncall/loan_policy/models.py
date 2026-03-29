from pydantic import BaseModel, Field
from typing import Optional


class OptimalPolicy(BaseModel):
    recommended_scheme: str = Field(..., description="Best govt scheme (KCC/MUDRA/etc)")
    recommended_bank: str = Field(..., description="Best bank for this farmer")
    product_name: str = Field(..., description="Specific bank product name")
    final_amount: float = Field(..., description="Optimized loan amount in ₹")
    final_rate_nominal: float = Field(..., description="Nominal interest rate %")
    final_rate_effective: float = Field(..., description="Effective rate after all subventions %")
    final_tenure_months: int
    collateral_plan: str = Field(..., description="Collateral strategy (waived/hypothecation/mortgage)")
    application_steps: list[str] = Field(..., description="Step-by-step application process")
    documents_needed: list[str] = Field(..., description="Documents to submit")
    estimated_processing_days: int
    total_cost_of_loan: float = Field(..., description="Total repayment including interest in ₹")
    monthly_emi_equivalent: float
    rationale: str = Field(..., description="Why this is the best option for this farmer")
