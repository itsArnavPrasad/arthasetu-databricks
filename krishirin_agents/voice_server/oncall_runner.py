"""
Runs the oncall ADK agent pipeline in the background during a voice call.
Emits SSE events as each agent completes so the frontend can render cards.
"""

import asyncio
import json
import logging
import sys
import os
from datetime import datetime
from typing import Optional

# Ensure krishirin_agents is importable
_d = os.path.dirname
sys.path.insert(0, _d(_d(_d(os.path.abspath(__file__)))))

from krishirin_agents.voice_server.models import AgentStatus, AgentResult, AGENT_DISPLAY

logger = logging.getLogger(__name__)

# Global state for SSE streaming
_session_results: dict[str, dict[str, AgentResult]] = {}
_session_events: dict[str, asyncio.Queue] = {}


def get_event_queue(session_id: str) -> asyncio.Queue:
    if session_id not in _session_events:
        _session_events[session_id] = asyncio.Queue()
    return _session_events[session_id]


def get_results(session_id: str) -> dict[str, AgentResult]:
    return _session_results.get(session_id, {})


def is_complete(session_id: str) -> bool:
    """Check if the 4 core agents are done."""
    results = _session_results.get(session_id, {})
    if not results:
        return False
    core_keys = {"call_insights", "optimal_policy", "agri_advisory", "risk_plan"}
    completed = {k for k, v in results.items() if v.status == AgentStatus.COMPLETED}
    return core_keys.issubset(completed)


def _parse_result(value) -> dict:
    """Parse agent output — LLM agents store strings, not dicts.
    Try to extract JSON from the string."""
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        text = value.strip()
        # Strip markdown code fences if present
        if text.startswith("```"):
            lines = text.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            text = "\n".join(lines).strip()
        # Try parsing as JSON
        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass
        # Try finding JSON object in the text
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end > start:
            try:
                parsed = json.loads(text[start:end + 1])
                if isinstance(parsed, dict):
                    return parsed
            except json.JSONDecodeError:
                pass
        return {"output": text[:1000]}
    return {"output": str(value)[:500]}


def get_final_analysis(session_id: str) -> Optional[dict]:
    """Get analysis results — returns partial results from completed agents
    even if the full pipeline hasn't finished yet."""
    results = _session_results.get(session_id, {})

    # Try full synthesis first
    final = results.get("postcall_analysis")
    if final and final.status == AgentStatus.COMPLETED and final.result:
        return final.result

    # Build partial result from completed core agents
    partial = {}
    for key in ["call_insights", "optimal_policy", "agri_advisory", "risk_plan", "cashflow_map"]:
        agent = results.get(key)
        if agent and agent.status == AgentStatus.COMPLETED and agent.result:
            partial[key] = agent.result

    if partial:
        # Map to the fields the voice agent expects
        return {
            "policy_recommendation": partial.get("optimal_policy", {}),
            "agri_advisory": partial.get("agri_advisory", {}),
            "cashflow_projection": partial.get("cashflow_map", {}),
            "risk_mitigation": partial.get("risk_plan", {}),
            "farmer_summary": partial.get("call_insights", {}).get("call_summary", "Analysis complete."),
        }
    return None


async def _emit(session_id: str, agent_key: str, result: AgentResult):
    """Emit an SSE event for a completed agent."""
    _session_results.setdefault(session_id, {})[agent_key] = result
    queue = get_event_queue(session_id)
    await queue.put({
        "type": "agent_update",
        "agent": agent_key,
        "title": result.title,
        "icon": result.icon,
        "status": result.status.value,
        "summary": result.summary,
        "result": result.result,
        "timestamp": datetime.utcnow().isoformat(),
    })


