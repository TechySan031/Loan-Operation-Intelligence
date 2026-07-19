"""
Signal Extraction Service — Shared Preprocessing Layer (Q1 + Q4)

A single reusable service that converts raw transcript text into structured
conversational signals for BOTH LangGraph workflows:

1. Conversation Tracker (Q1) — consumes the SYNC, regex/keyword-based path
   (extract_intent, extract_entities, extract_fast). No LLM round-trip: this
   runs once per conversation turn in the live voice call path, where added
   latency is directly felt by the caller. Populates ConversationState fields
   that conversation_tracker.py declares but never writes to today:
   objections_raised, questions_asked, commitment, callback, escalation_reason.
   Also offers a best-effort current_phase hint that update_phase()'s own
   keyword matching may override — additive, never conflicting, with the
   existing tested phase-detection behavior.

2. Nudge Pipeline (Q4) — consumes the ASYNC, LLM-based path (extract_llm_signals,
   generate_nudge). This mirrors the exact prompt-based approach already proven
   in app/services/signal_extractor.py (imported, not duplicated), but returns
   typed Signal/NudgeText objects instead of raw dicts, and adds structured
   error handling for malformed LLM output.

Design rationale for the sync/async split: mixing an LLM call into the
Conversation Tracker's per-turn graph would add ~300-800ms to every single
turn of a live phone call. The Nudge Pipeline already batches ~30 words
before calling out to the LLM (see nudge_pipeline.should_extract), which is
the appropriate place for that cost. Conversation Tracker instead gets a
fast, deterministic, fully testable intent/entity layer.

Both paths are exposed on ONE class so callers (Conversation Tracker nodes,
Nudge Pipeline nodes, NudgeEngine, evaluation harness) share one import and
one set of schemas (app/schemas/signal.py).
"""

import json
import logging
import re

from openai import AsyncOpenAI

from app.config import settings
from app.schemas.signal import (
    EntityType,
    ExtractedEntity,
    IntentResult,
    IntentType,
    NudgeText,
    Priority,
    Signal,
    SignalExtractionResult,
    SignalType,
)
from app.services.signal_extractor import NUDGE_GENERATION_PROMPT, SIGNAL_EXTRACTION_PROMPT

logger = logging.getLogger(__name__)


# --- Entity extraction patterns (fast path, no LLM) ---

