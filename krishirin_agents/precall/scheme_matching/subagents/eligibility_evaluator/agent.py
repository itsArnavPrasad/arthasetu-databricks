import sys, os
_d = os.path.dirname
sys.path.insert(0, _d(_d(_d(_d(_d(_d(os.path.abspath(__file__))))))))

from google.adk.agents import LlmAgent
from .prompt import ELIGIBILITY_EVALUATOR_INSTRUCTION
from krishirin_agents.shared.config import MODEL_FAST

eligibility_evaluator_agent = LlmAgent(
    name="eligibility_evaluator_agent",
    model=MODEL_FAST,
    description="Evaluates farmer eligibility for KCC, PM-KISAN, PMFBY, MUDRA, and state schemes.",
    instruction=ELIGIBILITY_EVALUATOR_INSTRUCTION,
    output_key="eligibility_evaluation",
)
