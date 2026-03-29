import sys, os; _d = os.path.dirname; sys.path.insert(0, _d(_d(_d(_d(os.path.abspath(__file__))))))
import json
import logging
from datetime import datetime
from google.adk.tools.tool_context import ToolContext
from krishirin_agents.shared.config import USE_SAMPLE_DATA

logger = logging.getLogger(__name__)


def write_analysis_to_delta(
    tool_context: ToolContext,
    farmer_id: str,
    analysis_json: str,
) -> dict:
    """Write the complete pre-call analysis to the precall_analysis Delta table.

    Args:
        farmer_id: The farmer's unique identifier
        analysis_json: Complete analysis as JSON string
    """
    logger.info(f"Writing pre-call analysis for {farmer_id}")
    timestamp = datetime.utcnow().isoformat()

    if USE_SAMPLE_DATA:
        logger.info(f"[SAMPLE MODE] Analysis for {farmer_id} logged at {timestamp} (not written to Delta)")
        return {
            "status": "success",
            "message": f"Analysis logged for {farmer_id} (sample mode — no Delta write)",
            "timestamp": timestamp,
        }

    try:
        from ..shared import delta_client
        from krishirin_agents.shared.config import TABLE_PRECALL_ANALYSIS
        escaped_json = analysis_json.replace("'", "''")
        sql = f"""
        INSERT INTO {TABLE_PRECALL_ANALYSIS}
        (farmer_id, analysis, generated_at)
        VALUES ('{farmer_id}', '{escaped_json}', '{timestamp}')
        """
        delta_client.execute_write(sql)
        return {
            "status": "success",
            "message": f"Analysis written to Delta for {farmer_id}",
            "timestamp": timestamp,
        }
    except Exception as e:
        logger.error(f"Failed to write to Delta: {e}")
        return {"status": "error", "message": str(e)}
