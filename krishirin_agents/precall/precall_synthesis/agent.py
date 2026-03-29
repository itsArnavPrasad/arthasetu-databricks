import sys, os; _d = os.path.dirname; sys.path.insert(0, _d(_d(_d(_d(os.path.abspath(__file__))))))
from google.adk.agents import LlmAgent

from .prompt import PRECALL_SYNTHESIS_INSTRUCTION
from krishirin_agents.shared.config import MODEL_SYNTHESIS

precall_synthesis_agent = LlmAgent(
    name="precall_synthesis_agent",
    model=MODEL_SYNTHESIS,
    description=(
        "Final synthesis agent that generates clarification questions "
        "and a voice agent briefing from all analysis results."
    ),
    instruction=PRECALL_SYNTHESIS_INSTRUCTION,
    tools=[],
    output_key="precall_analysis",
)
