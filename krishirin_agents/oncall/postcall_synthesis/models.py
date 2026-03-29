from pydantic import BaseModel, Field


class PostCallAnalysis(BaseModel):
    farmer_id: str
    generated_at: str = Field(..., description="ISO-8601 timestamp")
    policy_recommendation: dict = Field(..., description="Best scheme + bank + exact terms")
    application_checklist: dict = Field(..., description="Documents, steps, timeline to apply")
    agri_advisory: dict = Field(..., description="Complete 7-section agricultural plan")
    cashflow_projection: dict = Field(..., description="12-month income vs repayment map")
    risk_mitigation: dict = Field(..., description="Insurance + diversification + buffer plan")
    farmer_summary: str = Field(
        ...,
        description="Simple Hindi-translatable summary of everything the farmer needs to know and do. Under 300 words.",
    )
