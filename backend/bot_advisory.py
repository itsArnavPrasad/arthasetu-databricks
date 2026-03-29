"""System prompt + function tools for the unified Advisory Call.

The call now has 4 phases:
  Phase A: Clarification — ask questions about unclear points
  Phase B: Trigger — farmer confirms, LLM calls trigger_oncall_analysis
  Phase C: Small talk — while 13 ADK agents run in background
  Phase D: Results — present loan policy, crop plan, cashflow to farmer

The Pipecat pipeline is created in server.py. This module provides:
  - build_advisory_system_prompt() — the 4-phase system prompt
  - FUNCTION_DEFS — OpenAI function schemas for tool calling
  - handle_function_call() — routes function calls to oncall_runner
"""

import asyncio
import logging
import sys
import os

# Ensure krishirin_agents is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from krishirin_agents.voice_server.oncall_runner import (
    run_oncall_pipeline,
    is_complete,
    get_results,
    get_final_analysis,
)
from krishirin_agents.voice_server.models import AgentStatus

logger = logging.getLogger(__name__)

# Track active sessions
_sessions: dict[str, dict] = {}


def build_advisory_system_prompt(
    farmer_context: dict,
    results: dict,
    clarification_questions: list[str] | None = None,
) -> str:
    """Build the 4-phase advisory call system prompt.

    Args:
        farmer_context: dict with name, district, state
        results: normalized results from get_results() endpoint
        clarification_questions: precall-generated questions (from auto_questions)
    """
    name = farmer_context.get("name", "Farmer")
    district = farmer_context.get("district", "")
    state = farmer_context.get("state", "")

    # Read from correct keys after precall restructuring
    score = results.get("credit_assessment", results.get("score", {}))
    if not isinstance(score, dict):
        score = {}
    risk = results.get("risk_analysis", {})
    if not isinstance(risk, dict):
        risk = {}
    agri = results.get("agricultural_analysis", {})
    if not isinstance(agri, dict):
        agri = {}

    # Extract risk flags from multiple possible locations
    flags = score.get("top_negative_factors", [])
    if not flags and isinstance(risk.get("critical_risks", risk.get("critical_flags")), list):
        flags = [
            f.get("detail", f.get("description", str(f))) if isinstance(f, dict) else str(f)
            for f in (risk.get("critical_risks") or risk.get("critical_flags") or [])
        ]
    if not flags and isinstance(risk.get("warnings", risk.get("warning_flags")), list):
        flags = [
            f.get("detail", f.get("description", str(f))) if isinstance(f, dict) else str(f)
            for f in (risk.get("warnings") or risk.get("warning_flags") or [])[:3]
        ]

    flags_text = "\n".join(f"  - {f}" for f in flags) if flags else "  (none identified)"

    # Score info
    grameen_score = score.get("grameen_score", "N/A")
    predicted_capacity = score.get("predicted_capacity", 0)
    risk_category = score.get("risk_category", "")

    # Build clarification questions — use precall-generated ones, pick best 2
    if clarification_questions and len(clarification_questions) > 0:
        # Take up to 2 questions from precall analysis
        qs = clarification_questions[:2]
        questions_text = "\n".join(f'  {i+1}. "{q}"' for i, q in enumerate(qs))
    else:
        # Fallback to generic questions only if no precall questions available
        questions_text = (
            '  1. "Aapko kitne ka loan chahiye aur kis kaam ke liye?"\n'
            '  2. "Is baar kaun si fasal ugaane ka plan hai?"'
        )

    return f"""You are a KrishiRin loan advisor calling farmer {name} from {district}, {state}.
You speak in HINDI (Hinglish acceptable). Keep responses under 2-3 sentences — this is a voice call.

=== FARMER DATA ===
Grameen Score: {grameen_score}/100 (Category: {risk_category})
Estimated Loan Capacity: ₹{predicted_capacity:,}
Risk Flags:
{flags_text}

=== YOUR CONVERSATION FLOW ===

PHASE A — QUICK CLARIFICATION (start here):
Greet: "Namaste {name} ji, main KrishiRin se bol raha hoon."
Ask these 2 questions, one at a time:
{questions_text}
After both answered → move to Phase B immediately.

PHASE B — TRIGGER ANALYSIS:
Say: "Theek hai {name} ji, main aapke liye sabse achhi loan policy dhundhta hoon, ek minute dijiye."
Immediately call trigger_oncall_analysis with a brief summary of what farmer said.

PHASE C — BRIEF WAIT (while agents run, ~10 seconds):
Ask ONE casual question: "Aapke {district} mein mausam kaisa hai?"
After farmer responds, call check_analysis_status.
If all_done=true → go to Phase D.
If not done → ask one more question, then check again.

PHASE D — PRESENT RESULTS:
Call get_analysis_results to get the analysis.
Present conversationally:
  1. Loan: "{name} ji, aapke liye [scheme] mila hai, ₹[amount], sirf [rate]% byaaj."
  2. Crop plan: "[crops] ugaayein — expected income ₹[amount]"
  3. Next steps: "[Bank] branch jaayein [documents] lekar."
End: "Yeh plan follow karenge toh loan aasaani se chuka payenge!"

=== RULES ===
- ALWAYS Hindi/Hinglish. Max 2-3 sentences.
- Use ₹ amounts. Be warm, use "ji".
- NEVER reveal you are AI.
"""


