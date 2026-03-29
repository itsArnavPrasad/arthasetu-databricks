import sys, os
_d = os.path.dirname
sys.path.insert(0, _d(_d(_d(_d(_d(_d(os.path.abspath(__file__))))))))

from google.adk.agents import LlmAgent
from .prompt import SCHEME_WEB_INSTRUCTION
from krishirin_agents.shared.config import MODEL_FAST

scheme_web_agent = LlmAgent(
    name="scheme_web_agent",
    model=MODEL_FAST,
    description="Provides latest government scheme updates and state-specific schemes.",
    instruction=SCHEME_WEB_INSTRUCTION,
    output_key="scheme_web_results",
)
