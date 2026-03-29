import sys, os
_d = os.path.dirname
sys.path.insert(0, _d(_d(_d(_d(os.path.abspath(__file__))))))

from google.adk.agents import LlmAgent
from .prompt import CALL_ANALYZER_INSTRUCTION
from krishirin_agents.shared.config import MODEL_FAST

call_analyzer_agent = LlmAgent(
    name="call_analyzer_agent",
    model=MODEL_FAST,
    description="Analyzes voice call transcript to extract farmer preferences, concerns, and acceptance status.",
    instruction=CALL_ANALYZER_INSTRUCTION,
    output_key="call_insights",
)
