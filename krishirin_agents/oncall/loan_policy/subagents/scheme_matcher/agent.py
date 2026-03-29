import sys, os
_d = os.path.dirname
sys.path.insert(0, _d(_d(_d(_d(_d(_d(os.path.abspath(__file__))))))))

from google.adk.agents import LlmAgent
from google.adk.tools.tool_context import ToolContext
from .prompt import SCHEME_MATCHER_INSTRUCTION
from krishirin_agents.shared.config import MODEL_FAST, USE_SAMPLE_DATA
from krishirin_agents.shared.sample_data import SAMPLE_SCHEME_CHUNKS


def faiss_scheme_search(tool_context: ToolContext, query: str, top_k: int = 5) -> dict:
    """Search FAISS index of government scheme documents."""
    if USE_SAMPLE_DATA:
        query_lower = query.lower()
        scored = []
        for chunk in SAMPLE_SCHEME_CHUNKS:
            words = query_lower.split()
            score = sum(1 for w in words if w in chunk["text"].lower()) / max(len(words), 1)
            scored.append({**chunk, "score": round(score, 3)})
        scored.sort(key=lambda x: x["score"], reverse=True)
        return {"status": "success", "results": scored[:top_k], "query": query}
    from krishirin_agents.shared import faiss_client
    return {"status": "success", "results": faiss_client.search(query, top_k=top_k), "query": query}


scheme_matcher_agent = LlmAgent(
    name="scheme_matcher_agent",
    model=MODEL_FAST,
    description="Matches farmer to all applicable government schemes with exact terms and eligibility.",
    instruction=SCHEME_MATCHER_INSTRUCTION,
    tools=[faiss_scheme_search],
    output_key="scheme_matches",
)
