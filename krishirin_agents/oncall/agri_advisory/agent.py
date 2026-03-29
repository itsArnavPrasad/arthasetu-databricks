import sys, os
_d = os.path.dirname
sys.path.insert(0, _d(_d(_d(_d(os.path.abspath(__file__))))))

from google.adk.agents import SequentialAgent, ParallelAgent, LlmAgent
from .subagents.crop_planner.agent import crop_planner_agent
from .subagents.input_cost.agent import input_cost_agent
from .subagents.market_timing.agent import market_timing_agent
from krishirin_agents.shared.config import MODEL_FAST

# crop_planner must run FIRST — input_cost and market_timing both read its output_key "crop_plan"
parallel_after_crop = ParallelAgent(
    name="parallel_after_crop",
    sub_agents=[input_cost_agent, market_timing_agent],
    description="Runs input cost and market timing in parallel (both read crop_plan).",
)

agri_synthesizer_agent = LlmAgent(
    name="agri_synthesizer_agent",
    model=MODEL_FAST,
    description="Synthesizes crop plan, input costs, and market strategy into complete agricultural advisory.",
    instruction="""You are an agricultural advisory synthesizer for KrishiRin.

Use the crop plan (Sections 1-2), input costs (Section 3), market strategy (Sections 4-5), and farmer context from the conversation above.

YOUR TASK: Create Section 6 (Income Diversification) and merge everything into a complete advisory.

SECTION 6 — INCOME DIVERSIFICATION:
Based on the farmer's assets and land:
- Dairy: If land supports fodder, 1-2 cows = ₹3,000-5,000/month steady income
- Poultry: Backyard poultry, 20-30 birds = ₹1,500-2,000/month eggs
- Kitchen garden: Vegetables for household = saves ₹1,000-2,000/month
- Value addition: Dal milling, spice grinding, pickle making = 2-3x revenue
- MGNREGA: ₹300-350/day × 100 days = ₹30,000-35,000 during lean months
- Factor in what farmer mentioned in the call (cattle, new irrigation, etc.)

THEN SYNTHESIZE:
- Compile total_expected_revenue (all crops + allied income)
- Compile total_expected_costs (from input_costs)
- Calculate net_expected_income
- Write a 3-sentence advisory_summary connecting farming plan to loan repayment capacity

OUTPUT: JSON matching AgriAdvisory schema.

IMPORTANT: Output ONLY valid JSON, no markdown, no explanation.
""",
    output_key="agri_advisory",
)

agri_advisory_pipeline = SequentialAgent(
    name="agri_advisory_pipeline",
    sub_agents=[crop_planner_agent, parallel_after_crop, agri_synthesizer_agent],
    description="Crop planning → parallel cost/market analysis → synthesized agricultural advisory.",
)
