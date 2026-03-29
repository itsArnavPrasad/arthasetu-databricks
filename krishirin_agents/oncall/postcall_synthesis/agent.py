import sys, os
_d = os.path.dirname
sys.path.insert(0, _d(_d(_d(_d(os.path.abspath(__file__))))))

from google.adk.agents import LlmAgent
from .prompt import POSTCALL_SYNTHESIS_INSTRUCTION
from .tools import write_postcall_to_delta
from krishirin_agents.shared.config import MODEL_FAST

postcall_synthesis_agent = LlmAgent(
    name="postcall_synthesis_agent",
    model=MODEL_FAST,
    description="Final synthesis: combines policy, agri plan, cashflow, risk into complete post-call report.",
    instruction=POSTCALL_SYNTHESIS_INSTRUCTION,
    tools=[write_postcall_to_delta],
    output_key="postcall_analysis",
)
