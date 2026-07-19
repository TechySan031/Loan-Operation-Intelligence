"""
Voice Service — Vapi Tool Call Handler (Q1)

Routes Vapi function-call webhooks to the appropriate backend service:
- search_knowledge_base → RAG Service (grounded answers with citations)
- lookup_borrower → Mock CRM (borrower verification)
- schedule_callback → Call Service (callback scheduling)
- record_payment_commitment → Call Service (payment commitment)
- escalate_to_human → Call Service (human escalation)
- check_eligibility → Rule Engine (hardship/restructuring eligibility)

Also handles:
- status-update → Update call status, log state transitions
- end-of-call-report → Save transcript, generate summary, log to Langfuse
- assistant-request → Dynamic assistant configuration based on loan type/market
"""

import logging
import json
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.rag_service import RAGService
from app.services.call_service import CallService
from app.services.rule_engine import RuleEngine
from app.core.langfuse_client import create_trace

logger = logging.getLogger(__name__)

# --- Mock CRM Data (replace with real CRM integration in production) ---
MOCK_BORROWERS = {
    "LN001": {
        "borrower_name": "Rajesh Kumar",
        "loan_id": "LN001",
        "loan_type": "personal",
        "amount_due": 15000.00,
        "due_date": "2025-02-15",
        "days_until_due": 5,
        "payment_history": "Regular payments for 18 months, one late payment in month 6",
        "eligible_programs": ["emi_holiday", "extension"],
        "market": "india",
        "language": "en",
    },
    "LN002": {
        "borrower_name": "Priya Sharma",
        "loan_id": "LN002",
        "loan_type": "home",
        "amount_due": 45000.00,
        "due_date": "2025-02-20",
        "days_until_due": 10,
        "payment_history": "Perfect payment record for 36 months",
        "eligible_programs": ["restructuring", "emi_holiday"],
        "market": "india",
        "language": "en",
    },
    "LN003": {
        "borrower_name": "Amit Patel",
        "loan_id": "LN003",
        "loan_type": "auto",
        "amount_due": 22000.00,
        "due_date": "2025-02-12",
        "days_until_due": 2,
        "payment_history": "3 late payments in last 12 months",
        "eligible_programs": ["extension"],
        "market": "india",
        "language": "en",
    },
    "LN004": {
        "borrower_name": "Maria Santos",
        "loan_id": "LN004",
        "loan_type": "life_insurance",
        "amount_due": 5000.00,
        "due_date": "2025-02-18",
        "days_until_due": 8,
        "payment_history": "Taglish client with regular bancassurance renewals",
        "eligible_programs": ["grace_period"],
        "market": "philippines",
        "language": "fil",
    },
    "LN005": {
        "borrower_name": "Budi Santoso",
        "loan_id": "LN005",
        "loan_type": "consumer_finance",
        "amount_due": 1500000.00,
        "due_date": "2025-02-14",
        "days_until_due": 4,
        "payment_history": "Indonesian client, installment reminder",
        "eligible_programs": ["restructuring"],
        "market": "indonesia",
        "language": "id",
    },
}


