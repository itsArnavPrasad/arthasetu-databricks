"""
KrishiRin Voice Server — FastAPI backend for unified on-call experience.

Endpoints:
  POST /api/call/start     — Start a voice session (returns session_id)
  POST /api/call/process   — Process a user message (text mode for testing)
  GET  /api/events/{sid}   — SSE stream of agent results for frontend
  GET  /api/call/status/{sid} — Check analysis status
  GET  /health             — Health check

For production: WebSocket audio streaming integrates via Pipecat/SmallWebRTC.
For testing: Use the /api/call/process endpoint with text.
"""

import asyncio
import json
import logging
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from krishirin_agents.voice_server.voice_pipeline import VoiceSession
from krishirin_agents.voice_server.oncall_runner import get_event_queue, get_results, is_complete
from krishirin_agents.voice_server.models import AgentStatus
from krishirin_agents.shared.sample_data import (
    SAMPLE_FARMER_PROFILE, SAMPLE_ML_SCORES, SAMPLE_DISTRICT_DATA,
    SAMPLE_CROP_CALENDAR, SAMPLE_MSP_PRICES, SAMPLE_WEATHER,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Active voice sessions
_sessions: dict[str, VoiceSession] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("KrishiRin Voice Server starting...")
    yield
    logger.info("KrishiRin Voice Server shutting down.")


app = FastAPI(title="KrishiRin Voice Server", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class StartCallRequest(BaseModel):
    farmer_id: str = "FARMER_001"


class ProcessRequest(BaseModel):
    session_id: str
    text: str


@app.post("/api/call/start")
async def start_call(req: StartCallRequest):
    """Start a new voice call session. Returns session_id."""
    session_id = str(uuid.uuid4())[:8]

    # Build precall analysis context (sample data for now)
    precall = {
        "farmer_id": req.farmer_id,
        "profile": SAMPLE_FARMER_PROFILE,
        "ml_scores": SAMPLE_ML_SCORES,
        "district_data": SAMPLE_DISTRICT_DATA,
        "crop_calendar": SAMPLE_CROP_CALENDAR,
        "msp_prices": SAMPLE_MSP_PRICES,
        "weather": SAMPLE_WEATHER,
        "score_summary": {
            "grameen_score": SAMPLE_ML_SCORES["grameen_score"],
            "risk_category": SAMPLE_ML_SCORES["risk_category"],
            "top_positive_factors": SAMPLE_ML_SCORES["top_positive_factors"],
            "top_negative_factors": SAMPLE_ML_SCORES["top_negative_factors"],
        },
        "loan_strategy": {
            "recommended_product": "KCC",
            "amount": 200000,
            "interest_rate_effective": 2.0,
            "tenure_months": 36,
            "monthly_emi_equivalent": 5700,
            "collateral_requirement": "Waived up to ₹1.6L",
        },
        "risk_flags": {
            "warnings": ["Income seasonality 35%", "Not enrolled in PMFBY"],
        },
        "market_insights": {
            "weather_advisory": "Light rain expected Mar 31, good for sowing preparation",
        },
    }

    voice_session = VoiceSession(session_id, req.farmer_id, precall)
    _sessions[session_id] = voice_session

    # Generate initial greeting
    greeting = await voice_session.process_text(
        "The call has started. Greet the farmer and begin Phase 1 (clarification questions)."
    )

    return {
        "session_id": session_id,
        "farmer_id": req.farmer_id,
        "greeting": greeting,
    }


@app.post("/api/call/process")
async def process_message(req: ProcessRequest):
    """Process a text message from the farmer (text mode for testing)."""
    session = _sessions.get(req.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    reply = await session.process_text(req.text)
    return {"reply": reply, "session_id": req.session_id}


@app.get("/api/events/{session_id}")
async def agent_events(session_id: str):
    """SSE stream of agent completion events for frontend cards."""

    async def event_stream():
        queue = get_event_queue(session_id)
        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=60)
                yield f"data: {json.dumps(event)}\n\n"
                if event.get("type") in ("pipeline_complete", "pipeline_error"):
                    break
            except asyncio.TimeoutError:
                yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.get("/api/call/status/{session_id}")
async def call_status(session_id: str):
    """Get current analysis status."""
    results = get_results(session_id)
    completed = [k for k, v in results.items() if v.status == AgentStatus.COMPLETED]
    total = len(results)
    return {
        "all_done": is_complete(session_id),
        "completed": len(completed),
        "total": total,
        "agents": {k: {"status": v.status.value, "title": v.title, "summary": v.summary} for k, v in results.items()},
    }


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "krishirin_voice_server"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
