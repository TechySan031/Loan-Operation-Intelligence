"""
Nudge — ORM Model

Represents a real-time nudge generated during a live call.
Tracks signal detection, nudge text, confidence, latency breakdown,
and suppression status for false-positive analysis.
"""

import uuid
from datetime import datetime

from sqlalchemy import String, Text, Float, Boolean, Integer, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Nudge(Base):
    __tablename__ = "nudges"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    call_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("calls.id"), nullable=False, index=True
    )
    signal_type: Mapped[str] = mapped_column(
        String(50), nullable=False,
        comment="compliance_gap | sentiment | cross_sell | missed_opportunity | payment_difficulty | risk"
    )
    signal_text: Mapped[str] = mapped_column(
        Text, nullable=False,
        comment="What was detected in the conversation"
    )
    nudge_text: Mapped[str] = mapped_column(
        Text, nullable=False,
        comment="Actionable recommendation for the agent"
    )
    confidence: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0,
        comment="Confidence score 0.0 - 1.0"
    )
    priority: Mapped[str] = mapped_column(
        String(20), default="medium",
        comment="critical | high | medium | low"
    )
    displayed: Mapped[bool] = mapped_column(
        Boolean, default=False,
        comment="Was this nudge shown to the agent"
    )
    suppressed: Mapped[bool] = mapped_column(
        Boolean, default=False,
        comment="Was this nudge filtered out by controls"
    )
    suppression_reason: Mapped[str | None] = mapped_column(
        String(100), nullable=True,
        comment="duplicate | cooldown | low_confidence | max_per_call | expired"
    )
    latency_ms: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True,
        comment='{"asr": 180, "signal": 95, "llm": 320, "delivery": 15, "total": 610}'
    )
    transcript_position: Mapped[int | None] = mapped_column(
        Integer, nullable=True,
        comment="Word offset in transcript when signal was detected"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    call: Mapped["Call"] = relationship(back_populates="nudges")

    def __repr__(self):
        return f"<Nudge {self.signal_type} conf={self.confidence:.2f} {'[SUPPRESSED]' if self.suppressed else ''}>"