# --- Function definitions for Pipecat function calling ---

from pipecat.adapters.schemas.function_schema import FunctionSchema
from pipecat.processors.aggregators.llm_context import ToolsSchema

FUNCTION_SCHEMAS = [
    FunctionSchema(
        name="trigger_oncall_analysis",
        description="Trigger the on-call analysis pipeline in the background. Call this after the farmer has answered clarification questions and confirmed readiness.",
        properties={
            "summary": {
                "type": "string",
                "description": "Brief summary of farmer's answers and any new information revealed",
            },
        },
        required=["summary"],
    ),
    FunctionSchema(
        name="check_analysis_status",
        description="Check if background analysis agents are done. Call during small talk to know when results are ready.",
        properties={},
        required=[],
    ),
    FunctionSchema(
        name="get_analysis_results",
        description="Get final analysis results once all agents complete. Read the loan policy, crop plan, cashflow to present to farmer.",
        properties={},
        required=[],
    ),
]

TOOLS_SCHEMA = ToolsSchema(standard_tools=FUNCTION_SCHEMAS)


def register_session(session_id: str, farmer_id: str, precall_context: str):
    """Register a session for function call routing."""
    _sessions[session_id] = {
        "farmer_id": farmer_id,
        "precall_context": precall_context,
        "transcript_parts": [],
    }


def unregister_session(session_id: str):
    """Remove a session when the call ends (cleanup)."""
    _sessions.pop(session_id, None)


def append_to_transcript(session_id: str, speaker: str, text: str):
    """Append a turn to the running transcript."""
    if session_id in _sessions:
        _sessions[session_id]["transcript_parts"].append(f"{speaker}: {text}")


async def handle_function_call(session_id: str, fn_name: str, fn_args: dict) -> str:
    """Handle function calls from the Pipecat LLM. Returns result as string."""
    ctx = _sessions.get(session_id, {})
    farmer_id = ctx.get("farmer_id", "")

    if fn_name == "trigger_oncall_analysis":
        transcript = "\n".join(ctx.get("transcript_parts", []))
        precall_context = ctx.get("precall_context", "")

        # Fire pipeline in background — returns immediately
        asyncio.create_task(
            run_oncall_pipeline(session_id, transcript, farmer_id, precall_context)
        )
        logger.info(f"On-call analysis triggered for session {session_id}")
        return '{"status": "started", "message": "Analysis pipeline started. Continue talking to the farmer. Call check_analysis_status in a few turns to check progress."}'

    elif fn_name == "check_analysis_status":
        results = get_results(session_id)
        completed = [k for k, v in results.items() if v.status == AgentStatus.COMPLETED]
        pending = [k for k, v in results.items() if v.status != AgentStatus.COMPLETED]
        all_done = is_complete(session_id)

        if all_done:
            return f'{{"all_done": true, "completed": {len(completed)}, "message": "All analysis complete! Call get_analysis_results now."}}'
        return f'{{"all_done": false, "completed": {len(completed)}, "pending": {len(pending)}, "message": "Still processing. Keep talking to the farmer."}}'

    elif fn_name == "get_analysis_results":
        final = get_final_analysis(session_id)
        if final:
            import json
            # Extract key fields for the voice agent to speak about
            policy = final.get("policy_recommendation", {})
            agri = final.get("agri_advisory", {})
            cashflow = final.get("cashflow_projection", {})
            summary = final.get("farmer_summary", "")
            return json.dumps({
                "status": "ready",
                "policy": policy,
                "agri_plan": agri,
                "cashflow": cashflow,
                "farmer_summary": summary,
            }, default=str)[:3000]  # Truncate to keep context manageable
        return '{"status": "not_ready", "message": "Analysis not yet complete."}'

    return f'{{"error": "Unknown function: {fn_name}"}}'
