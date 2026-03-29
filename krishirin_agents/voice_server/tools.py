"""
Function tools available to the voice agent LLM during the call.
These are registered with OpenAI's function calling API.
"""

import asyncio
import logging
from krishirin_agents.voice_server.oncall_runner import (
    run_oncall_pipeline,
    is_complete,
    get_results,
    get_final_analysis,
)
from krishirin_agents.voice_server.models import AgentStatus

logger = logging.getLogger(__name__)

# Stores active session state
_active_sessions: dict[str, dict] = {}


def set_session_context(session_id: str, farmer_id: str, precall_context: str):
    """Store session context for tool access."""
    _active_sessions[session_id] = {
        "farmer_id": farmer_id,
        "precall_context": precall_context,
        "transcript_parts": [],
    }


def append_transcript(session_id: str, speaker: str, text: str):
    """Append a turn to the running transcript."""
    ctx = _active_sessions.get(session_id, {})
    ctx.setdefault("transcript_parts", []).append(f"{speaker}: {text}")


def get_transcript(session_id: str) -> str:
    ctx = _active_sessions.get(session_id, {})
    return "\n".join(ctx.get("transcript_parts", []))


# --- Tools exposed to the voice LLM ---

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "trigger_oncall_analysis",
            "description": (
                "Trigger the on-call analysis pipeline. Call this when the farmer has answered "
                "all clarification questions and confirmed readiness. The pipeline will run in "
                "the background while you continue talking to the farmer."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "confirmation_summary": {
                        "type": "string",
                        "description": "Brief summary of what the farmer confirmed and any new info revealed",
                    },
                },
                "required": ["confirmation_summary"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_analysis_status",
            "description": (
                "Check if the background analysis agents have finished. Call this periodically "
                "during small talk to know when results are ready."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_analysis_results",
            "description": (
                "Get the final analysis results after all agents are complete. "
                "Call this to read the loan policy, crop plan, and cashflow map to present to the farmer."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
]


async def handle_tool_call(session_id: str, tool_name: str, arguments: dict) -> dict:
    """Route tool calls from the voice LLM."""
    ctx = _active_sessions.get(session_id, {})
    farmer_id = ctx.get("farmer_id", "FARMER_001")

    if tool_name == "trigger_oncall_analysis":
        transcript = get_transcript(session_id)
        precall_context = ctx.get("precall_context", "")

        # Fire pipeline in background — returns immediately
        asyncio.create_task(
            run_oncall_pipeline(session_id, transcript, farmer_id, precall_context)
        )

        logger.info(f"Oncall analysis triggered for session {session_id}")
        return {
            "status": "started",
            "message": "Analysis pipeline started in background. Continue talking to the farmer. Use check_analysis_status to know when results are ready.",
        }

    elif tool_name == "check_analysis_status":
        results = get_results(session_id)
        completed = [k for k, v in results.items() if v.status == AgentStatus.COMPLETED]
        pending = [k for k, v in results.items() if v.status != AgentStatus.COMPLETED]
        all_done = is_complete(session_id)

        return {
            "all_done": all_done,
            "completed_agents": completed,
            "pending_agents": pending,
            "message": "All analysis complete! Use get_analysis_results to read the findings." if all_done else f"{len(completed)}/{len(completed)+len(pending)} agents finished. Keep talking.",
        }

    elif tool_name == "get_analysis_results":
        final = get_final_analysis(session_id)
        if final:
            return {
                "status": "ready",
                "policy": final.get("policy_recommendation", {}),
                "agri_plan": final.get("agri_advisory", {}),
                "cashflow": final.get("cashflow_projection", {}),
                "risk": final.get("risk_mitigation", {}),
                "farmer_summary": final.get("farmer_summary", ""),
            }
        return {"status": "not_ready", "message": "Analysis not yet complete."}

    return {"error": f"Unknown tool: {tool_name}"}
