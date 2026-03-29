from pydantic import BaseModel, Field
from typing import Optional


class SchemeChunk(BaseModel):
    scheme_name: str
    chunk_text: str
    source: Optional[str] = None
    relevance_score: Optional[float] = None


class SchemeRAGResults(BaseModel):
    queries_used: list[str] = Field(..., description="RAG queries generated from farmer profile")
    chunks: list[SchemeChunk] = Field(
        default_factory=list, description="Retrieved scheme document chunks"
    )
    schemes_found: list[str] = Field(
        default_factory=list, description="Unique scheme names found in results"
    )
