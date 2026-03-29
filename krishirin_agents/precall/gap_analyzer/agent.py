import sys, os; _d = os.path.dirname; sys.path.insert(0, _d(_d(_d(_d(os.path.abspath(__file__))))))
from google.adk.agents import LlmAgent

from .prompt import GAP_ANALYZER_INSTRUCTION
from .tools import profile_validator
from krishirin_agents.shared.config import MODEL_FAST

gap_analyzer_agent = LlmAgent(
    name="gap_analyzer_agent",
    model=MODEL_FAST,
    description=(
        "Identifies critical gaps, warnings, and improvement suggestions in the farmer's "
        "loan application by combining rule-based validation with AI analysis."
    ),
    instruction=GAP_ANALYZER_INSTRUCTION,
    tools=[profile_validator],
    output_key="gap_analysis",
)
