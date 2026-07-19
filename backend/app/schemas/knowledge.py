"""
Knowledge Base Schemas — Pydantic Models

Request/response schemas for KB CRUD, search, and ingestion endpoints.
"""

from datetime import datetime
from pydantic import BaseModel, Field


# --- Request Schemas ---
class KBRecordCreate(BaseModel):
    """Schema for creating a new KB record."""
    record_id: str = Field(..., description="Human-readable ID, e.g., kb_loan_policy_001")
    title: str = Field(..., max_length=500)
    content: str
    category: str = Field(..., description="product | policy | faq | objection | compliance | payment | escalation")
    subcategory: str | None = None
    source: str = Field(..., description="website | pdf | manual | csv")
    source_url: str | None = None
    version: str = "1.0"
    metadata: dict | None = None
    language: str = "en"


class KBRecordUpdate(BaseModel):
    """Schema for updating a KB record."""
    title: str | None = None
    content: str | None = None
    category: str | None = None
    subcategory: str | None = None
    metadata: dict | None = None
    version: str | None = None


class KBSearchRequest(BaseModel):
    """Schema for searching the knowledge base."""
    query: str = Field(..., min_length=3, description="Search query text")
    category: str | None = Field(None, description="Filter by category")
    product_type: str | None = Field(None, description="Filter by product type")
    language: str | None = Field(None, description="Filter by language")
    market: str | None = Field(None, description="Filter by market")
    top_k: int = Field(5, ge=1, le=20, description="Number of results to return")


class KBIngestRequest(BaseModel):
    """Schema for ingesting a batch of KB records."""
    records: list[KBRecordCreate]
    embed: bool = Field(True, description="Whether to generate embeddings")
    detect_pii: bool = Field(True, description="Whether to run PII detection")


# --- Response Schemas ---
class KBRecordResponse(BaseModel):
    """Schema for a KB record response."""
    id: str
    record_id: str
    title: str
    content: str
    content_clean: str | None
    category: str
    subcategory: str | None
    source: str
    source_url: str | None
    version: str
    contains_pii: bool
    metadata: dict | None
    chunk_id: str | None
    parent_doc_id: str | None
    token_count: int | None
    language: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class KBSearchResult(BaseModel):
    """Schema for a single search result."""
    record_id: str
    title: str
    content: str
    category: str
    source: str
    source_url: str | None
    relevance_score: float = Field(..., description="Cosine similarity score")
    metadata: dict | None


class KBSearchResponse(BaseModel):
    """Schema for search results."""
    query: str
    results: list[KBSearchResult]
    total: int
    retrieval_time_ms: float


class KBRetrievalTest(BaseModel):
    """Schema for a KB retrieval test result (Q2 evaluation)."""
    query: str
    retrieved_record: KBSearchResult
    source_reference: str
    relevance_explanation: str
    verdict: str = Field(..., description="correct | partially_correct | incorrect")
