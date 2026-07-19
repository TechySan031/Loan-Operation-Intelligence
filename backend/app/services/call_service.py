"""
Call Service — Call Lifecycle Management

Handles:
- Creating and updating call records
- Logging call events (state transitions, tool calls)
- Retrieving transcripts and event timelines
- Call analytics
"""

import uuid
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update

from app.models.call import Call, CallEvent

logger = logging.getLogger(__name__)


class CallService:
    """
    Call lifecycle management service.
    
    Usage:
        service = CallService(db)
        await service.create_or_update_call(external_call_id="vapi_123", status="active")
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_or_update_call(
        self,
        external_call_id: str,
        status: str | None = None,
        transcript: dict | None = None,
        summary: str | None = None,
        metadata: dict | None = None,
        **kwargs,
    ) -> Call:
        """Create a new call record or update an existing one."""
        result = await self.db.execute(
            select(Call).where(Call.external_call_id == external_call_id)
        )
        call = result.scalar_one_or_none()

        if call is None:
            call = Call(
                id=uuid.uuid4(),
                external_call_id=external_call_id,
                status=status or "active",
                **kwargs,
            )
            self.db.add(call)
        else:
            if status:
                call.status = status
            if transcript:
                call.transcript = transcript
            if summary:
                call.summary = summary
            if metadata:
                existing = call.metadata_ or {}
                existing.update(metadata)
                call.metadata_ = existing

        await self.db.flush()
        return call

    async def log_event(
        self,
        call_id: str,
        event_type: str,
        from_state: str | None = None,
        to_state: str | None = None,
        payload: dict | None = None,
    ):
        """Log a call event for audit trail."""
        # Find call by external_call_id
        result = await self.db.execute(
            select(Call).where(Call.external_call_id == call_id)
        )
        call = result.scalar_one_or_none()

        if call:
            event = CallEvent(
                id=uuid.uuid4(),
                call_id=call.id,
                event_type=event_type,
                from_state=from_state,
                to_state=to_state,
                payload=payload,
            )
            self.db.add(event)
            await self.db.flush()

    async def get_call(self, call_id: str) -> Call | None:
        """Get call by ID or external_call_id."""
        result = await self.db.execute(
            select(Call).where(
                (Call.external_call_id == call_id) | (Call.id == call_id)
            )
        )
        return result.scalar_one_or_none()

    async def get_transcript(self, call_id: str) -> dict | None:
        """Get call transcript."""
        call = await self.get_call(call_id)
        return call.transcript if call else None

    async def get_events(self, call_id: str) -> list[dict]:
        """Get call events timeline."""
        call = await self.get_call(call_id)
        if not call:
            return []

        result = await self.db.execute(
            select(CallEvent)
            .where(CallEvent.call_id == call.id)
            .order_by(CallEvent.created_at.asc())
        )
        events = result.scalars().all()
        return [
            {
                "id": str(e.id),
                "event_type": e.event_type,
                "from_state": e.from_state,
                "to_state": e.to_state,
                "payload": e.payload,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in events
        ]

    async def list_calls(
        self,
        status: str | None = None,
        outcome: str | None = None,
        market: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        """List calls with optional filtering and pagination."""
        query = select(Call)
        count_query = select(func.count(Call.id))

        if status:
            query = query.where(Call.status == status)
            count_query = count_query.where(Call.status == status)
        if outcome:
            query = query.where(Call.outcome == outcome)
            count_query = count_query.where(Call.outcome == outcome)
        if market:
            query = query.where(Call.market == market)
            count_query = count_query.where(Call.market == market)

        total = (await self.db.execute(count_query)).scalar()
        query = query.order_by(Call.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        calls = result.scalars().all()

        return {
            "calls": calls,
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    async def get_analytics(self, market: str | None = None) -> dict:
        """Call analytics summary."""
        base_query = select(Call)
        if market:
            base_query = base_query.where(Call.market == market)

        # Total calls
        total = (await self.db.execute(
            select(func.count(Call.id)).select_from(Call)
        )).scalar()

        # Outcome breakdown
        outcome_query = select(Call.outcome, func.count(Call.id)).group_by(Call.outcome)
        outcome_result = await self.db.execute(outcome_query)
        outcomes = {row[0] or "unknown": row[1] for row in outcome_result.all()}

        return {
            "total_calls": total,
            "outcomes": outcomes,
        }
