import sys, os
_d = os.path.dirname
sys.path.insert(0, _d(_d(_d(_d(_d(_d(os.path.abspath(__file__))))))))

from google.adk.agents import LlmAgent
from .prompt import CROP_PLANNER_INSTRUCTION
from krishirin_agents.shared.config import MODEL_FAST

crop_planner_agent = LlmAgent(
    name="crop_planner_agent",
    model=MODEL_FAST,
    description="Creates land assessment and sowing plan with specific crops, area, yield, and revenue.",
    instruction=CROP_PLANNER_INSTRUCTION,
    output_key="crop_plan",
)
