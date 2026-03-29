import sys, os
_d = os.path.dirname
sys.path.insert(0, _d(_d(_d(_d(_d(_d(os.path.abspath(__file__))))))))

from google.adk.agents import LlmAgent
from .prompt import INPUT_COST_INSTRUCTION
from krishirin_agents.shared.config import MODEL_FAST

input_cost_agent = LlmAgent(
    name="input_cost_agent",
    model=MODEL_FAST,
    description="Estimates per-crop cultivation costs and recommends specific cost reduction strategies.",
    instruction=INPUT_COST_INSTRUCTION,
    output_key="input_costs",
)
