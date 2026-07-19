"""
Knowledge Base Record — ORM Model

Represents a single knowledge base record (chunk) with:
- Content and PII-safe version
- Category taxonomy (product, policy, faq, objection, compliance, payment, escalation)
- Source tracking for citations
- Versioning for content updates
- Chunk-to-parent linking for document traceability
- Embedding ID for Pinecone vector reference
"""

import uuid
from datetime import datetime

from sqlalchemy import String, Text, Boolean, Integer, DateTime, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class KBRecord(Base):
    __tablename__ = "kb_records"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    record_id: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True,
        comment="Human-readable ID, e.g., kb_loan_policy_001"
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_clean: Mapped[str | None] = mapped_column(
        Text, nullable=True,
        comment="PII-redacted version of content"
    )
    category: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True,
        comment="product | policy | faq | objection | compliance | payment | escalation"
    )
    subcategory: Mapped[str | None] = mapped_column(String(100), nullable=True)
    source: Mapped[str] = mapped_column(
        String(50), nullable=False,
        comment="website | pdf | manual | csv"
    )
    source_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    version: Mapped[str] = mapped_column(String(20), default="1.0")
    contains_pii: Mapped[bool] = mapped_column(Boolean, default=False)
    metadata_: Mapped[dict | None] = mapped_column(
        "metadata", JSONB, nullable=True,
        comment="tags, language, product_type, applicable_market, etc."
    )
    chunk_id: Mapped[str | None] = mapped_column(
        String(100), nullable=True,
        comment="Chunk identifier within parent doc"
    )
    parent_doc_id: Mapped[str | None] = mapped_column(
        String(100), nullable=True, index=True,
        comment="Links chunk to parent document"
    )
    embedding_id: Mapped[str | None] = mapped_column(
        String(200), nullable=True,
        comment="Pinecone vector ID"
    )
    token_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    language: Mapped[str] = mapped_column(String(10), default="en")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self):
        return f"<KBRecord {self.record_id}: {self.title[:50]}>"
