"""Unit tests for SignalExtractionService (Phase 1).

No database dependency — SignalExtractionService is stateless w.r.t. Postgres,
so these tests don't use the db_session/client fixtures from conftest.py.
LLM calls are mocked; nothing here hits the real OpenAI API.
"""

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.schemas.signal import EntityType, IntentType, Priority, Signal, SignalType
from app.services.signal_extraction_service import SignalExtractionService


def _make_response(content: str):
    """Build a minimal object mimicking openai's ChatCompletion response shape."""
    message = SimpleNamespace(content=content)
    choice = SimpleNamespace(message=message)
    return SimpleNamespace(choices=[choice])


@pytest.fixture
def service() -> SignalExtractionService:
    return SignalExtractionService()


def _base_state(**overrides) -> dict:
    base = {
        "call_id": "call-1",
        "messages": [],
        "current_phase": "remind",
        "verification_attempts": 0,
        "objections_raised": [],
        "questions_asked": [],
        "compliance_checklist": {},
        "turn_count": 0,
        "commitment": None,
        "callback": None,
        "escalation_reason": None,
    }
    return {**base, **overrides}


# --- Intent detection ---

class TestIntentDetection:
    def test_detects_objection_intent(self, service):
        result = service.extract_intent("I can't pay this amount, I lost my job last month")
        assert result.intent == IntentType.OBJECTION
        assert result.confidence >= 0.7

    def test_detects_commitment_intent(self, service):
        result = service.extract_intent("Okay, I will pay on Friday")
        assert result.intent == IntentType.COMMITMENT

    def test_detects_callback_intent(self, service):
        result = service.extract_intent("Can you call me back later today?")
        assert result.intent == IntentType.CALLBACK_REQUEST

    def test_detects_escalation_intent_over_objection(self, service):
        """Escalation must win when an utterance matches both patterns — higher priority."""
        result = service.extract_intent("I can't pay, get me a supervisor")
        assert result.intent == IntentType.ESCALATION_REQUEST

    def test_detects_question_intent(self, service):
        result = service.extract_intent("What is the late payment penalty?")
        assert result.intent == IntentType.QUESTION

    def test_detects_payment_options_intent(self, service):
        result = service.extract_intent("What payment options do I have?")
        assert result.intent == IntentType.PAYMENT_OPTIONS_REQUEST

    def test_detects_greeting_intent(self, service):
        result = service.extract_intent("Good morning")
        assert result.intent == IntentType.GREETING

    def test_unknown_intent_for_unmatched_text(self, service):
        result = service.extract_intent("The weather has been nice lately")
        assert result.intent == IntentType.UNKNOWN
        assert result.confidence < 0.5

    def test_confidence_increases_with_more_matched_phrases(self, service):
        single = service.extract_intent("can't pay right now")
        multiple = service.extract_intent("can't pay, too much, financial difficulty this month")
        assert multiple.confidence >= single.confidence

    def test_confidence_capped_at_reasonable_ceiling(self, service):
        result = service.extract_intent(
            "can't pay, cannot pay, unable to pay, too much, not able to, "
            "financial difficulty, lost my job, don't have money, no money, can't afford"
        )
        assert result.confidence <= 0.97


# --- Entity extraction ---

class TestEntityExtraction:
    def test_extracts_date_entity_weekday(self, service):
        entities = service.extract_entities("I will pay on Friday")
        dates = [e for e in entities if e.type == EntityType.DATE]
        assert dates
        assert "friday" in dates[0].value.lower()

    def test_extracts_date_entity_relative(self, service):
        entities = service.extract_entities("I can pay tomorrow")
        dates = [e for e in entities if e.type == EntityType.DATE]
        assert any("tomorrow" in d.value.lower() for d in dates)

    def test_extracts_amount_entity_rs_prefix(self, service):
        entities = service.extract_entities("The amount due is Rs 15000")
        amounts = [e for e in entities if e.type == EntityType.AMOUNT]
        assert amounts
        assert amounts[0].normalized_value == "15000"

    def test_extracts_amount_entity_rupee_symbol(self, service):
        entities = service.extract_entities("You owe ₹22,000 on this loan")
        amounts = [e for e in entities if e.type == EntityType.AMOUNT]
        assert amounts

    def test_extracts_loan_id_entity(self, service):
        entities = service.extract_entities("My loan ID is LN001")
        loan_ids = [e for e in entities if e.type == EntityType.LOAN_ID]
        assert loan_ids
        assert loan_ids[0].value == "LN001"

    def test_extracts_payment_method_entity(self, service):
        entities = service.extract_entities("I'll pay via UPI")
        methods = [e for e in entities if e.type == EntityType.PAYMENT_METHOD]
        assert methods

    def test_extracts_phone_number_entity(self, service):
        entities = service.extract_entities("You can reach me at 9876543210")
        phones = [e for e in entities if e.type == EntityType.PHONE_NUMBER]
        assert phones

    def test_extracts_negation_entity(self, service):
        entities = service.extract_entities("I cannot pay right now")
        negations = [e for e in entities if e.type == EntityType.NEGATION]
        assert negations

    def test_no_entities_in_unrelated_text(self, service):
        entities = service.extract_entities("The weather has been nice lately")
        assert entities == []