_DATE_PATTERNS: tuple[re.Pattern, ...] = (
    re.compile(r"\b(?:next|this|coming)?\s?(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b", re.IGNORECASE),
    re.compile(r"\b(?:today|tomorrow|tonight|day after tomorrow)\b", re.IGNORECASE),
    re.compile(r"\bnext\s+(?:week|month)\b", re.IGNORECASE),
    re.compile(r"\b\d{4}-\d{2}-\d{2}\b"),
    re.compile(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b"),
    re.compile(r"\b(?:on\s+the\s+)?\d{1,2}(?:st|nd|rd|th)\b", re.IGNORECASE),
    re.compile(r"\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{1,2}(?:st|nd|rd|th)?\b", re.IGNORECASE),
)

_AMOUNT_PATTERNS: tuple[re.Pattern, ...] = (
    re.compile(r"₹\s?[\d,]+(?:\.\d+)?"),
    re.compile(r"\brs\.?\s?[\d,]+(?:\.\d+)?\b", re.IGNORECASE),
    re.compile(r"\binr\s?[\d,]+(?:\.\d+)?\b", re.IGNORECASE),
    re.compile(r"\$\s?[\d,]+(?:\.\d+)?"),
    re.compile(r"\b[\d,]+(?:\.\d+)?\s?rupees\b", re.IGNORECASE),
)

_LOAN_ID_PATTERN = re.compile(r"\b[A-Z]{2,5}\d{3,6}\b")
_PHONE_PATTERN = re.compile(r"\b(?:\+?91[-\s]?)?\d{10}\b")
_PAYMENT_METHOD_PATTERN = re.compile(
    r"\b(?:upi|net\s?banking|bank transfer|neft|imps|rtgs|cheque|check|cash|"
    r"debit card|credit card|auto[-\s]?debit|standing instruction)\b",
    re.IGNORECASE,
)
_DURATION_PATTERN = re.compile(r"\bin\s+\d+\s+(?:day|days|week|weeks|month|months)\b", re.IGNORECASE)
_NEGATION_PATTERN = re.compile(r"\b(?:not|cannot|can't|won't|no|never|unable|isn't|don't)\b", re.IGNORECASE)


def _extract_entities(text: str) -> list[ExtractedEntity]:
    """Regex-based entity extraction. Pure function — no LLM, no I/O, fully deterministic."""
    entities: list[ExtractedEntity] = []

    for pattern in _DATE_PATTERNS:
        for match in pattern.finditer(text):
            value = match.group(0).strip()
            if not value:
                continue
            entities.append(ExtractedEntity(
                type=EntityType.DATE, value=value, normalized_value=value.lower(),
                confidence=0.85, span_start=match.start(), span_end=match.end(),
            ))

    for pattern in _AMOUNT_PATTERNS:
        for match in pattern.finditer(text):
            value = match.group(0).strip()
            entities.append(ExtractedEntity(
                type=EntityType.AMOUNT, value=value,
                normalized_value=re.sub(r"[^\d.]", "", value) or None,
                confidence=0.9, span_start=match.start(), span_end=match.end(),
            ))

    for match in _LOAN_ID_PATTERN.finditer(text):
        entities.append(ExtractedEntity(
            type=EntityType.LOAN_ID, value=match.group(0), normalized_value=match.group(0).upper(),
            confidence=0.8, span_start=match.start(), span_end=match.end(),
        ))

    for match in _PHONE_PATTERN.finditer(text):
        entities.append(ExtractedEntity(
            type=EntityType.PHONE_NUMBER, value=match.group(0),
            normalized_value=re.sub(r"[^\d]", "", match.group(0)),
            confidence=0.85, span_start=match.start(), span_end=match.end(),
        ))

    for match in _PAYMENT_METHOD_PATTERN.finditer(text):
        entities.append(ExtractedEntity(
            type=EntityType.PAYMENT_METHOD, value=match.group(0), normalized_value=match.group(0).lower(),
            confidence=0.85, span_start=match.start(), span_end=match.end(),
        ))

    for match in _DURATION_PATTERN.finditer(text):
        entities.append(ExtractedEntity(
            type=EntityType.DURATION, value=match.group(0), normalized_value=match.group(0).lower(),
            confidence=0.8, span_start=match.start(), span_end=match.end(),
        ))

    for match in _NEGATION_PATTERN.finditer(text):
        entities.append(ExtractedEntity(
            type=EntityType.NEGATION, value=match.group(0), normalized_value=match.group(0).lower(),
            confidence=0.7, span_start=match.start(), span_end=match.end(),
        ))

    return entities


# --- Intent classification (fast path, no LLM) ---

# Priority order matters: when an utterance matches multiple intent phrase sets
# (e.g. "I can't pay, get me a supervisor" matches both OBJECTION and
# ESCALATION_REQUEST), the FIRST matching intent in this tuple wins. This
# mirrors the priority ordering already established in
# conversation_tracker._PHASES (escalate > callback > commit > objection > ...).
_INTENT_PRIORITY: tuple[IntentType, ...] = (
    IntentType.ESCALATION_REQUEST,
    IntentType.CALLBACK_REQUEST,
    IntentType.COMMITMENT,
    IntentType.OBJECTION,
    IntentType.PAYMENT_OPTIONS_REQUEST,
    IntentType.QUESTION,
    IntentType.VERIFY_RESPONSE,
    IntentType.GREETING,
)

_INTENT_PATTERNS: dict[IntentType, tuple[str, ...]] = {
    IntentType.ESCALATION_REQUEST: (
        "supervisor", "human agent", "real person", "speak to someone", "complaint", "manager",
    ),
    IntentType.CALLBACK_REQUEST: (
        "call me back", "call back", "callback", "later today", "call me later", "try again later",
    ),
    IntentType.COMMITMENT: (
        "i will pay", "i'll pay", "will make payment", "pay on", "payment by",
        "i can pay on", "i'll make the payment",
    ),
    IntentType.OBJECTION: (
        "can't pay", "cannot pay", "unable to pay", "too much", "not able to",
        "financial difficulty", "lost my job", "don't have money", "no money", "can't afford",
    ),
    IntentType.PAYMENT_OPTIONS_REQUEST: (
        "payment option", "installment", "payment plan", "can pay via", "how can i pay", "ways to pay",
    ),
    IntentType.QUESTION: (
        "?", "what is", "why is", "how do", "when is", "how much", "what happens if",
    ),
    IntentType.VERIFY_RESPONSE: (
        "date of birth", "my dob", "last four", "yes that's correct", "that's right", "confirmed",
    ),
    IntentType.GREETING: (
        "hello", "hi there", "good morning", "good afternoon", "good evening",
    ),
}

_INTENT_BASE_CONFIDENCE: dict[IntentType, float] = {
    IntentType.ESCALATION_REQUEST: 0.80,
    IntentType.CALLBACK_REQUEST: 0.75,
    IntentType.COMMITMENT: 0.72,
    IntentType.OBJECTION: 0.70,
    IntentType.PAYMENT_OPTIONS_REQUEST: 0.65,
    IntentType.QUESTION: 0.60,
    IntentType.VERIFY_RESPONSE: 0.58,
    IntentType.GREETING: 0.55,
}

# Maps a fast-path intent to a conversation_tracker phase name. Used only as a
# fallback hint in apply_to_conversation_state — update_phase's own _PHASES
# matching always takes precedence when it finds a match.
_INTENT_TO_PHASE: dict[IntentType, str] = {
    IntentType.ESCALATION_REQUEST: "escalate",
    IntentType.CALLBACK_REQUEST: "callback",
    IntentType.COMMITMENT: "commit",
    IntentType.OBJECTION: "objection",
    IntentType.PAYMENT_OPTIONS_REQUEST: "options",
    IntentType.QUESTION: "question",
    IntentType.VERIFY_RESPONSE: "verify",
    IntentType.GREETING: "greeting",
}


def _score_intent(text: str) -> IntentResult:
    """Deterministic, explainable intent classification with confidence scoring.

    Confidence = per-intent base score + a small bonus per additional matched
    phrase (capped at 0.97). Base scores encode priority: higher-priority
    intents (escalation, callback) have higher base confidence than lower
    priority ones (greeting), consistent with _INTENT_PRIORITY ordering.
    """
    text_lower = text.lower()
    for intent in _INTENT_PRIORITY:
        phrases = _INTENT_PATTERNS[intent]
        matches = [p for p in phrases if p in text_lower]
        if not matches:
            continue
        base = _INTENT_BASE_CONFIDENCE[intent]
        confidence = min(base + 0.04 * (len(matches) - 1), 0.97)
        return IntentResult(intent=intent, confidence=round(confidence, 2), matched_phrases=matches)
    return IntentResult(intent=IntentType.UNKNOWN, confidence=0.30, matched_phrases=[])


class SignalExtractionService:
    """
    Shared preprocessing layer between transcript ingestion and downstream graph logic.

    Usage (Conversation Tracker — sync, fast path):
        service = get_signal_extraction_service()
        result = service.extract_fast("I can't pay, too much this month")
        state = service.apply_to_conversation_state(result, state)

    Usage (Nudge Pipeline — async, LLM path):
        service = get_signal_extraction_service()
        result = await service.extract(transcript=full_transcript, new_segment=new_text)
        nudge_dicts = service.to_nudge_pipeline_signals(result.signals)
    """

    def __init__(self, llm_model: str | None = None, mini_model: str | None = None):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.llm_model = llm_model or settings.OPENAI_LLM_MODEL
        self.mini_model = mini_model or settings.OPENAI_LLM_MODEL_MINI

    # --- Sync, fast path (Conversation Tracker / Q1) ---

    def extract_intent(self, text: str) -> IntentResult:
        """Classify the dialogue act of a single utterance. No I/O, no LLM."""
        return _score_intent(text)

    def extract_entities(self, text: str) -> list[ExtractedEntity]:
        """Extract dates, amounts, loan IDs, phone numbers, payment methods, etc. No I/O, no LLM."""
        return _extract_entities(text)

    def extract_fast(self, text: str) -> SignalExtractionResult:
        """Combined intent + entity extraction with an empty signals list (no LLM call)."""
        return SignalExtractionResult(intent=_score_intent(text), entities=_extract_entities(text), signals=[])

    def apply_to_conversation_state(self, result: SignalExtractionResult, state: dict) -> dict:
        """Merge fast-path extraction results into a ConversationState dict.

        Populates fields conversation_tracker.py declares but never writes to:
        objections_raised, questions_asked, commitment, callback, escalation_reason.
        Also sets a current_phase fallback hint — only takes effect when the
        state isn't already in a terminal phase; update_phase's own keyword
        matching still has final say whenever it finds a match.
        """
        updates: dict = {}
        intent_result = result.intent
        intent = intent_result.intent

        updates["detected_intent"] = intent_result.model_dump(mode="json")
        updates["extracted_entities"] = [e.model_dump(mode="json") for e in result.entities]

        if intent == IntentType.OBJECTION:
            objections = list(state.get("objections_raised", []))
            label = intent_result.matched_phrases[0] if intent_result.matched_phrases else "objection_raised"
            if label not in objections:
                objections.append(label)
            updates["objections_raised"] = objections

        elif intent == IntentType.QUESTION:
            questions = list(state.get("questions_asked", []))
            label = intent_result.matched_phrases[0] if intent_result.matched_phrases else "question_asked"
            questions.append(label)
            updates["questions_asked"] = questions

        elif intent == IntentType.COMMITMENT:
            dates = result.get_entity_values(EntityType.DATE)
            amounts = result.get_entity_values(EntityType.AMOUNT)
            methods = result.get_entity_values(EntityType.PAYMENT_METHOD)
            updates["commitment"] = {
                "date": dates[0] if dates else None,
                "amount": amounts[0] if amounts else None,
                "method": methods[0] if methods else None,
                "confidence": intent_result.confidence,
            }

        elif intent == IntentType.CALLBACK_REQUEST:
            dates = result.get_entity_values(EntityType.DATE)
            updates["callback"] = {
                "date": dates[0] if dates else None,
                "time": None,
                "reason": "Borrower requested a callback",
            }

        elif intent == IntentType.ESCALATION_REQUEST:
            if not state.get("escalation_reason"):
                updates["escalation_reason"] = "Borrower explicitly requested a human agent"

        mapped_phase = _INTENT_TO_PHASE.get(intent)
        if (
            mapped_phase
            and intent_result.confidence >= 0.6
            and state.get("current_phase") not in {"wrap_up", "escalate"}
        ):
            updates["current_phase"] = mapped_phase

        return {**state, **updates}

    # --- Async, LLM path (Nudge Pipeline / Q4) ---

    async def extract_llm_signals(self, transcript: str, new_segment: str) -> list[Signal]:
        """LLM-based signal detection, reusing the proven prompt from signal_extractor.py.

        Returns typed Signal objects. Malformed entries from the LLM response are
        logged and skipped individually rather than discarding the whole batch.
        """
        try:
            response = await self.client.chat.completions.create(
                model=self.llm_model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a precise real-time call analysis system. "
                            "Only detect genuine, actionable signals. Minimize false positives."
                        ),
                    },
                    {
                        "role": "user",
                        "content": SIGNAL_EXTRACTION_PROMPT.format(
                            transcript=transcript[-2000:],
                            new_segment=new_segment,
                        ),
                    },
                ],
                temperature=0.1,
                max_tokens=500,
            )
            content = response.choices[0].message.content.strip()
            raw_signals = json.loads(content)
            if not isinstance(raw_signals, list):
                return []

            signals: list[Signal] = []
            for raw in raw_signals:
                try:
                    signals.append(Signal(
                        type=SignalType(raw.get("type")),
                        text=raw.get("text", ""),
                        confidence=float(raw.get("confidence", 0.5)),
                        priority=Priority(raw.get("priority", "medium")),
                        key_entity=raw.get("key_entity", ""),
                    ))
                except (ValueError, KeyError, TypeError) as exc:
                    logger.warning("Skipping malformed signal from LLM response: %s (%s)", raw, exc)
            return signals

        except json.JSONDecodeError:
            logger.warning("Failed to parse LLM signal extraction response as JSON")
            return []
        except Exception as exc:
            logger.error("LLM signal extraction failed: %s", exc)
            return []

    async def generate_nudge(self, signal: Signal | dict) -> NudgeText:
        """Generate an actionable nudge from a detected signal. Accepts either a
        typed Signal or a raw dict (for compatibility with LLM-derived signals
        that haven't been coerced to Signal yet)."""
        if isinstance(signal, Signal):
            signal_type, signal_text = signal.type.value, signal.text
            confidence, key_entity = signal.confidence, signal.key_entity
        else:
            signal_type = signal.get("type", "")
            signal_text = signal.get("text", "")
            confidence = float(signal.get("confidence", 0.5))
            key_entity = signal.get("key_entity", "")

        try:
            response = await self.client.chat.completions.create(
                model=self.mini_model,
                messages=[{
                    "role": "user",
                    "content": NUDGE_GENERATION_PROMPT.format(signal_type=signal_type, signal_text=signal_text),
                }],
                temperature=0.3,
                max_tokens=100,
            )
            nudge_text = response.choices[0].message.content.strip()
        except Exception as exc:
            logger.error("Nudge generation failed: %s", exc)
            nudge_text = f"Check: {signal_text or 'Signal detected'}"

        return NudgeText(text=nudge_text, confidence=confidence, signal_type=signal_type, key_entity=key_entity)

    async def extract(
        self,
        transcript: str,
        new_segment: str,
        include_llm_signals: bool = True,
    ) -> SignalExtractionResult:
        """Unified extraction: fast intent/entities on new_segment, plus optional
        LLM-based signal detection across the fuller transcript window."""
        intent = _score_intent(new_segment)
        entities = _extract_entities(new_segment)
        signals: list[Signal] = []
        if include_llm_signals and new_segment.strip():
            signals = await self.extract_llm_signals(transcript=transcript, new_segment=new_segment)
        return SignalExtractionResult(intent=intent, entities=entities, signals=signals)

    # --- Adapters ---

    def to_nudge_pipeline_signals(self, signals: list[Signal]) -> list[dict]:
        """Adapter: typed Signals -> flat dicts matching NudgePipelineState.active_signals
        and the shape nudge_engine.py already expects from SignalExtractor.extract()."""
        return [s.to_dict() for s in signals]


# --- Module-level singleton, matching the get_redis()/get_pinecone_index() DI pattern ---

_service_singleton: SignalExtractionService | None = None


def get_signal_extraction_service() -> SignalExtractionService:
    """Dependency accessor for the shared SignalExtractionService instance."""
    global _service_singleton
    if _service_singleton is None:
        _service_singleton = SignalExtractionService()
    return _service_singleton
