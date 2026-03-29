from pydantic import BaseModel, Field
from typing import Optional


class RepaymentInstallment(BaseModel):
    month: str = Field(..., description="Month name e.g. 'November 2026'")
    amount: float = Field(..., description="Installment amount in INR")
    reason: str = Field(..., description="Why this month, e.g. 'Post-Kharif harvest'")


class LoanStrategy(BaseModel):
    recommended_product: str = Field(..., description="KCC / Term Loan / MUDRA Shishu / MUDRA Kishore")
    amount: float = Field(..., description="Recommended loan amount in INR")
    tenure_months: int = Field(..., description="Loan tenure in months")
    interest_rate_nominal: float = Field(..., description="Nominal interest rate %")
    interest_rate_effective: float = Field(..., description="Effective rate after subvention %")
    collateral_requirement: str = Field(..., description="What collateral is needed, if any")
    collateral_waiver_applicable: bool
    repayment_schedule: list[RepaymentInstallment] = Field(
        ..., description="Repayment installments aligned to harvest seasons"
    )
    monthly_emi_equivalent: float = Field(..., description="Monthly EMI equivalent in INR")
    total_repayment: float = Field(..., description="Total amount to be repaid including interest")
    rationale: str = Field(..., description="2-sentence justification for this strategy")
    alternative_option: Optional[str] = Field(
        None, description="Alternative loan option if applicable"
    )
    warnings: list[str] = Field(
        default_factory=list, description="Warnings if amount exceeds capacity or other concerns"
    )
