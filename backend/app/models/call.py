"""
Call & CallEvent — ORM Models

Call: Represents a voice call session with borrower details, outcome, and transcript.
CallEvent: Event-sourced log of every state transition during a call (audit trail).
"""

import uuid
from datetime import datetime, date
from decimal import Decimal

from sqlalchemy import String, Text, Boolean, Integer, DateTime, Date, Numeric, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Call(Base):
    __tablename__ = "calls"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    external_call_id: Mapped[str | None] = mapped_column(
        String(200), unique=True, nullable=True, index=True,
        comment="Vapi call ID"
    )
    borrower_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    loan_id: Mapped[str | None] = mapped_column(
        String(100), nullable=True, index=True
    )
    loan_type: Mapped[str | None] = mapped_column(
        String(50), nullable=True,
        comment="personal | home | auto | business"
    )
    language: Mapped[str] = mapped_column(String(10), default="en")
    status: Mapped[str] = mapped_column(
        String(20), default="active",
        comment="active | completed | escalated | failed"
    )
    outcome: Mapped[str | None] = mapped_column(
        String(50), nullable=True,
        comment="commitment | callback | escalation | refused | no_answer"
    )
    payment_due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    amount_due: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2), nullable=True
    )
    commitment_date: Mapped[date | None] = mapped_column(
        Date, nullable=True,
        comment="Date borrower committed to pay"
    )
    callback_scheduled: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    transcript: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True,
        comment="Full conversation transcript as JSON"
    )
    summary: Mapped[str | None] = mapped_column(
        Text, nullable=True,
        comment="LLM-generated call summary"
    )
    sentiment_score: Mapped[float | None] = mapped_column(
        Numeric(3, 2), nullable=True,
        comment="Overall call sentiment (-1.0 to 1.0)"
    )
    metadata_: Mapped[dict | None] = mapped_column(
        "metadata", JSONB, nullable=True,
        comment="duration_seconds, agent_id, recording_url, etc."
    )
    market: Mapped[str] = mapped_column(
        String(20), default="india",
        comment="india | philippines | indonesia"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    events: Mapped[list["CallEvent"]] = relationship(
        back_populates="call", cascade="all, delete-orphan"
    )
    nudges: Mapped[list["Nudge"]] = relationship(
        "Nudge", back_populates="call", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Call {self.external_call_id} status={self.status}>"


class CallEvent(Base):
    """
    Event-sourced log of conversation state transitions.
    Every tool call, state change, escalation, and error is recorded.
    Enables full audit trail and conversation replay.
    """
    __tablename__ = "call_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    call_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("calls.id"), nullable=False, index=True
    )
    event_type: Mapped[str] = mapped_column(
        String(50), nullable=False,
        comment="state_change | tool_call | rag_query | escalation | error | compliance_check"
    )
    from_state: Mapped[str | None] = mapped_column(String(50), nullable=True)
    to_state: Mapped[str | None] = mapped_column(String(50), nullable=True)
    payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    call: Mapped["Call"] = relationship(back_populates="events")

    def __repr__(self):
        return f"<CallEvent {self.event_type}: {self.from_state} → {self.to_state}>"
