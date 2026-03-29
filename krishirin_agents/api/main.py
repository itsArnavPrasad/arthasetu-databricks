"""
FastAPI endpoint for the KrishiRin Pre-Call Analysis Pipeline.

Usage (standalone — same pattern as voice_server/server.py):
    cd /Users/anmolsureka/Documents/Databricks Hack
    python -m uvicorn krishirin_agents.api.main:app --host 0.0.0.0 --port 8001

    POST /analysis/{farmer_id}
    → Runs the full pre-call analysis pipeline
    → Returns the complete PreCallAnalysis JSON

    POST /analysis/{farmer_id}/with-ocr
    → Same but accepts OCR-extracted farmer data in request body
"""

import logging
import sys
import os
from contextlib import asynccontextmanager
from typing import Optional

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

from krishirin_agents.precall.coordinator.agent import root_agent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

session_service = InMemorySessionService()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("KrishiRin Pre-Call Analysis API starting...")
    yield
    logger.info("KrishiRin Pre-Call Analysis API shutting down.")


app = FastAPI(
    title="KrishiRin Pre-Call Analysis API",
    description="AI-powered Grameen Credit Advisory — Pre-Call Analysis Pipeline",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class OCRAnalysisRequest(BaseModel):
    """Request body for analysis with OCR-extracted data."""
    ocr_farmer_data: Optional[dict] = None
    ocr_results: Optional[dict] = None


async def _run_pipeline(farmer_id: str, initial_state: dict) -> dict:
    """Run the precall pipeline with given initial state."""
    session = await session_service.create_session(
        app_name="krishirin_precall",
        user_id="system",
        state=initial_state,
    )

    runner = Runner(
        agent=root_agent,
        app_name="krishirin_precall",
        session_service=session_service,
    )

    collected_keys = set()
    async for event in runner.run_async(
        user_id="system",
        session_id=session.id,
        new_message_text=f"Run complete pre-call analysis for farmer {farmer_id}",
    ):
        if hasattr(event, "actions") and event.actions:
            state_delta = getattr(event.actions, "state_delta", None)
            if state_delta and isinstance(state_delta, dict):
                collected_keys.update(state_delta.keys())
                logger.info(f"Agent output: {list(state_delta.keys())}")

    # Get the final analysis from session state
    updated_session = await session_service.get_session(
        app_name="krishirin_precall",
        user_id="system",
        session_id=session.id,
    )

    return updated_session.state


@app.post("/analysis/{farmer_id}")
async def run_analysis(farmer_id: str):
    """Run the complete pre-call analysis pipeline for a farmer.

    Uses data from Delta tables / sample data (no OCR input).
    """
    logger.info(f"Starting pre-call analysis for farmer_id={farmer_id}")

    try:
        final_state = await _run_pipeline(farmer_id, {"farmer_id": farmer_id})

        precall_analysis = final_state.get("precall_analysis")
        if precall_analysis is None:
            raise HTTPException(
                status_code=500,
                detail="Pipeline completed but precall_analysis not found in state",
            )

        logger.info(f"Pre-call analysis completed for farmer_id={farmer_id}")
        return {"status": "success", "farmer_id": farmer_id, "analysis": precall_analysis}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Pipeline failed for farmer_id={farmer_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Pipeline error: {str(e)}")


@app.post("/analysis/{farmer_id}/with-ocr")
async def run_analysis_with_ocr(farmer_id: str, body: OCRAnalysisRequest):
    """Run the pre-call analysis pipeline with OCR-extracted farmer data.

    Agents will use the OCR data for ML scoring (Databricks endpoints)
    and crop predictions (local models).
    """
    logger.info(f"Starting OCR-aware pre-call analysis for farmer_id={farmer_id}")

    try:
        initial_state = {
            "farmer_id": farmer_id,
            "ocr_farmer_data": body.ocr_farmer_data or {},
            "ocr_results": body.ocr_results or {},
        }

        final_state = await _run_pipeline(farmer_id, initial_state)

        precall_analysis = final_state.get("precall_analysis")
        credit_assessment = final_state.get("credit_assessment")
        market_research = final_state.get("market_research")

        if precall_analysis is None:
            # Return partial results if synthesis agent didn't run
            return {
                "status": "partial",
                "farmer_id": farmer_id,
                "credit_assessment": credit_assessment,
                "market_research": market_research,
                "available_keys": [k for k in final_state.keys() if not k.startswith("_")],
            }

        logger.info(f"Pre-call analysis completed for farmer_id={farmer_id}")
        return {"status": "success", "farmer_id": farmer_id, "analysis": precall_analysis}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Pipeline failed for farmer_id={farmer_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Pipeline error: {str(e)}")


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "krishirin_precall_analysis"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
