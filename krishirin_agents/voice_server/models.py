from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional


class CallPhase(str, Enum):
    CLARIFICATION = "clarification"
    CONFIRMATION = "confirmation"
    SMALL_TALK = "small_talk"
    RESULTS = "results"
    ENDED = "ended"


class AgentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentResult(BaseModel):
    agent_name: str
    status: AgentStatus
    title: str = ""
    summary: str = ""
    result: Optional[dict] = None
    icon: str = ""


class CallState(BaseModel):
    farmer_id: str
    session_id: str = ""
    phase: CallPhase = CallPhase.CLARIFICATION
    transcript: list[dict] = Field(default_factory=list)
    questions_asked: list[str] = Field(default_factory=list)
    questions_answered: int = 0
    total_questions: int = 5
    analysis_triggered: bool = False
    analysis_complete: bool = False
    agent_results: dict[str, AgentResult] = Field(default_factory=dict)


# Agent display metadata — icon + title for frontend cards (7 visible agents)
AGENT_DISPLAY = {
    "call_insights": AgentResult(
        agent_name="call_insights", status=AgentStatus.PENDING,
        title="Call Analysis", icon="📞", summary="Analyzing conversation..."
    ),
    "scheme_matches": AgentResult(
        agent_name="scheme_matches", status=AgentStatus.PENDING,
        title="Scheme Matching", icon="📋", summary="Matching government schemes..."
    ),
    "bank_products": AgentResult(
        agent_name="bank_products", status=AgentStatus.PENDING,
        title="Bank Comparison", icon="🏧", summary="Comparing bank products..."
    ),
    "optimal_policy": AgentResult(
        agent_name="optimal_policy", status=AgentStatus.PENDING,
        title="Loan Policy", icon="🏦", summary="Optimizing loan terms..."
    ),
    "agri_advisory": AgentResult(
        agent_name="agri_advisory", status=AgentStatus.PENDING,
        title="Agricultural Advisory", icon="🌾", summary="Planning crop strategy..."
    ),
    "risk_plan": AgentResult(
        agent_name="risk_plan", status=AgentStatus.PENDING,
        title="Risk Mitigation", icon="🛡️", summary="Analyzing risks..."
    ),
    "cashflow_map": AgentResult(
        agent_name="cashflow_map", status=AgentStatus.PENDING,
        title="Cashflow Map", icon="📊", summary="Mapping 12-month cashflow..."
    ),
}
