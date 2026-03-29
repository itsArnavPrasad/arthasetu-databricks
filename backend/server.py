"""KrishiRin Backend — FastAPI server with real Pipecat voice pipelines.

Serves:
- REST API for application management, ML pipeline status, results
- SmallWebRTC /api/offer endpoint for Pipecat voice calls
- All Databricks interaction happens here (frontend never talks to Databricks)
"""

import asyncio
import os
import sys
import uuid
import logging
from contextlib import asynccontextmanager
from typing import Dict
import json

# Add project root to sys.path so krishirin_agents is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Add backend dir so ocr_service, databricks_client etc. are importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, Request, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Suppress noisy loggers
logging.getLogger("LiteLLM").setLevel(logging.WARNING)
logging.getLogger("litellm").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

# In-memory stores (hackathon demo)
applications: dict = {}
pipeline_statuses: dict = {}

# SmallWebRTC peer connections
pcs_map: Dict[str, "SmallWebRTCConnection"] = {}

# Active call sessions (farmer_id → session_id for SSE)
_active_call_sessions: Dict[str, str] = {}


# ============================================================
# Pipecat Pipeline Runner
# ============================================================

async def run_voice_pipeline(webrtc_connection, call_type: str, farmer_id: str):
    """Run a full Sarvam STT → LLM → Sarvam TTS pipeline over SmallWebRTC."""
    from pipecat.audio.vad.silero import SileroVADAnalyzer
    from pipecat.frames.frames import LLMRunFrame
    from pipecat.pipeline.pipeline import Pipeline
    from pipecat.pipeline.runner import PipelineRunner
    from pipecat.pipeline.task import PipelineParams, PipelineTask
    from pipecat.processors.aggregators.llm_context import LLMContext
    from pipecat.processors.aggregators.llm_response_universal import (
        LLMContextAggregatorPair,
        LLMUserAggregatorParams,
    )
    from pipecat.services.sarvam.stt import SarvamSTTService
    from pipecat.services.sarvam.tts import SarvamTTSService
    from pipecat.services.openai.llm import OpenAILLMService
    from pipecat.transports.base_transport import TransportParams
    from pipecat.transports.smallwebrtc.transport import SmallWebRTCTransport

    logger.info(f"Starting {call_type} voice pipeline for farmer {farmer_id}")

    # --- Transport ---
    transport = SmallWebRTCTransport(
        webrtc_connection=webrtc_connection,
        params=TransportParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
        ),
    )

    # --- STT: Sarvam Saaras v3 ---
    stt = SarvamSTTService(
        api_key=os.getenv("SARVAMAI_API_KEY") or os.getenv("SARVAM_API_KEY"),
        settings=SarvamSTTService.Settings(
            model="saaras:v3",
        ),
    )

    # --- TTS: Sarvam Bulbul v3 ---
    tts = SarvamTTSService(
        api_key=os.getenv("SARVAMAI_API_KEY") or os.getenv("SARVAM_API_KEY"),
        settings=SarvamTTSService.Settings(
            model="bulbul:v3",
            voice="shubh",
        ),
    )

    # --- LLM: OpenAI GPT-4o-mini ---
    llm = OpenAILLMService(
        api_key=os.getenv("OPENAI_API_KEY"),
        settings=OpenAILLMService.Settings(
            model="gpt-4o-mini",
        ),
    )

    # --- Build system prompt based on call type ---
    if call_type == "understanding":
        from bot_understanding import build_understanding_system_prompt
        briefing = await get_pre_call_briefing(farmer_id)
        farmer_context = {
            "name": briefing["farmer"]["name"],
            "district": briefing["farmer"]["district"],
            "state": briefing["farmer"]["state"],
            "land_holding_acres": briefing["farmer"]["land_holding_acres"],
            "crops": briefing["farmer"]["crops"],
            "grameen_score": briefing["score"]["grameen_score"],
            "risk_category": briefing["score"]["risk_category"],
            "flags": [f["description"] for f in briefing["flags"]],
            "auto_questions": briefing["auto_questions"],
        }
        system_prompt = build_understanding_system_prompt(farmer_context)
    else:
        from bot_advisory import (
            build_advisory_system_prompt,
            TOOLS_SCHEMA,
            register_session,
            unregister_session,
            handle_function_call,
        )
        import json as _json

        briefing = await get_pre_call_briefing(farmer_id)
        results = await get_results(farmer_id)

        # Merge briefing score into results if credit_assessment is empty
        # (briefing extracts score from pipeline_state with multiple fallbacks)
        results_dict = dict(results) if isinstance(results, dict) else {}
        briefing_score = briefing.get("score", {})
        if briefing_score and isinstance(briefing_score, dict) and briefing_score.get("grameen_score"):
            existing_credit = results_dict.get("credit_assessment", {})
            if not isinstance(existing_credit, dict) or not existing_credit.get("grameen_score"):
                results_dict["credit_assessment"] = briefing_score
        # Merge briefing flags into results if risk_analysis is empty
        briefing_flags = briefing.get("flags", [])
        if briefing_flags and isinstance(briefing_flags, list):
            existing_risk = results_dict.get("risk_analysis", {})
            if not existing_risk or (isinstance(existing_risk, dict) and len(existing_risk) == 0):
                results_dict["risk_analysis"] = {"critical_risks": briefing_flags}

        farmer_context = {
            "name": briefing["farmer"]["name"],
            "district": briefing["farmer"]["district"],
            "state": briefing["farmer"]["state"],
        }
        clarification_qs = briefing.get("auto_questions", [])
        system_prompt = build_advisory_system_prompt(farmer_context, results_dict, clarification_qs)

        # Cleanup any previous session for this farmer (e.g. page refresh)
        old_session_id = _active_call_sessions.pop(farmer_id, None)
        if old_session_id:
            unregister_session(old_session_id)
            logger.info(f"Cleaned up stale session {old_session_id} for farmer {farmer_id}")

        # Register this session for on-call agent function routing
        session_id = f"call_{farmer_id}_{uuid.uuid4().hex[:6]}"
        precall_context = _json.dumps({**briefing, **results_dict}, default=str)
        register_session(session_id, farmer_id, precall_context)

        # Register function tools with the LLM
        from pipecat.services.llm_service import FunctionCallParams

        async def _trigger_analysis(params: FunctionCallParams):
            result = await handle_function_call(session_id, "trigger_oncall_analysis", params.arguments)
            await params.result_callback(result)

        async def _check_status(params: FunctionCallParams):
            result = await handle_function_call(session_id, "check_analysis_status", {})
            await params.result_callback(result)

        async def _get_results(params: FunctionCallParams):
            result = await handle_function_call(session_id, "get_analysis_results", {})
            await params.result_callback(result)

        llm.register_function("trigger_oncall_analysis", _trigger_analysis)
        llm.register_function("check_analysis_status", _check_status)
        llm.register_function("get_analysis_results", _get_results)

        # Store session_id for SSE endpoint
        _active_call_sessions[farmer_id] = session_id

    # --- Context + Aggregators ---
    if call_type == "advisory":
        context = LLMContext(tools=TOOLS_SCHEMA)
    else:
        context = LLMContext()
    user_aggregator, assistant_aggregator = LLMContextAggregatorPair(
        context,
        user_params=LLMUserAggregatorParams(vad_analyzer=SileroVADAnalyzer()),
    )

    # --- Pipeline: Transport In → STT → User Agg → LLM → TTS → Transport Out → Assistant Agg ---
    pipeline = Pipeline(
        [
            transport.input(),
            stt,
            user_aggregator,
            llm,
            tts,
            transport.output(),
            assistant_aggregator,
        ]
    )

    task = PipelineTask(
        pipeline,
        params=PipelineParams(
            enable_metrics=True,
            enable_usage_metrics=True,
            allow_interruptions=True,
        ),
    )

    # --- Events ---
    @transport.event_handler("on_client_connected")
    async def on_client_connected(transport, client):
        logger.info(f"Client connected for {call_type} call (farmer: {farmer_id})")
        # Inject system prompt and kick off the conversation
        context.add_message({"role": "system", "content": system_prompt})
        context.add_message({"role": "user", "content": "Please introduce yourself to the farmer and begin the conversation."})
        await task.queue_frames([LLMRunFrame()])

    # Capture session_id for cleanup in disconnect handler (only set for advisory calls)
    _cleanup_session_id = _active_call_sessions.get(farmer_id)

    @transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, client):
        logger.info(f"Client disconnected from {call_type} call (farmer: {farmer_id})")
        # Cleanup active call session mapping
        _active_call_sessions.pop(farmer_id, None)
        if _cleanup_session_id:
            try:
                from bot_advisory import unregister_session as _unreg
                _unreg(_cleanup_session_id)
            except Exception:
                pass
        await task.cancel()

    # --- Run ---
    runner = PipelineRunner(handle_sigint=False)
    await runner.run(task)
    logger.info(f"{call_type} pipeline finished for farmer {farmer_id}")