# --- extract_fast (combined, no LLM) ---

class TestExtractFast:
    def test_extract_fast_returns_no_llm_signals(self, service):
        result = service.extract_fast("I will pay on Friday")
        assert result.signals == []
        assert result.intent.intent == IntentType.COMMITMENT

    def test_extract_fast_combines_intent_and_entities(self, service):
        result = service.extract_fast("I will pay Rs 15000 on Friday via UPI")
        assert result.intent.intent == IntentType.COMMITMENT
        assert result.get_entity_values(EntityType.DATE)
        assert result.get_entity_values(EntityType.AMOUNT)
        assert result.get_entity_values(EntityType.PAYMENT_METHOD)


# --- apply_to_conversation_state ---

class TestApplyToConversationState:
    def test_objection_updates_objections_raised_and_phase(self, service):
        result = service.extract_fast("I can't pay, too much this month")
        state = service.apply_to_conversation_state(result, _base_state())
        assert len(state["objections_raised"]) == 1
        assert state["current_phase"] == "objection"

    def test_objection_does_not_duplicate_same_label(self, service):
        result = service.extract_fast("I can't pay right now")
        state = service.apply_to_conversation_state(result, _base_state())
        state2 = service.apply_to_conversation_state(result, state)
        assert len(state2["objections_raised"]) == 1

    def test_commitment_sets_commitment_dict(self, service):
        result = service.extract_fast("I will pay on Friday via UPI")
        state = service.apply_to_conversation_state(result, _base_state())
        assert state["commitment"] is not None
        assert state["commitment"]["method"] is not None
        assert state["commitment"]["date"] is not None

    def test_callback_request_sets_callback_dict(self, service):
        result = service.extract_fast("Can you call me back tomorrow?")
        state = service.apply_to_conversation_state(result, _base_state())
        assert state["callback"] is not None
        assert state["callback"]["reason"] == "Borrower requested a callback"

    def test_escalation_sets_reason(self, service):
        result = service.extract_fast("Get me a supervisor now")
        state = service.apply_to_conversation_state(result, _base_state())
        assert state["escalation_reason"] == "Borrower explicitly requested a human agent"

    def test_escalation_does_not_overwrite_existing_reason(self, service):
        result = service.extract_fast("Get me a supervisor now")
        state = service.apply_to_conversation_state(
            result, _base_state(escalation_reason="Verification failed 3 times")
        )
        assert state["escalation_reason"] == "Verification failed 3 times"

    def test_does_not_override_terminal_phase(self, service):
        result = service.extract_fast("I will pay tomorrow")
        state = service.apply_to_conversation_state(result, _base_state(current_phase="escalate"))
        assert state["current_phase"] == "escalate"

    def test_question_appends_without_dedup(self, service):
        result = service.extract_fast("What is the late fee?")
        state = service.apply_to_conversation_state(result, _base_state())
        state2 = service.apply_to_conversation_state(result, state)
        assert len(state2["questions_asked"]) == 2

    def test_always_records_detected_intent_and_entities(self, service):
        result = service.extract_fast("Hello there")
        state = service.apply_to_conversation_state(result, _base_state())
        assert state["detected_intent"]["intent"] == "greeting"
        assert isinstance(state["extracted_entities"], list)

    def test_low_confidence_unknown_does_not_set_phase(self, service):
        result = service.extract_fast("The weather has been nice lately")
        state = service.apply_to_conversation_state(result, _base_state(current_phase="remind"))
        assert state["current_phase"] == "remind"


# --- LLM-based signal extraction (mocked, async) ---

