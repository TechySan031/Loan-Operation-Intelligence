"""
Call Schemas — Pydantic Models

Request/response schemas for call management endpoints.
"""

from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, Field


class CallCreate(BaseModel):
    """Schema for creating a new call record."""
    external_call_id: str | None = None
    borrower_name: str | None = None
    loan_id: str | None = None
    loan_type: str | None = None
    language: str = "en"
    payment_due_date: date | None = None
    amount_due: Decimal | None = None
    market: str = "india"


class CallUpdate(BaseModel):
    """Schema for updating a call record."""
    status: str | None = None
    outcome: str | None = None
    commitment_date: date | None = None
    callback_scheduled: datetime | None = None
    transcript: dict | None = None
    summary: str | None = None
    sentiment_score: float | None = None
    metadata: dict | None = None


class CallResponse(BaseModel):
    """Schema for a call response."""
    id: str
    external_call_id: str | None
    borrower_name: str | None
    loan_id: str | None
    loan_type: str | None
    language: str
    status: str
    outcome: str | None
    payment_due_date: date | None
    amount_due: Decimal | None
    commitment_date: date | None
    callback_scheduled: datetime | None
    summary: str | None
    sentiment_score: float | None
    market: str
    created_at: datetime
    updated_at: datetime
    event_count: int | None = None
    nudge_count: int | None = None

    model_config = {"from_attributes": True}


class CallEventResponse(BaseModel):
    """Schema for a call event."""
    id: str
    event_type: str
    from_state: str | None
    to_state: str | None
    payload: dict | None
    created_at: datetime

    model_config = {"from_attributes": True}


class CallListResponse(BaseModel):
    """Schema for paginated call list."""
    calls: list[CallResponse]
    total: int
    page: int
    page_size: int
