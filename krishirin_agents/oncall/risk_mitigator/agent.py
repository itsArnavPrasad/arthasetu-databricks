import sys, os
_d = os.path.dirname
sys.path.insert(0, _d(_d(_d(_d(os.path.abspath(__file__))))))

from google.adk.agents import LlmAgent
from .prompt import RISK_MITIGATOR_INSTRUCTION
from krishirin_agents.shared.config import MODEL_FAST

risk_mitigator_agent = LlmAgent(
    name="risk_mitigator_agent",
    model=MODEL_FAST,
    description="Creates actionable risk mitigation plan: insurance, diversification, buffers, documentation.",
    instruction=RISK_MITIGATOR_INSTRUCTION,
    output_key="risk_plan",
)
