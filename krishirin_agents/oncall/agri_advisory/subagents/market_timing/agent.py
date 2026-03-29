import sys, os
_d = os.path.dirname
sys.path.insert(0, _d(_d(_d(_d(_d(_d(os.path.abspath(__file__))))))))

from google.adk.agents import LlmAgent
from .prompt import MARKET_TIMING_INSTRUCTION
from krishirin_agents.shared.config import MODEL_FAST

market_timing_agent = LlmAgent(
    name="market_timing_agent",
    model=MODEL_FAST,
    description="Provides weather-aware farming timing and crop selling strategy with MSP and mandi insights.",
    instruction=MARKET_TIMING_INSTRUCTION,
    output_key="market_strategy",
)