# ============================================================
# App Lifecycle
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("KrishiRin backend starting...")
    yield
    logger.info("KrishiRin backend shutting down...")
    # Disconnect all WebRTC peers
    coros = [pc.disconnect() for pc in pcs_map.values()]
    await asyncio.gather(*coros)
    pcs_map.clear()
    from databricks_client import db
    db.close()


app = FastAPI(
    title="KrishiRin API",
    description="Grameen Credit Advisory Backend",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# SmallWebRTC Offer Endpoint (THE voice connection point)
# ============================================================

@app.post("/api/offer")
async def offer(request: Request, background_tasks: BackgroundTasks):
    """WebRTC offer/answer exchange for Pipecat voice calls.

    The frontend sends an SDP offer, we create a SmallWebRTCConnection,
    launch the Pipecat pipeline in a background task, and return the SDP answer.
    """
    try:
        from pipecat.transports.smallwebrtc.connection import IceServer, SmallWebRTCConnection
    except ImportError as e:
        logger.error(f"Pipecat not installed: {e}")
        raise HTTPException(status_code=503, detail="Voice pipeline dependencies not available")

    # Parse body as JSON
    body = await request.json()

    ice_servers = [IceServer(urls="stun:stun.l.google.com:19302")]

    pc_id = body.get("pc_id")

    # Determine call type and farmer_id — try query params first (reliable),
    # then fall back to body fields (SmallWebRTC may or may not forward these)
    qp = request.query_params
    call_type = qp.get("call_type") or body.get("call_type") or body.get("callType") or "advisory"
    farmer_id = qp.get("farmer_id") or body.get("farmer_id") or body.get("farmerId") or ""
    logger.info(f"Resolved call_type={call_type}, farmer_id={farmer_id}")

    try:
        if pc_id and pc_id in pcs_map:
            # Renegotiation for existing connection
            pipecat_connection = pcs_map[pc_id]
            logger.info(f"Renegotiating connection for pc_id: {pc_id}")
            await pipecat_connection.renegotiate(
                sdp=body["sdp"],
                type=body["type"],
                restart_pc=body.get("restart_pc", False),
            )
        else:
            # New connection
            pipecat_connection = SmallWebRTCConnection(ice_servers)
            await pipecat_connection.initialize(sdp=body["sdp"], type=body["type"])

            @pipecat_connection.event_handler("closed")
            async def handle_disconnected(webrtc_connection: SmallWebRTCConnection):
                logger.info(f"Discarding peer connection: {webrtc_connection.pc_id}")
                pcs_map.pop(webrtc_connection.pc_id, None)

            # Launch the voice pipeline in the background
            background_tasks.add_task(run_voice_pipeline, pipecat_connection, call_type, farmer_id)

        answer = pipecat_connection.get_answer()
        pcs_map[answer["pc_id"]] = pipecat_connection

        return answer
    except Exception as e:
        logger.error(f"WebRTC offer failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to establish voice connection: {str(e)}")


# ============================================================
# Application APIs (kept from before)
# ============================================================

@app.post("/api/application")
async def create_application(data: dict):
    farmer_id = f"farmer_{uuid.uuid4().hex[:8]}"
    applications[farmer_id] = {
        "farmer_id": farmer_id,
        "phase": "apply",
        "farmer_data": data,
        "documents": [],
        "ml_status": "pending",
    }
    return {"farmer_id": farmer_id}


@app.post("/api/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    doc_type: str = Form(...),
    farmer_id: str = Form(...),
):
    from ocr_service import process_document, merge_ocr_into_farmer_data

    doc_id = f"doc_{uuid.uuid4().hex[:8]}"
    os.makedirs("uploads", exist_ok=True)
    file_path = f"uploads/{doc_id}_{file.filename}"
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # Run GPT-4o-mini Vision OCR
    ocr_result = process_document(file_path, doc_type, farmer_id)
    logger.info(f"OCR result for {doc_type}/{farmer_id}: status={ocr_result['status']}")

    # Auto-create application entry if it doesn't exist yet (handles upload-before-save flow)
    if farmer_id not in applications:
        applications[farmer_id] = {
            "farmer_id": farmer_id,
            "phase": "apply",
            "farmer_data": {},
            "documents": [],
            "ml_status": "pending",
        }

    if farmer_id in applications:
        app_data = applications[farmer_id]

        # Store document record
        app_data["documents"].append({
            "id": doc_id,
            "type": doc_type,
            "filename": file.filename,
            "status": "verified" if ocr_result["status"] == "success" else "uploaded",
            "path": file_path,
        })

        # Store OCR result — support multiple docs per type
        ocr_store = app_data.setdefault("ocr_results", {})
        if doc_type in ("land_record", "loan_slip", "bank_statement", "crop_receipt"):
            # Accumulate: store as list
            existing = ocr_store.get(doc_type)
            if isinstance(existing, list):
                existing.append(ocr_result)
            elif existing:
                ocr_store[doc_type] = [existing, ocr_result]
            else:
                ocr_store[doc_type] = ocr_result
        else:
            # Single doc types (aadhaar): overwrite
            ocr_store[doc_type] = ocr_result

        # Merge extracted data into farmer profile for immediate dashboard display
        app_data["farmer_data"] = merge_ocr_into_farmer_data(
            app_data.get("farmer_data", {}),
            app_data["ocr_results"],
        )

    return {
        "document_id": doc_id,
        "status": "verified" if ocr_result["status"] == "success" else "uploaded",
        "extracted_data": ocr_result.get("extracted_data", {}),
        "confidence": ocr_result.get("confidence", 0),
    }


async def run_precall_pipeline(farmer_id: str):
    """Run the precall ADK agent pipeline in the background."""
    try:
        import time as _time
        from google.adk.runners import Runner
        from google.adk.sessions import InMemorySessionService
        from google.genai import types as genai_types
        from krishirin_agents.precall.coordinator.agent import root_agent

        pipeline_start = _time.time()
        logger.info(f"[PIPELINE] Starting precall pipeline for {farmer_id}")
        pipeline_statuses[farmer_id] = {"overall_progress": 10, "status": "running"}

        # Build initial state with OCR-extracted data for agent tools
        app_data = applications.get(farmer_id, {})
        initial_state = {
            "farmer_id": farmer_id,
            "ocr_farmer_data": app_data.get("farmer_data", {}),
            "ocr_results": app_data.get("ocr_results", {}),
        }

        session_service = InMemorySessionService()
        runner = Runner(
            agent=root_agent,
            app_name="krishirin_precall",
            session_service=session_service,
        )
        session = await session_service.create_session(
            app_name="krishirin_precall",
            user_id="system",
            state=initial_state,
        )

        msg = genai_types.Content(
            role="user",
            parts=[genai_types.Part.from_text(text=f"Run analysis for farmer {farmer_id}")],
        )

        # Map output_keys to human-readable agent names for logging
        _AGENT_NAMES = {
            "farmer_context": "Data Loader",
            "credit_assessment": "ML Credit Scoring",
            "risk_flags": "Risk Analysis",
            "market_research": "Crop & Market Analysis",
            "gap_analysis": "Gap Analysis & Insights",
            "precall_analysis": "Final Synthesis",
        }

        collected_keys = set()
        # Ensure _pipeline_state exists for intermediate result storage
        if farmer_id in applications:
            applications[farmer_id].setdefault("_pipeline_state", {})

        async for event in runner.run_async(
            user_id="system", session_id=session.id, new_message=msg
        ):
            if hasattr(event, "actions") and event.actions:
                state_delta = getattr(event.actions, "state_delta", None)
                if state_delta and isinstance(state_delta, dict):
                    for key, value in state_delta.items():
                        if key not in collected_keys:
                            agent_name = _AGENT_NAMES.get(key, key)
                            elapsed = round(_time.time() - pipeline_start, 1)
                            logger.info(f"[PIPELINE] ✓ {agent_name} [{elapsed}s]")
                            # Store intermediate result immediately
                            if farmer_id in applications and key in _AGENT_NAMES:
                                applications[farmer_id]["_pipeline_state"][key] = value
                    collected_keys.update(state_delta.keys())
                    progress = min(10 + len(collected_keys) * 12, 95)
                    pipeline_statuses[farmer_id] = {
                        "overall_progress": progress,
                        "status": "running",
                        "completed_agents": list(collected_keys),
                        "completed_agent_names": [_AGENT_NAMES.get(k, k) for k in collected_keys],
                    }

        # Collect final state from session
        updated_session = await session_service.get_session(
            app_name="krishirin_precall", user_id="system", session_id=session.id
        )
        if updated_session and updated_session.state:
            state = updated_session.state
            precall_result = state.get("precall_analysis")
            if farmer_id in applications:
                applications[farmer_id]["ml_status"] = "complete"
                applications[farmer_id]["phase"] = "ready"
                applications[farmer_id]["precall_result"] = precall_result
                # Store all intermediate agent outputs for the results endpoint
                applications[farmer_id]["_pipeline_state"] = {
                    k: v for k, v in state.items()
                    if k in (
                        "farmer_context", "credit_assessment", "risk_flags",
                        "market_research", "eligibility_report", "gap_analysis",
                        "loan_strategy", "precall_analysis",
                        "scheme_rag_results", "scheme_web_results", "eligibility_evaluation",
                    )
                }

        total_time = round(_time.time() - pipeline_start, 1)
        pipeline_statuses[farmer_id] = {"overall_progress": 100, "status": "complete"}
        logger.info(f"[PIPELINE] Precall pipeline completed for {farmer_id} in {total_time}s")

    except Exception as e:
        logger.error(f"Precall pipeline failed for {farmer_id}: {e}", exc_info=True)
        pipeline_statuses[farmer_id] = {"overall_progress": 0, "status": "error", "error": str(e)}
        if farmer_id in applications:
            applications[farmer_id]["ml_status"] = "error"


@app.post("/api/application/{farmer_id}/analyze")
async def trigger_analysis(farmer_id: str, background_tasks: BackgroundTasks):
    if farmer_id in applications:
        applications[farmer_id]["ml_status"] = "running"
        applications[farmer_id]["phase"] = "analysis"
    background_tasks.add_task(run_precall_pipeline, farmer_id)
    return {"status": "analysis_started"}


@app.get("/api/application/{farmer_id}/status")
async def get_application_status(farmer_id: str):
    if farmer_id in applications:
        return applications[farmer_id]
    return {"farmer_id": farmer_id, "phase": "apply", "ml_status": "pending"}


@app.get("/api/application/{farmer_id}/briefing")
async def get_pre_call_briefing(farmer_id: str):
    """Returns pre-call briefing data for the understanding call.

    Priority: OCR-extracted data from uploaded documents > Databricks > Mock data.
    If ML models haven't run yet (no precall_result), score section is partial.
    """
    # Check if we have OCR-enriched data from document uploads
    app_data = applications.get(farmer_id, {})
    farmer_data = app_data.get("farmer_data", {})
    precall_result = app_data.get("precall_result")
    ocr_results = app_data.get("ocr_results", {})

    # If we have OCR-extracted data, use it
    if farmer_data and any(ocr_results.values()):
        farmer_profile = {
            "farmer_id": farmer_id,
            "name": farmer_data.get("name", "Unknown"),
            "aadhaar_last4": farmer_data.get("aadhaar_last4", ""),
            "district": farmer_data.get("district", ""),
            "state": farmer_data.get("state", ""),
            "land_holding_acres": farmer_data.get("land_holding_acres", 0),
            "land_type": farmer_data.get("land_type", "unknown"),
            "crops": farmer_data.get("crops", []),
            "existing_loans": farmer_data.get("existing_loans", []),
            "govt_schemes": farmer_data.get("govt_schemes", []),
            "bank_summary": farmer_data.get("bank_summary", {}),
            "data_completeness": farmer_data.get("data_completeness", {}),
        }

        # Try to get score from multiple sources
        pipeline_state = app_data.get("_pipeline_state", {})
        synthesis = _parse_agent_output(precall_result) if precall_result else {}

        # Priority 1: synthesis score_summary
        score = _parse_agent_output(synthesis.get("score_summary")) if isinstance(synthesis, dict) else {}
        # Priority 2: raw credit_assessment from pipeline state
        if not score or not isinstance(score, dict) or not score.get("grameen_score"):
            credit = _parse_agent_output(pipeline_state.get("credit_assessment"))
            if isinstance(credit, dict) and credit.get("grameen_score"):
                score = credit
        # Priority 3: nothing yet
        if not score or not isinstance(score, dict) or not score.get("grameen_score"):
            score = {"grameen_score": None, "risk_category": None, "status": "pending_analysis"}

        flags = (synthesis.get("risk_flags", []) if isinstance(synthesis, dict) else []) or _parse_agent_output(pipeline_state.get("risk_flags"))
        auto_qs = synthesis.get("clarification_questions", []) if isinstance(synthesis, dict) else []

        return {
            "farmer": farmer_profile,
            "score": score,
            "flags": flags if isinstance(flags, list) else [],
            "auto_questions": auto_qs if isinstance(auto_qs, list) else [],
            "ocr_complete": True,
            "ml_complete": precall_result is not None,
        }

    # No OCR data available — return empty briefing (no hardcoded mock data)
    return {
        "farmer": {
            "farmer_id": farmer_id,
            "name": farmer_data.get("name", ""),
            "aadhaar_last4": farmer_data.get("aadhaar_last4", ""),
            "district": farmer_data.get("district", ""),
            "state": farmer_data.get("state", ""),
            "land_holding_acres": farmer_data.get("land_holding_acres", 0),
            "land_type": farmer_data.get("land_type", ""),
            "crops": farmer_data.get("crops", []),
            "existing_loans": farmer_data.get("existing_loans", []),
            "govt_schemes": farmer_data.get("govt_schemes", []),
            "bank_summary": farmer_data.get("bank_summary", {}),
        },
        "score": {"grameen_score": None, "risk_category": None, "status": "no_data"},
        "flags": [],
        "auto_questions": [],
        "ocr_complete": False,
        "ml_complete": False,
    }


@app.post("/api/application/{farmer_id}/call1-complete")
async def mark_call1_complete(farmer_id: str):
    if farmer_id in applications:
        applications[farmer_id]["phase"] = "processing"
    return {"status": "call1_complete"}


@app.get("/api/application/{farmer_id}/pipeline-status")
async def get_pipeline_status(farmer_id: str):
    if farmer_id in pipeline_statuses:
        return pipeline_statuses[farmer_id]
    return {
        "agents": [
            {"name": "EligibilityChecker", "status": "pending"},
            {"name": "GrameenScorer", "status": "pending"},
            {"name": "GapAnalyzer", "status": "pending"},
            {"name": "StrategyArchitect", "status": "pending"},
            {"name": "AgriAdvisor", "status": "pending"},
        ],
        "overall_progress": 0,
    }


@app.get("/api/application/{farmer_id}/results")
async def get_results(farmer_id: str):
    """Returns normalized agent outputs for the farmer.

    Merges data from both synthesis output (precall_result) and intermediate
    agent outputs (_pipeline_state), using whichever has more complete data.
    """
    app_data = applications.get(farmer_id, {})
    state = app_data.get("_pipeline_state", {})
    synthesis = _parse_agent_output(app_data.get("precall_result"))
    is_complete = app_data.get("ml_status") == "complete"

    if not state and not synthesis:
        return {"pipeline_complete": False, "status": "pending"}

    # Credit assessment (ML scores)
    credit = _parse_agent_output(synthesis.get("credit_assessment_summary")) if isinstance(synthesis, dict) else {}
    if not credit or not isinstance(credit, dict) or not credit.get("grameen_score"):
        credit = _parse_agent_output(state.get("credit_assessment"))

    # Risk analysis
    risk = _parse_agent_output(synthesis.get("risk_analysis")) if isinstance(synthesis, dict) else {}
    if not risk or not isinstance(risk, dict) or len(risk) == 0:
        risk = _parse_agent_output(state.get("risk_flags"))

    # Agricultural / market analysis
    agri = _parse_agent_output(synthesis.get("agricultural_analysis")) if isinstance(synthesis, dict) else {}
    if not agri or not isinstance(agri, dict) or len(agri) == 0:
        agri = _parse_agent_output(state.get("market_research"))

    # Gap analysis & actionable insights
    gaps = _parse_agent_output(synthesis.get("gap_analysis")) if isinstance(synthesis, dict) else {}
    if not gaps or not isinstance(gaps, dict) or len(gaps) == 0:
        gaps = _parse_agent_output(state.get("gap_analysis"))

    return {
        "credit_assessment": credit if isinstance(credit, dict) else {},
        "risk_analysis": risk if isinstance(risk, (dict, list)) else {},
        "agricultural_analysis": agri if isinstance(agri, dict) else {},
        "gap_analysis": gaps if isinstance(gaps, dict) else {},
        "farmer_summary": _stringify_if_object(synthesis.get("farmer_summary", "")) if isinstance(synthesis, dict) else "",
        "clarification_questions": _normalize_list_of_strings(synthesis.get("clarification_questions", [])) if isinstance(synthesis, dict) else [],
        "voice_agent_briefing": synthesis.get("voice_agent_briefing", "") if isinstance(synthesis, dict) else "",
        "pipeline_complete": is_complete,
        "agents_done": list(state.keys()),
    }


def _stringify_if_object(val) -> str:
    """Convert an object to a readable string if it's not already a string."""
    if isinstance(val, str):
        return val
    if isinstance(val, dict):
        parts = []
        for k, v in val.items():
            parts.append(f"{k}: {v if isinstance(v, str) else json.dumps(v, default=str)}")
        return " · ".join(parts)
    return str(val) if val else ""


def _normalize_list_of_strings(val) -> list[str]:
    """Ensure a list contains only strings (agent may return list of objects)."""
    if not isinstance(val, list):
        return []
    result = []
    for item in val:
        if isinstance(item, str):
            result.append(item)
        elif isinstance(item, dict):
            result.append(item.get("question") or item.get("text") or json.dumps(item, default=str))
        else:
            result.append(str(item))
    return result


def _parse_agent_output(raw) -> dict | list | str:
    """Parse agent output which may be a JSON string, dict, list, or None."""
    if raw is None:
        return {}
    if isinstance(raw, (dict, list)):
        return raw
    if isinstance(raw, str):
        # Try to extract JSON from the string (may have markdown or preamble)
        text = raw.strip()
        # Strip markdown code fences
        if text.startswith("```"):
            lines = text.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            text = "\n".join(lines).strip()
        # Try parsing as JSON
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Try finding JSON object in the text
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                try:
                    return json.loads(text[start:end])
                except json.JSONDecodeError:
                    pass
            return {"raw_text": raw[:2000]}
    return {}


@app.get("/api/application/{farmer_id}/transcripts")
async def get_transcripts(farmer_id: str):
    return {"call1": "", "call2": ""}


# ============================================================
# SSE: Stream on-call agent results to frontend
# ============================================================

@app.get("/api/events/{farmer_id}")
async def agent_events_stream(farmer_id: str):
    """SSE stream of on-call agent completion events for the frontend side panel.

    Keeps the connection open and waits for the call session to start,
    then streams agent completion events in real-time.
    """
    import json
    from fastapi.responses import StreamingResponse

    try:
        from krishirin_agents.voice_server.oncall_runner import get_event_queue
    except ImportError:
        get_event_queue = None

    async def event_stream():
        # Wait for call to start (poll for session_id, up to 120s)
        session_id = None
        for _ in range(120):
            session_id = _active_call_sessions.get(farmer_id)
            if session_id:
                break
            yield f"data: {json.dumps({'type': 'waiting'})}\n\n"
            await asyncio.sleep(1)

        if not session_id:
            yield f"data: {json.dumps({'type': 'no_session'})}\n\n"
            return

        if not get_event_queue:
            yield f"data: {json.dumps({'type': 'pipeline_error', 'error': 'Agent pipeline not available'})}\n\n"
            return

        logger.info(f"SSE connected for {farmer_id}, session {session_id}")

        # Stream real events from the queue
        try:
            queue = get_event_queue(session_id)
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30)
                    yield f"data: {json.dumps(event, default=str)}\n\n"
                    if event.get("type") in ("pipeline_complete", "pipeline_error"):
                        break
                except asyncio.TimeoutError:
                    # Check if session is still active; if not, end the stream
                    if farmer_id not in _active_call_sessions:
                        yield f"data: {json.dumps({'type': 'pipeline_complete'})}\n\n"
                        break
                    yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"
        except Exception as e:
            logger.error(f"SSE stream error for {farmer_id}: {e}")
            yield f"data: {json.dumps({'type': 'pipeline_error', 'error': str(e)})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": "*",
        },
    )


@app.get("/api/call/{farmer_id}/session")
async def get_call_session(farmer_id: str):
    """Get the active call session ID for a farmer (used by frontend for SSE)."""
    session_id = _active_call_sessions.get(farmer_id)
    return {"session_id": session_id, "active": session_id is not None}


@app.get("/api/health")
async def health():
    from databricks_client import db
    return {"status": "ok", "databricks_configured": db.is_configured}


if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host=host, port=port, access_log=False)
