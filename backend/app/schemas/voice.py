"""
Voice / Vapi Schemas — Pydantic Models

Schemas for Vapi.ai webhook payloads:
- function-call: When the LLM calls a tool
- status-update: Call status changes
- end-of-call-report: Post-call analytics
- assistant-request: Dynamic assistant configuration

Reference: https://docs.vapi.ai/server-url
"""

from pydantic import BaseModel, Field


# --- Vapi Webhook Payloads ---
class VapiMessage(BaseModel):
    """Base schema for all Vapi webhook messages."""
    message: dict = Field(..., description="The Vapi webhook payload")


class VapiFunctionCallPayload(BaseModel):
    """Schema for Vapi function-call webhook."""
    type: str = "function-call"
    function_call: dict = Field(
        ..., description='{"name": "search_knowledge_base", "parameters": {"query": "..."}}'
    )
    call: dict = Field(
        default_factory=dict,
        description="Call metadata including call ID"
    )


class VapiStatusUpdate(BaseModel):
    """Schema for Vapi status-update webhook."""
    type: str = "status-update"
    status: str = Field(..., description="in-progress | forwarding | ended")
    call: dict = Field(default_factory=dict)
    messages: list[dict] = Field(default_factory=list)
    ended_reason: str | None = None
    transcript: str | None = None


class VapiEndOfCallReport(BaseModel):
    """Schema for Vapi end-of-call-report webhook."""
    type: str = "end-of-call-report"
    call: dict = Field(default_factory=dict)
    ended_reason: str | None = None
    transcript: str | None = None
    messages: list[dict] = Field(default_factory=list)
    summary: str | None = None
    recording_url: str | None = None
    stereo_recording_url: str | None = None
    duration_seconds: float | None = None
    cost: float | None = None


class VapiAssistantRequest(BaseModel):
    """Schema for Vapi assistant-request webhook (dynamic configuration)."""
    type: str = "assistant-request"
    call: dict = Field(default_factory=dict)
    phone_number: dict | None = None


# --- Tool Response Schemas ---
class ToolCallResult(BaseModel):
    """Schema for a tool call result returned to Vapi."""
    result: str = Field(..., description="The tool call result as a string for the LLM")


class KBSearchToolResult(BaseModel):
    """Schema for knowledge base search tool result."""
    found: bool
    answer: str
    sources: list[dict] = Field(
        default_factory=list,
        description='[{"record_id": "kb_001", "title": "...", "source": "website"}]'
    )
    confidence: float = 0.0


class BorrowerLookupResult(BaseModel):
    """Schema for borrower lookup tool result."""
    found: bool
    borrower_name: str | None = None
    loan_id: str | None = None
    loan_type: str | None = None
    amount_due: float | None = None
    due_date: str | None = None
    days_until_due: int | None = None
    payment_history: str | None = None
    eligible_programs: list[str] = Field(default_factory=list)