async def run_oncall_pipeline(session_id: str, transcript: str, farmer_id: str, precall_context: str):
    """
    Run the oncall agents in the background (2 stages, 4 LLM calls).
    Emits SSE events as each agent completes so the frontend can render cards.
    """
    logger.info(f"Starting oncall pipeline for {farmer_id}, session {session_id}")

    # Initialize all agents as pending
    for key, template in AGENT_DISPLAY.items():
        await _emit(session_id, key, template.model_copy())

    try:
        from google.adk.runners import Runner
        from google.adk.sessions import InMemorySessionService
        from krishirin_agents.oncall.coordinator.agent import root_agent

        session_service = InMemorySessionService()
        runner = Runner(
            agent=root_agent,
            app_name="krishirin_oncall",
            session_service=session_service,
        )

        session = await session_service.create_session(
            app_name="krishirin_oncall",
            user_id="voice_system",
            state={"farmer_id": farmer_id},
        )

        input_message = f"""{precall_context}

=== CALL TRANSCRIPT ===
{transcript}
"""
        # Track all agents — 7 visible + intermediates (None = skip)
        seen_keys = set()
        agent_key_map = {
            "call_insights": ("call_insights", "Call Analysis", "📞"),
            "scheme_matches": ("scheme_matches", "Scheme Matching", "📋"),
            "bank_products": ("bank_products", "Bank Comparison", "🏧"),
            "optimal_policy": ("optimal_policy", "Loan Policy", "🏦"),
            "crop_plan": None,        # intermediate
            "input_costs": None,      # intermediate
            "market_strategy": None,  # intermediate
            "agri_advisory": ("agri_advisory", "Agricultural Advisory", "🌾"),
            "risk_plan": ("risk_plan", "Risk Mitigation", "🛡️"),
            "cashflow_map": ("cashflow_map", "Cashflow Map", "📊"),
        }

        from google.genai import types as genai_types
        new_message = genai_types.Content(
            role="user",
            parts=[genai_types.Part.from_text(text=input_message)],
        )

        async for event in runner.run_async(
            user_id="voice_system",
            session_id=session.id,
            new_message=new_message,
        ):
            if hasattr(event, "actions") and event.actions:
                state_delta = getattr(event.actions, "state_delta", None)
                if state_delta and isinstance(state_delta, dict):
                    for key in state_delta:
                        if key not in seen_keys and key in agent_key_map:
                            seen_keys.add(key)
                            mapping = agent_key_map[key]
                            if mapping:  # visible agent
                                ak, title, icon = mapping
                                parsed = _parse_result(state_delta[key])
                                summary = _summarize(key, parsed)
                                logger.info(f"Agent {ak} completed, keys: {list(parsed.keys()) if isinstance(parsed, dict) else 'str'}")
                                await _emit(session_id, ak, AgentResult(
                                    agent_name=ak,
                                    status=AgentStatus.COMPLETED,
                                    title=title,
                                    icon=icon,
                                    summary=summary,
                                    result=parsed,
                                ))

        # Fallback: check session state for any missed agents
        updated_session = await session_service.get_session(
            app_name="krishirin_oncall", user_id="voice_system", session_id=session.id
        )
        if updated_session and updated_session.state:
            for key, mapping in agent_key_map.items():
                if mapping and key in updated_session.state and key not in seen_keys:
                    ak, title, icon = mapping
                    parsed = _parse_result(updated_session.state[key])
                    logger.info(f"Agent {ak} found in session state (fallback)")
                    await _emit(session_id, ak, AgentResult(
                        agent_name=ak, status=AgentStatus.COMPLETED,
                        title=title, icon=icon,
                        summary=_summarize(key, parsed),
                        result=parsed,
                    ))

        await get_event_queue(session_id).put({"type": "pipeline_complete"})
        logger.info(f"Oncall pipeline completed for {farmer_id}, agents: {seen_keys}")

    except Exception as e:
        logger.error(f"Oncall pipeline failed: {e}", exc_info=True)
        await get_event_queue(session_id).put({
            "type": "pipeline_error", "error": str(e)
        })


def _summarize(key: str, value) -> str:
    """Generate a brief summary for a completed agent."""
    if isinstance(value, str):
        return value[:100]
    if isinstance(value, dict):
        if key == "optimal_policy":
            return f"{value.get('recommended_scheme', 'KCC')} via {value.get('recommended_bank', 'Bank')}, ₹{value.get('final_amount', '?')}"
        if key == "agri_advisory":
            return f"Complete advisory: {value.get('advisory_summary', 'Plan ready')[:80]}"
        if key == "cashflow_map":
            return f"12-month projection: {value.get('annual_summary', 'Map ready')[:80]}"
        if key == "risk_plan":
            return f"Risk level: {value.get('overall_risk_level', 'assessed')}"
        if key == "call_insights":
            return f"Status: {value.get('acceptance_status', 'analyzed')}"
    return "Completed"
