from pydantic import BaseModel, Field
from typing import Optional


class SchemeWebResult(BaseModel):
    scheme_name: str
    info: str = Field(..., description="Key information found about the scheme")
    source_url: Optional[str] = None
    last_updated: Optional[str] = None


class SchemeWebResults(BaseModel):
    queries_used: list[str] = Field(..., description="Google search queries executed")
    results: list[SchemeWebResult] = Field(
        default_factory=list, description="Scheme information from web search"
    )
    summary: str = Field(
        ..., description="Brief summary of latest scheme updates found"
    )