class TestLLMSignalExtraction:
    @pytest.mark.asyncio
    async def test_extract_llm_signals_parses_valid_response(self, service):
        payload = json.dumps([{
            "type": "payment_difficulty",
            "text": "Customer mentioned job loss",
            "confidence": 0.82,
            "priority": "high",
            "key_entity": "job_loss",
        }])
        service.client.chat.completions.create = AsyncMock(return_value=_make_response(payload))

        signals = await service.extract_llm_signals(transcript="...", new_segment="I lost my job")

        assert len(signals) == 1
        assert signals[0].type == SignalType.PAYMENT_DIFFICULTY
        assert signals[0].confidence == 0.82

    @pytest.mark.asyncio
    async def test_extract_llm_signals_handles_empty_array(self, service):
        service.client.chat.completions.create = AsyncMock(return_value=_make_response("[]"))
        signals = await service.extract_llm_signals(transcript="...", new_segment="hello")
        assert signals == []

    @pytest.mark.asyncio
    async def test_extract_llm_signals_handles_malformed_json(self, service):
        service.client.chat.completions.create = AsyncMock(return_value=_make_response("not json"))
        signals = await service.extract_llm_signals(transcript="...", new_segment="hello")
        assert signals == []

    @pytest.mark.asyncio
    async def test_extract_llm_signals_skips_malformed_entries_without_failing_batch(self, service):
        payload = json.dumps([
            {"type": "not_a_real_type", "text": "bad", "confidence": 0.9},
            {"type": "risk", "text": "Agent made an unverified promise", "confidence": 0.7,
             "priority": "critical", "key_entity": "promise"},
        ])
        service.client.chat.completions.create = AsyncMock(return_value=_make_response(payload))
        signals = await service.extract_llm_signals(transcript="...", new_segment="...")
        assert len(signals) == 1
        assert signals[0].type == SignalType.RISK

    @pytest.mark.asyncio
    async def test_extract_llm_signals_handles_client_exception(self, service):
        service.client.chat.completions.create = AsyncMock(side_effect=RuntimeError("network error"))
        signals = await service.extract_llm_signals(transcript="...", new_segment="hello")
        assert signals == []


# --- Nudge generation (mocked, async) ---

class TestGenerateNudge:
    @pytest.mark.asyncio
    async def test_generate_nudge_returns_nudge_text(self, service):
        service.client.chat.completions.create = AsyncMock(
            return_value=_make_response("Acknowledge the customer's concern before continuing.")
        )
        signal = Signal(
            type=SignalType.SENTIMENT, text="Customer sounds frustrated",
            confidence=0.75, priority=Priority.HIGH, key_entity="frustration",
        )

        nudge = await service.generate_nudge(signal)

        assert nudge.text == "Acknowledge the customer's concern before continuing."
        assert nudge.confidence == 0.75
        assert nudge.signal_type == "sentiment"

    @pytest.mark.asyncio
    async def test_generate_nudge_accepts_raw_dict(self, service):
        service.client.chat.completions.create = AsyncMock(return_value=_make_response("Offer a payment plan."))
        raw_signal = {"type": "payment_difficulty", "text": "Customer hesitant", "confidence": 0.6, "key_entity": "hesitation"}

        nudge = await service.generate_nudge(raw_signal)

        assert nudge.text == "Offer a payment plan."
        assert nudge.signal_type == "payment_difficulty"

    @pytest.mark.asyncio
    async def test_generate_nudge_falls_back_on_llm_error(self, service):
        service.client.chat.completions.create = AsyncMock(side_effect=RuntimeError("timeout"))
        signal = Signal(
            type=SignalType.RISK, text="Agent overpromised",
            confidence=0.6, priority=Priority.HIGH, key_entity="promise",
        )

        nudge = await service.generate_nudge(signal)

        assert "Agent overpromised" in nudge.text
        assert nudge.confidence == 0.6


# --- Unified extract() ---

class TestUnifiedExtract:
    @pytest.mark.asyncio
    async def test_extract_combines_fast_and_llm_signals(self, service):
        payload = json.dumps([{
            "type": "compliance_gap", "text": "Missing recording disclosure",
            "confidence": 0.8, "priority": "critical", "key_entity": "disclosure",
        }])
        service.client.chat.completions.create = AsyncMock(return_value=_make_response(payload))

        result = await service.extract(transcript="...", new_segment="I will pay on Friday")

        assert result.intent.intent == IntentType.COMMITMENT
        assert len(result.signals) == 1

    @pytest.mark.asyncio
    async def test_extract_skips_llm_call_when_disabled(self, service):
        service.client.chat.completions.create = AsyncMock(side_effect=AssertionError("should not be called"))
        result = await service.extract(
            transcript="...", new_segment="I will pay on Friday", include_llm_signals=False,
        )
        assert result.signals == []

    @pytest.mark.asyncio
    async def test_extract_skips_llm_call_for_empty_segment(self, service):
        service.client.chat.completions.create = AsyncMock(side_effect=AssertionError("should not be called"))
        result = await service.extract(transcript="...", new_segment="   ")
        assert result.signals == []


# --- Adapter for Nudge Pipeline ---

class TestNudgePipelineAdapter:
    def test_to_nudge_pipeline_signals_shape(self, service):
        signal = Signal(
            type=SignalType.CROSS_SELL, text="Mentioned a second vehicle",
            confidence=0.7, priority=Priority.MEDIUM, key_entity="second_vehicle",
        )
        signals = service.to_nudge_pipeline_signals([signal])
        assert signals == [{
            "type": "cross_sell",
            "text": "Mentioned a second vehicle",
            "confidence": 0.7,
            "priority": "medium",
            "key_entity": "second_vehicle",
        }]

    def test_to_nudge_pipeline_signals_empty_list(self, service):
        assert service.to_nudge_pipeline_signals([]) == []