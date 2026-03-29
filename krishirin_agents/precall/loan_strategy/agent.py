import sys, os; _d = os.path.dirname; sys.path.insert(0, _d(_d(_d(_d(os.path.abspath(__file__))))))
from google.adk.agents import LlmAgent

from .prompt import LOAN_STRATEGY_INSTRUCTION
from .tools import interest_calculator, collateral_checker
from krishirin_agents.shared.config import MODEL_SMART

loan_strategy_agent = LlmAgent(
    name="loan_strategy_agent",
    model=MODEL_SMART,
    description=(
        "Designs optimal loan package: product selection, amount, interest calculation, "
        "collateral check, and harvest-aligned repayment schedule."
    ),
    instruction=LOAN_STRATEGY_INSTRUCTION,
    tools=[interest_calculator, collateral_checker],
    output_key="loan_strategy",
)
