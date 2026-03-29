import sys, os; _d = os.path.dirname; sys.path.insert(0, _d(_d(_d(_d(os.path.abspath(__file__))))))
from google.adk.agents import LlmAgent

from .prompt import DATA_LOADER_INSTRUCTION
from .tools import (
    load_farmer_profile,
    load_ml_scores,
    load_district_data,
    load_crop_calendar,
    load_msp_prices,
    fetch_weather_data,
)
from krishirin_agents.shared.config import MODEL_FAST

data_loader_agent = LlmAgent(
    name="data_loader_agent",
    model=MODEL_FAST,
    description=(
        "Loads all farmer data from Databricks Delta tables and external APIs. "
        "Produces a unified farmer_context that all downstream agents read from."
    ),
    instruction=DATA_LOADER_INSTRUCTION,
    tools=[
        load_farmer_profile,
        load_ml_scores,
        load_district_data,
        load_crop_calendar,
        load_msp_prices,
        fetch_weather_data,
    ],
    output_key="farmer_context",
)
