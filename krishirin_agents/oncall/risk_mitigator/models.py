from pydantic import BaseModel, Field


class RiskAction(BaseModel):
    risk: str = Field(..., description="What the risk is")
    mitigation: str = Field(..., description="Specific action to mitigate it")
    cost: str = Field(..., description="Cost of mitigation (₹ or 'free')")
    priority: str = Field(..., description="high / medium / low")


class RiskPlan(BaseModel):
    actions: list[RiskAction]
    insurance_plan: str = Field(..., description="PMFBY enrollment details with premium calculation")
    savings_buffer_target: str = Field(..., description="How much to save as EMI buffer")
    documentation_checklist: list[str] = Field(..., description="Documents needed to complete application")
    overall_risk_level: str = Field(..., description="low / moderate / elevated after mitigation")
