"""
Nudge Routes — Real-time Nudge Streaming (Q4)

Endpoints for the live nudge system:
- GET /stream/{call_id} — SSE stream of real-time nudges for a call
- POST /session/start — Start a nudge processing session (live or simulated)
- POST /session/stop — Stop a nudge session
- GET /analysis/{call_id} — Nudge quality analysis for a call
- GET /latency-report — P50/P95 latency report across all calls
"""

import logging
import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.redis import subscribe_nudges
from app.schemas.nudge import (
    NudgeResponse, NudgeAnalysis, StartNudgeSessionRequest, LatencyReport,
)
from app.services.nudge_engine import NudgeEngine
from app.services.call_service import CallService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/stream/{call_id}")
async def stream_nudges(call_id: str):
    """
    SSE endpoint for real-time nudge delivery.
    
    Subscribes to Redis pub/sub channel for the given call_id
    and streams nudges as Server-Sent Events.
    
    Frontend connects via EventSource:
        const es = new EventSource(`/api/nudges/stream/${callId}`);
        es.onmessage = (e) => { const nudge = JSON.parse(e.data); ... };
    """
    async def event_generator():
        async for nudge_data in subscribe_nudges(call_id):
            yield f"data: {nudge_data}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/session/start")
async def start_nudge_session(
    request: StartNudgeSessionRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Start a real-time nudge processing session.
    
    For live calls: hooks into Vapi's real-time transcript stream.
    For simulation: replays audio file at real-time speed through Deepgram.
    
    The nudge engine processes the stream and publishes nudges
    to the Redis channel for the call_id.
    """
    engine = NudgeEngine(db)
    session_id = await engine.start_session(
        call_id=request.call_id,
        audio_source=request.audio_source,
        chunk_ms=request.chunk_ms,
    )
    return {"session_id": session_id, "call_id": request.call_id, "status": "started"}


@router.post("/session/stop")
async def stop_nudge_session(
    call_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Stop an active nudge processing session."""
    engine = NudgeEngine(db)
    await engine.stop_session(call_id)
    return {"call_id": call_id, "status": "stopped"}


@router.get("/analysis/{call_id}", response_model=NudgeAnalysis)
async def nudge_analysis(
    call_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Nudge quality analysis for a specific call.
    
    Returns: total/delivered/suppressed counts, suppression breakdown,
    avg confidence, avg/P50/P95 latency, signal type breakdown,
    and false positive estimate.
    """
    engine = NudgeEngine(db)
    analysis = await engine.analyze_call(call_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="No nudges found for call")
    return analysis


@router.get("/latency-report", response_model=LatencyReport)
async def latency_report(
    db: AsyncSession = Depends(get_db),
):
    """
    Aggregate latency report across all calls (Q4 deliverable).
    
    Reports P50/P95 for each pipeline component:
    ASR → signal extraction → LLM nudge generation → delivery
    """
    engine = NudgeEngine(db)
    return await engine.generate_latency_report()
