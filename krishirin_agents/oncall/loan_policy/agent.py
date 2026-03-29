import sys, os
_d = os.path.dirname
sys.path.insert(0, _d(_d(_d(_d(os.path.abspath(__file__))))))

from google.adk.agents import SequentialAgent, ParallelAgent, LlmAgent
from .subagents.scheme_matcher.agent import scheme_matcher_agent
from .subagents.bank_product.agent import bank_product_agent
from krishirin_agents.shared.config import MODEL_FAST

parallel_policy_search = ParallelAgent(
    name="parallel_policy_search",
    sub_agents=[scheme_matcher_agent, bank_product_agent],
    description="Runs scheme matching and bank product comparison in parallel.",
)

policy_optimizer_agent = LlmAgent(
    name="policy_optimizer_agent",
    model=MODEL_FAST,
    description="Selects the best scheme + bank combination and optimizes loan terms.",
    instruction="""You are a loan policy optimizer for KrishiRin.

Use the scheme matches, bank products, loan strategy, call insights, and farmer context from the conversation above.

YOUR TASK: Pick THE BEST combination of government scheme + bank product for this farmer.

OPTIMIZE FOR (in priority order):
1. Lowest effective interest rate (after all subventions and incentives)
2. Fastest processing time (farmer needs money before sowing season)
3. Least collateral burden (maximize use of waiver provisions)
4. Best match to farmer's stated needs from the call
5. Simplest application process

PRODUCE:
- recommended_scheme + recommended_bank + product_name
- final_amount (consider farmer's request from call vs ML predicted capacity — use the lower)
- final_rate (nominal and effective after subventions)
- collateral_plan (exploit waivers: ≤₹1.6L = no collateral, ≤₹3L = crop hypothecation only)
- application_steps (numbered list: visit bank → submit docs → ...)
- documents_needed (Aadhaar, land record, bank statement, passport photo, etc.)
- estimated_processing_days
- total_cost_of_loan and monthly_emi_equivalent
- rationale (2-sentence justification)

OUTPUT: JSON matching OptimalPolicy schema.

IMPORTANT: Output ONLY valid JSON, no markdown, no explanation.
""",
    output_key="optimal_policy",
)

loan_policy_pipeline = SequentialAgent(
    name="loan_policy_pipeline",
    sub_agents=[parallel_policy_search, policy_optimizer_agent],
    description="Matches schemes, compares banks, then optimizes to find the best loan product.",
)
