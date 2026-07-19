"""
Signal Extraction Schemas — Pydantic Models

Shared data contracts for the SignalExtractionService (app/services/signal_extraction_service.py),
consumed by both LangGraph workflows:
- ConversationTracker (Q1): fast, sync intent + entity extraction per turn
- NudgePipeline (Q4): async LLM-based signal detection per transcript buffer

Enums intentionally mirror the string vocabularies already in use elsewhere in the
codebase (nudges.signal_type, nudges.priority, conversation_tracker phase names) so
that .value round-trips cleanly through JSONB columns and existing dict-based
consumers (nudge_engine.py, evaluation.py) without translation.
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class IntentType(str, Enum):
    """Dialogue-act classification for a single utterance (Conversation Tracker fast path)."""
    GREETING = "greeting"
    VERIFY_RESPONSE = "verify_response"
    QUESTION = "question"
    OBJECTION = "objection"
    PAYMENT_OPTIONS_REQUEST = "payment_options_request"
    COMMITMENT = "commitment"
    CALLBACK_REQUEST = "callback_request"
    ESCALATION_REQUEST = "escalation_request"
    UNKNOWN = "unknown"


class EntityType(str, Enum):
    """Entity categories extracted via regex from a raw transcript segment."""
    DATE = "date"
    AMOUNT = "amount"
    LOAN_ID = "loan_id"
    PHONE_NUMBER = "phone_number"
    PAYMENT_METHOD = "payment_method"
    DURATION = "duration"
    NEGATION = "negation"


class SignalType(str, Enum):
    """LLM-detected conversational signal categories (Nudge Pipeline / Q4).

    Values match app.models.nudge.Nudge.signal_type exactly.
    """
    COMPLIANCE_GAP = "compliance_gap"
    SENTIMENT = "sentiment"
    CROSS_SELL = "cross_sell"
    MISSED_OPPORTUNITY = "missed_opportunity"
    PAYMENT_DIFFICULTY = "payment_difficulty"
    RISK = "risk"


class Priority(str, Enum):
    """Nudge/signal priority. Values match app.models.nudge.Nudge.priority exactly."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ExtractedEntity(BaseModel):
    """A single entity detected in a transcript segment via regex extraction."""
    type: EntityType
    value: str = Field(..., description="Raw matched text as it appeared in the transcript")
    normalized_value: str | None = Field(
        None, description="Cleaned/normalized form, e.g. amount digits stripped of currency symbols"
    )
    confidence: float = Field(0.8, ge=0.0, le=1.0)
    span_start: int | None = Field(None, description="Character offset where the match starts")
    span_end: int | None = Field(None, description="Character offset where the match ends")


class IntentResult(BaseModel):
    """Result of fast intent classification on a single utterance."""
    intent: IntentType
    confidence: float = Field(..., ge=0.0, le=1.0)
    matched_phrases: list[str] = Field(
        default_factory=list, description="Phrases that triggered this classification, in match order"
    )


class Signal(BaseModel):
    """A single LLM-detected conversational signal (compliance gap, sentiment shift, etc.)."""
    type: SignalType
    text: str = Field(..., description="What was detected in the conversation")
    confidence: float = Field(..., ge=0.0, le=1.0)
    priority: Priority = Priority.MEDIUM
    key_entity: str = Field("", description="Key entity/concept involved, used for dedup by nudge_engine.py")

    def to_dict(self) -> dict:
        """Serialize to the flat dict shape expected by nudge_engine.py and evaluation.py."""
        return {
            "type": self.type.value,
            "text": self.text,
            "confidence": self.confidence,
            "priority": self.priority.value,
            "key_entity": self.key_entity,
        }


class NudgeText(BaseModel):
    """A generated, agent-facing nudge derived from a Signal."""
    text: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    signal_type: str
    key_entity: str = ""

    def to_dict(self) -> dict:
        """Serialize to the flat dict shape expected by nudge_engine.py."""
        return self.model_dump()


class SignalExtractionResult(BaseModel):
    """Unified output of SignalExtractionService.extract() / extract_fast()."""
    intent: IntentResult
    entities: list[ExtractedEntity] = Field(default_factory=list)
    signals: list[Signal] = Field(default_factory=list)
    extracted_at: datetime = Field(default_factory=datetime.utcnow)

    def get_entity_values(self, entity_type: EntityType) -> list[str]:
        """Convenience accessor: all raw values for a given entity type, in match order."""
        return [e.value for e in self.entities if e.type == entity_type]