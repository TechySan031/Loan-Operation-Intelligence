"""
Knowledge Base Routes (Q2)

CRUD and search endpoints for the knowledge base:
- POST /ingest — Bulk ingest KB records (parse, clean, chunk, embed, store)
- GET /search — RAG search with metadata filtering
- GET /records — List all records with pagination
- GET /records/{record_id} — Get a single record
- PUT /records/{record_id} — Update a record
- DELETE /records/{record_id} — Delete a record
- GET /retrieval-test — Run the 5+ retrieval test queries
"""

import logging
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.knowledge import (
    KBRecordCreate, KBRecordUpdate, KBRecordResponse,
    KBSearchRequest, KBSearchResponse, KBIngestRequest,
    KBRetrievalTest,
)
from app.services.knowledge_service import KnowledgeService
from app.services.rag_service import RAGService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/ingest")
async def ingest_records(
    request: KBIngestRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Bulk ingest KB records.
    
    Pipeline: validate → PII detect → chunk → embed → store in Postgres + Pinecone
    """
    service = KnowledgeService(db)
    result = await service.ingest_records(
        records=request.records,
        embed=request.embed,
        detect_pii_flag=request.detect_pii,
    )
    return result


@router.post("/search", response_model=KBSearchResponse)
async def search_knowledge_base(
    request: KBSearchRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Search the knowledge base using RAG.
    
    Pipeline: embed query → Pinecone similarity search → metadata filter → rerank → return with citations
    """
    rag_service = RAGService(db)
    results = await rag_service.search(
        query=request.query,
        category=request.category,
        product_type=request.product_type,
        language=request.language,
        market=request.market,
        top_k=request.top_k,
    )
    return results


@router.get("/records")
async def list_records(
    category: str | None = Query(None),
    language: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List KB records with optional filtering and pagination."""
    service = KnowledgeService(db)
    return await service.list_records(
        category=category,
        language=language,
        page=page,
        page_size=page_size,
    )


@router.get("/records/{record_id}", response_model=KBRecordResponse)
async def get_record(
    record_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a single KB record by record_id."""
    service = KnowledgeService(db)
    record = await service.get_record(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    return record


@router.put("/records/{record_id}", response_model=KBRecordResponse)
async def update_record(
    record_id: str,
    update: KBRecordUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a KB record and re-embed if content changed."""
    service = KnowledgeService(db)
    record = await service.update_record(record_id, update)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    return record


@router.delete("/records/{record_id}")
async def delete_record(
    record_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete a KB record and its vector from Pinecone."""
    service = KnowledgeService(db)
    await service.delete_record(record_id)
    return {"status": "deleted", "record_id": record_id}


@router.get("/retrieval-test")
async def run_retrieval_test(
    db: AsyncSession = Depends(get_db),
):
    """
    Run the Q2 retrieval test: 5+ queries with verdicts.
    
    Returns: query, retrieved chunk, source reference, 
    relevance explanation, and verdict for each test case.
    """
    rag_service = RAGService(db)
    results = await rag_service.run_retrieval_test()
    return results


@router.get("/stats")
async def kb_stats(
    db: AsyncSession = Depends(get_db),
):
    """Get knowledge base statistics (record count, category breakdown, etc.)."""
    service = KnowledgeService(db)
    return await service.get_stats()
