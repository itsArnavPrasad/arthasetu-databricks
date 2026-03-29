import sys, os; _d = os.path.dirname; sys.path.insert(0, _d(_d(_d(_d(os.path.abspath(__file__))))))
from google.adk.agents import LlmAgent

from .prompt import RISK_FLAG_DETECTOR_INSTRUCTION
from krishirin_agents.shared.config import MODEL_FAST

risk_flag_detector_agent = LlmAgent(
    name="risk_flag_detector_agent",
    model=MODEL_FAST,
    description=(
        "Detects financial, agricultural, documentation, and scheme-related risk flags "
        "in the farmer's profile. Returns critical and warning flags with specific numbers."
    ),
    instruction=RISK_FLAG_DETECTOR_INSTRUCTION,
    output_key="risk_flags",
)
