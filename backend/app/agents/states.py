"""
LangGraph State Definitions

TypedDict state classes for:
1. ConversationState — Voice agent conversation tracking (Q1)
2. NudgePipelineState — Real-time nudge generation pipeline (Q4)
"""

from typing import TypedDict, Literal


class ConversationState(TypedDict):
    """
    State for the voice agent conversation tracker (Q1).
    
    Tracks conversation phase, borrower details, objections,
    questions, compliance checklist, and outcome.
    """
    # Call identification
    call_id: str
    
    # Borrower info (populated during verification)
    borrower_name: str | None
    loan_id: str | None
    loan_type: str | None
    amount_due: float | None
    due_date: str | None
    
    # Conversation state
    current_phase: str  # greeting | verify | remind | objection | question | options | commit | callback | escalate | wrap_up
    verification_attempts: int
    objections_raised: list[str]
    questions_asked: list[str]

    # Signal Extraction output (Phase 1) — populated by app.agents.conversation_tracker.extract_signals
    # via app.services.signal_extraction_service.SignalExtractionService.apply_to_conversation_state
    detected_intent: dict | None  # IntentResult.model_dump(mode="json")
    extracted_entities: list[dict]  # [ExtractedEntity.model_dump(mode="json"), ...]

    # RAG context tracking (for citations)
    rag_contexts_used: list[dict]
    
    # Outcomes
    commitment: dict | None  # {date, amount, method}
    callback: dict | None    # {date, time, reason}
    escalation_reason: str | None
    
    # Compliance tracking
    compliance_checklist: dict  # {identity_disclosed: bool, purpose_stated: bool, recording_mentioned: bool}
    
    # Analytics
    sentiment_trajectory: list[str]  # per-turn sentiment
    turn_count: int
    
    # Conversation history
    messages: list[dict]


class NudgePipelineState(TypedDict):
    """
    State for the real-time nudge pipeline (Q4).
    
    Tracks audio processing, transcript buffering,
    signal detection, nudge generation, and delivery.
    """
    # Session identification
    call_id: str
    session_id: str
    
    # Audio processing
    audio_buffer: bytes
    chunk_count: int
    
    # Transcript
    transcript_buffer: str
    transcript_segments: list[dict]  # [{text, speaker, start, end, confidence}]
    last_processed_position: int
    
    # Signal detection
    active_signals: list[dict]
    signal_history: list[dict]
    
    # Nudge generation
    generated_nudges: list[dict]
    delivered_nudges: list[dict]
    suppressed_nudges: list[dict]
    
    # Nudge control state
    nudge_hash_history: list[str]  # for dedup
    last_nudge_timestamp: float    # for cooldown
    total_delivered: int           # for max per call
    
    # Latency tracking
    latency_log: list[dict]  # [{component, latency_ms, timestamp}]
    
    # Analytics
    compliance_flags: list[str]
    sentiment_score: float
    turn_count: int