"""Scheme synthesizer agent — separated so it can be imported without
triggering parallel_scheme_search creation (which would claim the sub-agents).
"""

import sys, os; _d = os.path.dirname; sys.path.insert(0, _d(_d(_d(_d(os.path.abspath(__file__))))))
from google.adk.agents import LlmAgent
from krishirin_agents.shared.config import MODEL_SMART

scheme_synthesizer_agent = LlmAgent(
    name="scheme_synthesizer_agent",
    model=MODEL_SMART,
    description=(
        "Combines scheme search results from RAG, web search, and eligibility evaluation "
        "into a unified eligibility report."
    ),
    instruction="""You are a scheme eligibility synthesizer for the KrishiRin system.

You have access to results from 3 parallel scheme search agents in session state:
- {scheme_rag_results} — retrieved scheme document chunks from FAISS
- {scheme_web_results} — latest scheme updates from web search
- {eligibility_evaluation} — rule-based eligibility assessment per scheme

YOUR TASK: Combine all three sources into a unified eligibility report.

FOR EACH SCHEME:
1. Start with the eligibility_evaluation (rule-based assessment) as the baseline
2. Enrich with details from scheme_rag_results (official scheme rules, fine print)
3. Update with any new information from scheme_web_results (changed rates, new deadlines)
4. If web results contradict RAG/rules, note the discrepancy

PRODUCE a JSON response with:
- eligible_schemes: list of objects with scheme_name, eligible (bool), match_pct (0-100), missing_requirements (list), estimated_benefit (string), action_needed (string), source (string)
- recommended_primary: name of the best-fit scheme
- total_available_benefits: estimated total across all eligible schemes
- key_findings: 2-3 sentence summary

PRIORITY ORDER for conflict resolution: web (most current) > RAG (official docs) > rules (embedded knowledge)
""",
    output_key="eligibility_report",
)