class VoiceService:
    """
    Voice service that handles all Vapi webhook events.
    
    Usage:
        service = VoiceService(db)
        result = await service.handle_function_call(message)
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.rag = RAGService(db)
        self.call_service = CallService(db)
        self.rule_engine = RuleEngine(db)

    async def handle_function_call(self, message: dict) -> dict:
        """
        Route a Vapi function-call to the appropriate handler.
        
        Returns the result dict that Vapi will pass back to the LLM.
        """
        func_call = message.get("functionCall", message.get("function_call", {}))
        func_name = func_call.get("name", "")
        params = func_call.get("parameters", {})
        call_info = message.get("call", {})
        call_id = call_info.get("id", "unknown")

        logger.info(f"Function call: {func_name} for call {call_id}")

        trace = create_trace(
            name=f"tool_call_{func_name}",
            metadata={"call_id": call_id, "params": params},
        )

        # Route to handler
        handlers = {
            "search_knowledge_base": self._handle_kb_search,
            "lookup_borrower": self._handle_borrower_lookup,
            "schedule_callback": self._handle_schedule_callback,
            "record_payment_commitment": self._handle_payment_commitment,
            "escalate_to_human": self._handle_escalation,
            "check_eligibility": self._handle_eligibility_check,
        }

        handler = handlers.get(func_name)
        if not handler:
            logger.warning(f"Unknown function: {func_name}")
            return {"result": f"Unknown function: {func_name}"}

        result = await handler(params, call_id)

        # Log event
        await self.call_service.log_event(
            call_id=call_id,
            event_type="tool_call",
            payload={"function": func_name, "params": params, "result": result},
        )

        return {"result": json.dumps(result) if isinstance(result, dict) else str(result)}

    async def _handle_kb_search(self, params: dict, call_id: str) -> dict:
        """Search knowledge base for grounded answers."""
        query = params.get("query", "")
        category = params.get("category")
        return await self.rag.search_for_voice(query=query, category=category)

    async def _handle_borrower_lookup(self, params: dict, call_id: str) -> dict:
        """Look up borrower in mock CRM."""
        name = (params.get("borrower_name") or "").lower()
        loan_id = (
            (params.get("loan_id") or "")
            .upper()
            .replace("-", "")
            .replace(".", "")
            .replace(" ", "")
        )

        # Search by loan_id first, then by name
        if loan_id and loan_id in MOCK_BORROWERS:
           borrower = MOCK_BORROWERS[loan_id]

           return {
               "found": True,
               **borrower,
                "message": (
                    f"Welcome back, {borrower['borrower_name']}. "
                    f"Your next EMI of ₹{borrower['amount_due']:,.2f} "
                    f"is due on {borrower['due_date']}, "
                    f"which is in {borrower['days_until_due']} days."
                ),
            }

        for lid, data in MOCK_BORROWERS.items():
            if name and name in data["borrower_name"].lower():
                return {
                  "found": True,
                  **data,
                  "message": (
                      f"Welcome back, {data['borrower_name']}. "
                      f"Your next EMI of ₹{data['amount_due']:,.2f} "
                      f"is due on {data['due_date']}, "
                      f"which is in {data['days_until_due']} days."
                    ),
                } 

        return {
            "found": False,
            "message": "Borrower not found. Please verify the name or loan ID.",
        }

    async def _handle_schedule_callback(self, params: dict, call_id: str) -> dict:
        """Schedule a callback for the borrower."""
        date = params.get("date", "")
        time = params.get("time", "")
        reason = params.get("reason", "Follow-up on payment")

        # TODO: Save to database
        return {
            "scheduled": True,
            "callback_date": date,
            "callback_time": time,
            "reason": reason,
            "message": (
                f"I've successfully scheduled your callback for {date} at {time}. "
                "One of our loan specialists will contact you then."
            ),
        }

    async def _handle_payment_commitment(self, params: dict, call_id: str) -> dict:
        """Record a payment commitment from the borrower."""
        commitment_date = params.get("commitment_date", "")
        amount = params.get("amount")
        method = params.get("payment_method", "")

        # TODO: Save to database
        return {
            "recorded": True,
            "commitment_date": commitment_date,
            "amount": amount,
            "payment_method": method,
            "message": (
                f"Thank you. I've recorded your commitment to pay ₹{amount:,.2f} "
                f"on {commitment_date} via {method}."
            ),
        }

    async def _handle_escalation(self, params: dict, call_id: str) -> dict:
        """Escalate call to a human agent."""
        reason = params.get("reason", "Customer request")
        priority = params.get("priority", "normal")

        # TODO: Trigger actual escalation (webhook, queue, etc.)
        return {
            "escalated": True,
            "reason": reason,
            "priority": priority,
            "message": (
                "Certainly. I'm connecting you with a human loan specialist now. "
                "Please stay on the line."
            ),
        }

    async def _handle_eligibility_check(self, params: dict, call_id: str) -> dict:
        """Check borrower eligibility for hardship programs."""
        loan_id = (
            (params.get("loan_id") or "")
            .upper()
            .replace("-", "")
            .replace(".", "")
            .replace(" ", "")
        )
        program_type = params.get("program_type", "")

        borrower = MOCK_BORROWERS.get(loan_id)
        if not borrower:
            return {"eligible": False, "reason": "Loan not found"}

        eligible = program_type in borrower.get("eligible_programs", [])

        if eligible:
            message = (
                f"Good news! Based on your loan details, "
                f"you are eligible for the {program_type} program."
            )
        else:
            message = (
                f"Based on the available records, "
                f"you are currently not eligible for the {program_type} program."
            )

        return {
            "eligible": eligible,
            "program_type": program_type,
            "message": message,
        }

    async def handle_status_update(self, message: dict):
        """Handle Vapi status-update webhook."""
        status = message.get("status", "")
        call_info = message.get("call", {})
        call_id = call_info.get("id", "unknown")

        logger.info(f"Call {call_id} status: {status}")

        if status == "in-progress":
            await self.call_service.create_or_update_call(
                external_call_id=call_id,
                status="active",
            )
        elif status == "ended":
            ended_reason = message.get("endedReason", "unknown")
            await self.call_service.create_or_update_call(
                external_call_id=call_id,
                status="completed",
                metadata={"ended_reason": ended_reason},
            )

    async def handle_end_of_call(self, message: dict):
        """Handle Vapi end-of-call-report webhook. Save transcript and summary."""
        call_info = message.get("call", {})
        call_id = call_info.get("id", "unknown")

        transcript = message.get("transcript", "")
        messages = message.get("messages", [])
        summary = message.get("summary", "")
        recording_url = message.get("recordingUrl", "")
        duration = message.get("durationSeconds", 0)

        await self.call_service.create_or_update_call(
            external_call_id=call_id,
            status="completed",
            transcript={"raw": transcript, "messages": messages},
            summary=summary,
            metadata={
                "recording_url": recording_url,
                "duration_seconds": duration,
            },
        )

        logger.info(f"Call {call_id} completed. Duration: {duration}s")

    async def handle_assistant_request(self, message: dict) -> dict:
        """
        Handle Vapi assistant-request webhook.
        
        Dynamically configure the assistant based on the incoming call context
        (e.g., different prompts for different loan types or markets).
        """
        # TODO: Return dynamic assistant configuration
        # For now, return None to use the default assistant
        return {}

    async def trigger_outbound_call(self, loan_id: str) -> dict:
        """Trigger an outbound call via Vapi API."""
        # TODO: Implement Vapi outbound call API
        # POST https://api.vapi.ai/call/phone
        return {"status": "not_implemented", "loan_id": loan_id}
