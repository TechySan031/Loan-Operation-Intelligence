"""
Voice Agent Routes — Vapi Webhook Handlers (Q1)

Handles all Vapi.ai webhook events:
- POST /webhook — Main webhook endpoint (function-call, status-update, end-of-call-report)
- POST /webhook/assistant-request — Dynamic assistant configuration

Each function-call from Vapi routes to the appropriate service:
- search_knowledge_base → RAG Service
- lookup_borrower → Mock CRM / Call Service
- schedule_callback → Call Service
- record_payment_commitment → Call Service
- escalate_to_human → Call Service
- check_eligibility → Rule Engine
"""

import logging
from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.voice_service import VoiceService
from app.services.rag_service import RAGService
from app.services.rule_engine import RuleEngine
from app.services.call_service import CallService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/webhook")
async def vapi_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Main Vapi webhook endpoint.
    
    Receives all webhook events from Vapi and routes them:
    - function-call → tool execution → return result to Vapi
    - status-update → update call status in DB
    - end-of-call-report → save transcript, generate summary, log to Langfuse
    """
    payload = await request.json()
    message = payload.get("message", payload)
    message_type = message.get("type", "")

    logger.info(f"Vapi webhook received: {message_type}")

    voice_service = VoiceService(db)

    if message_type == "function-call":
        return await voice_service.handle_function_call(message)

    elif message_type == "status-update":
        await voice_service.handle_status_update(message)
        return {"status": "ok"}

    elif message_type == "end-of-call-report":
        await voice_service.handle_end_of_call(message)
        return {"status": "ok"}

    elif message_type == "assistant-request":
        return await voice_service.handle_assistant_request(message)

    elif message_type == "hang":
        # Vapi sends this as a keepalive ping
        return {"status": "ok"}

    else:
        logger.warning(f"Unknown Vapi webhook type: {message_type}")
        return {"status": "ok"}


@router.post("/outbound-call")
async def trigger_outbound_call(
    loan_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Trigger an outbound pre-due reminder call via Vapi.
    
    Looks up borrower by loan_id, creates a call record,
    and initiates the call through Vapi API.
    """
    voice_service = VoiceService(db)
    result = await voice_service.trigger_outbound_call(loan_id)
    return result
