import sys, os
_d = os.path.dirname
sys.path.insert(0, _d(_d(_d(_d(os.path.abspath(__file__))))))

from google.adk.agents import LlmAgent
from .prompt import CASHFLOW_MAPPER_INSTRUCTION
from krishirin_agents.shared.config import MODEL_FAST

cashflow_mapper_agent = LlmAgent(
    name="cashflow_mapper_agent",
    model=MODEL_FAST,
    description="Creates 12-month income vs EMI projection with surplus/deficit analysis and buffer strategy.",
    instruction=CASHFLOW_MAPPER_INSTRUCTION,
    output_key="cashflow_map",
)
