import sys, os
_d = os.path.dirname
sys.path.insert(0, _d(_d(_d(_d(_d(_d(os.path.abspath(__file__))))))))

from google.adk.agents import LlmAgent
from .prompt import BANK_PRODUCT_INSTRUCTION
from krishirin_agents.shared.config import MODEL_FAST

bank_product_agent = LlmAgent(
    name="bank_product_agent",
    model=MODEL_FAST,
    description="Compares specific bank products (SBI, PNB, BoB, cooperative) for agricultural loans.",
    instruction=BANK_PRODUCT_INSTRUCTION,
    output_key="bank_products",
)
