import sys, os; _d = os.path.dirname; sys.path.insert(0, _d(_d(_d(_d(os.path.abspath(__file__))))))
from google.adk.agents import LlmAgent

from .prompt import MARKET_RESEARCH_INSTRUCTION
from .tools import predict_crop_prices, predict_crop_yields
from krishirin_agents.shared.config import MODEL_FAST

market_research_agent = LlmAgent(
    name="market_research_agent",
    model=MODEL_FAST,
    description=(
        "Runs crop price and yield prediction models, then provides comprehensive "
        "market intelligence including mandi prices, disease alerts, weather advisories, "
        "and scheme updates for the farmer's district and crops."
    ),
    instruction=MARKET_RESEARCH_INSTRUCTION,
    tools=[predict_crop_prices, predict_crop_yields],
    output_key="market_research",
)
