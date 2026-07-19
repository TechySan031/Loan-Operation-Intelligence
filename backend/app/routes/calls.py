"""
Call Management Routes

Endpoints for viewing and managing call records:
- GET /calls — List calls with pagination and filtering
- GET /calls/{call_id} — Get call details with events and nudges
- GET /calls/{call_id}/transcript — Get full transcript
- GET /calls/{call_id}/events — Get call event timeline
- GET /calls/analytics — Call analytics summary
"""

import logging
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.call import CallResponse, CallListResponse, CallEventResponse
from app.services.call_service import CallService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", response_model=CallListResponse)
async def list_calls(
    status: str | None = Query(None),
    outcome: str | None = Query(None),
    market: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List calls with optional filtering and pagination."""
    service = CallService(db)
    return await service.list_calls(
        status=status, outcome=outcome, market=market,
        page=page, page_size=page_size,
    )


@router.get("/{call_id}", response_model=CallResponse)
async def get_call(
    call_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get full call details including event and nudge counts."""
    service = CallService(db)
    call = await service.get_call(call_id)
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    return call


@router.get("/{call_id}/transcript")
async def get_transcript(
    call_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get the full conversation transcript for a call."""
    service = CallService(db)
    transcript = await service.get_transcript(call_id)
    if transcript is None:
        raise HTTPException(status_code=404, detail="Transcript not found")
    return {"call_id": call_id, "transcript": transcript}


@router.get("/{call_id}/events")
async def get_call_events(
    call_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get the event timeline for a call (state changes, tool calls, etc.)."""
    service = CallService(db)
    events = await service.get_events(call_id)
    return {"call_id": call_id, "events": events}


@router.get("/analytics/summary")
async def call_analytics(
    market: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Call analytics summary:
    - Total calls, completion rate, outcome breakdown
    - Average duration, sentiment distribution
    - Escalation rate, commitment rate
    """
    service = CallService(db)
    return await service.get_analytics(market=market)
