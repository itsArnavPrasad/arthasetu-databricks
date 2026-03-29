import json
import logging
import numpy as np
from .config import FAISS_INDEX_PATH, FAISS_CHUNKS_PATH

logger = logging.getLogger(__name__)

_index = None
_chunks = None
_model = None


def _load_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def _load_index():
    global _index, _chunks
    if _index is None:
        import faiss
        _index = faiss.read_index(FAISS_INDEX_PATH)
        with open(FAISS_CHUNKS_PATH, "r") as f:
            _chunks = json.load(f)
    return _index, _chunks


def search(query: str, top_k: int = 5) -> list[dict]:
    """Search FAISS index for relevant scheme document chunks."""
    model = _load_model()
    index, chunks = _load_index()

    embedding = model.encode([query], normalize_embeddings=True)
    distances, indices = index.search(
        np.array(embedding, dtype=np.float32), top_k
    )

    results = []
    for i, idx in enumerate(indices[0]):
        if idx < len(chunks) and idx >= 0:
            results.append({
                "chunk_text": chunks[idx]["text"],
                "source": chunks[idx].get("source", "unknown"),
                "scheme_name": chunks[idx].get("scheme_name", ""),
                "score": float(distances[0][i]),
            })
    return results
