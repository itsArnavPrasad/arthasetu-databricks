import sys, os; _d = os.path.dirname; sys.path.insert(0, _d(_d(_d(_d(os.path.abspath(__file__))))))
from google.adk.agents import LlmAgent

from .prompt import SCORE_EXPLAINER_INSTRUCTION
from .tools import run_behavioral_classifier, run_default_predictor
from krishirin_agents.shared.config import MODEL_FAST

score_explainer_agent = LlmAgent(
    name="score_explainer_agent",
    model=MODEL_FAST,
    description=(
        "Runs ML scoring models on OCR-extracted bank/loan data and generates "
        "a human-readable credit assessment. Uses Databricks serving endpoints "
        "for behavioral classification and default prediction."
    ),
    instruction=SCORE_EXPLAINER_INSTRUCTION,
    tools=[run_behavioral_classifier, run_default_predictor],
    output_key="credit_assessment",
)
