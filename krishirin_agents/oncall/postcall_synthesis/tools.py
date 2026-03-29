import logging
from datetime import datetime
from google.adk.tools.tool_context import ToolContext

import sys, os
_d = os.path.dirname
sys.path.insert(0, _d(_d(_d(_d(os.path.abspath(__file__))))))
from krishirin_agents.shared.config import USE_SAMPLE_DATA

logger = logging.getLogger(__name__)


def write_postcall_to_delta(tool_context: ToolContext, farmer_id: str, analysis_json: str) -> dict:
    """Write post-call analysis to the postcall_analysis Delta table.

    Args:
        farmer_id: The farmer's unique identifier
        analysis_json: Complete post-call analysis as JSON string
    """
    timestamp = datetime.utcnow().isoformat()
    if USE_SAMPLE_DATA:
        logger.info(f"[SAMPLE MODE] Post-call analysis for {farmer_id} logged at {timestamp}")
        return {"status": "success", "message": f"Post-call analysis saved (sample mode)", "timestamp": timestamp}

    try:
        from krishirin_agents.shared import delta_client
        escaped = analysis_json.replace("'", "''")
        delta_client.execute_write(
            f"INSERT INTO krishirin.loan_advisory.postcall_analysis (farmer_id, analysis, generated_at) "
            f"VALUES ('{farmer_id}', '{escaped}', '{timestamp}')"
        )
        return {"status": "success", "message": f"Written to Delta", "timestamp": timestamp}
    except Exception as e:
        return {"status": "error", "message": str(e)}
