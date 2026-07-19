"""
REST Tool Endpoints for Vapi API Request Tools.

These endpoints expose the existing VoiceService handlers through
simple REST APIs that Vapi can call.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.voice_service import VoiceService

router = APIRouter()


# ==========================
# Request Models
# ==========================

class SearchRequest(BaseModel):
    query: str
    category: str | None = None


class BorrowerLookupRequest(BaseModel):
    borrower_name: str | None = None
    loan_id: str | None = None


class EligibilityRequest(BaseModel):
    loan_id: str
    program_type: str


class CallbackRequest(BaseModel):
    date: str
    time: str
    reason: str = "Follow-up"


class PaymentCommitmentRequest(BaseModel):
    commitment_date: str
    amount: float
    payment_method: str


class EscalationRequest(BaseModel):
    reason: str
    priority: str = "normal"


# ==========================
# Search Knowledge Base
# ==========================

@router.post("/search")
async def search_kb(
    request: SearchRequest,
    db: AsyncSession = Depends(get_db)
):
    service = VoiceService(db)

    return await service._handle_kb_search(
        {
            "query": request.query,
            "category": request.category,
        },
        "api-request"
    )


# ==========================
# Borrower Lookup
# ==========================

@router.post("/lookup-borrower")
async def lookup_borrower(
    request: BorrowerLookupRequest,
    db: AsyncSession = Depends(get_db)
):
    service = VoiceService(db)

    return await service._handle_borrower_lookup(
        {
            "borrower_name": request.borrower_name,
            "loan_id": request.loan_id,
        },
        "api-request"
    )


# ==========================
# Eligibility
# ==========================

@router.post("/check-eligibility")
async def check_eligibility(
    request: EligibilityRequest,
    db: AsyncSession = Depends(get_db)
):
    service = VoiceService(db)

    return await service._handle_eligibility_check(
        {
            "loan_id": request.loan_id,
            "program_type": request.program_type,
        },
        "api-request"
    )


# ==========================
# Callback
# ==========================

@router.post("/schedule-callback")
async def schedule_callback(
    request: CallbackRequest,
    db: AsyncSession = Depends(get_db)
):
    service = VoiceService(db)

    return await service._handle_schedule_callback(
        {
            "date": request.date,
            "time": request.time,
            "reason": request.reason,
        },
        "api-request"
    )


# ==========================
# Payment Commitment
# ==========================

@router.post("/payment-commitment")
async def payment_commitment(
    request: PaymentCommitmentRequest,
    db: AsyncSession = Depends(get_db)
):
    service = VoiceService(db)

    return await service._handle_payment_commitment(
        {
            "commitment_date": request.commitment_date,
            "amount": request.amount,
            "payment_method": request.payment_method,
        },
        "api-request"
    )


# ==========================
# Escalation
# ==========================

@router.post("/escalate")
async def escalate(
    request: EscalationRequest,
    db: AsyncSession = Depends(get_db)
):
    service = VoiceService(db)

    return await service._handle_escalation(
        {
            "reason": request.reason,
            "priority": request.priority,
        },
        "api-request"
    )