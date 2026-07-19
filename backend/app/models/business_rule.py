"""
Business Rule — ORM Model

Declarative business rules for:
- Escalation criteria (when to transfer to human)
- Compliance requirements (disclosures that must be made)
- Qualification logic (eligibility checks)
- Payment rules (grace periods, late fees)

Rules are evaluated by the RuleEngine service against conversation state.
"""

import uuid
from datetime import datetime

from sqlalchemy import String, Text, Boolean, Integer, DateTime, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class BusinessRule(Base):
    __tablename__ = "business_rules"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    rule_id: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True,
        comment="Human-readable ID, e.g., rule_escalation_001"
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True,
        comment="escalation | compliance | qualification | payment"
    )
    rule_type: Mapped[str] = mapped_column(
        String(50), nullable=False,
        comment="threshold | pattern | schedule | checklist"
    )
    condition: Mapped[dict] = mapped_column(
        JSONB, nullable=False,
        comment='Declarative condition, e.g., {"field": "objection_count", "operator": "gte", "value": 3}'
    )
    action: Mapped[dict] = mapped_column(
        JSONB, nullable=False,
        comment='Action to take, e.g., {"type": "escalate", "reason": "Multiple unresolved objections"}'
    )
    priority: Mapped[int] = mapped_column(
        Integer, default=100,
        comment="Higher priority = evaluated first"
    )
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    market: Mapped[str] = mapped_column(
        String(20), default="all",
        comment="all | india | philippines | indonesia"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self):
        return f"<BusinessRule {self.rule_id}: {self.name}>"
