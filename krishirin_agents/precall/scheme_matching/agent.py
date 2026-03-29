import sys, os; _d = os.path.dirname; sys.path.insert(0, _d(_d(_d(_d(os.path.abspath(__file__))))))
from google.adk.agents import SequentialAgent, ParallelAgent, LlmAgent

from .subagents.scheme_rag.agent import scheme_rag_agent
from .subagents.scheme_web.agent import scheme_web_agent
from .subagents.eligibility_evaluator.agent import eligibility_evaluator_agent
from krishirin_agents.shared.config import MODEL_SMART

# --- Parallel: Run all 3 scheme search agents concurrently ---
parallel_scheme_search = ParallelAgent(
    name="parallel_scheme_search",
    sub_agents=[
        scheme_rag_agent,
        scheme_web_agent,
        eligibility_evaluator_agent,
    ],
    description=(
        "Runs 3 scheme search agents in parallel: "
        "FAISS RAG search, web search for latest updates, and rule-based eligibility evaluation."
    ),
)

# --- Synthesizer: Merge results from all 3 parallel agents ---
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

# --- Orchestrator: Sequential (parallel search → synthesis) ---
scheme_matching_pipeline = SequentialAgent(
    name="scheme_matching_pipeline",
    sub_agents=[parallel_scheme_search, scheme_synthesizer_agent],
    description=(
        "Scheme matching pipeline: runs FAISS RAG, web search, and eligibility evaluation "
        "in parallel, then synthesizes results into a unified eligibility report."
    ),
)
