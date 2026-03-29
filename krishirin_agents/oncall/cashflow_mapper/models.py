from pydantic import BaseModel, Field


class MonthProjection(BaseModel):
    month: str = Field(..., description="e.g., 'April 2026'")
    farm_income: float = Field(..., description="Expected farm income this month in ₹")
    allied_income: float = Field(..., description="Dairy, poultry, MGNREGA etc in ₹")
    total_income: float
    loan_emi: float
    surplus_or_deficit: float = Field(..., description="total_income - loan_emi")
    notes: str = Field(..., description="Key event: 'Soybean harvest', 'Lean month', etc.")


class CashFlowMap(BaseModel):
    monthly_projections: list[MonthProjection] = Field(..., description="12-month projection")
    surplus_months: list[str]
    deficit_months: list[str]
    buffer_needed: float = Field(..., description="₹ needed to cover all deficit months")
    buffer_strategy: str = Field(..., description="How to build the buffer")
    lump_sum_repayment_months: list[str] = Field(..., description="Best months for large repayments")
    annual_summary: str = Field(..., description="Total income vs total loan obligation for the year")
