"""Conversation state tracker for the real-time voice workflow."""

import logging
import re

from langgraph.graph import END, StateGraph

from app.agents.states import ConversationState
from app.services.signal_extraction_service import get_signal_extraction_service

logger = logging.getLogger(__name__)

_PHASES = (
    ("escalate", ("supervisor", "human agent", "complaint", "escalate")),
    ("callback", ("call me back", "call back", "callback", "later today")),
    ("commit", ("i will pay", "will make payment", "pay on", "payment by")),
    ("objection", ("can't pay", "cannot pay", "too much", "not able to", "financial difficulty")),
    ("question", ("?", "what is", "why is", "how do", "when is")),
    ("options", ("payment option", "installment", "payment plan", "can pay via")),
    ("remind", ("amount due", "payment due", "emi due", "installment due")),
    ("verify", ("verify", "date of birth", "last four", "confirm your identity")),
    ("greeting", ("hello", "good morning", "good afternoon", "good evening")),
)


def _message_text(messages: list[dict]) -> str:
    return " ".join(str(message.get("content") or message.get("text") or "") for message in messages).lower()


def extract_signals(state: ConversationState) -> ConversationState:
    """Run fast, deterministic intent/entity extraction and enrich state before phase detection.

    Populates objections_raised, questions_asked, commitment, callback, and
    escalation_reason — fields the rest of this graph declares but, prior to
    this node, never actually wrote to. Also offers a current_phase fallback
    hint that update_phase's own _PHASES matching may override.

    This runs synchronously (regex/keyword based, no LLM round-trip) so it adds
    negligible latency to the per-turn voice path. The richer LLM-based signal
    detection (compliance gaps, sentiment, cross-sell) stays in the async
    Nudge Pipeline (Q4), which already batches ~30 words before calling the LLM.
    See app.services.signal_extraction_service for the full design rationale.
    """
    if state.get("current_phase") in {"wrap_up", "escalate"}:
        return state
    latest = _message_text(state.get("messages", [])[-2:])
    if not latest.strip():
        return state
    service = get_signal_extraction_service()
    result = service.extract_fast(latest)
    return service.apply_to_conversation_state(result, state)


def update_phase(state: ConversationState) -> ConversationState:
    """Advance state from the latest utterances without regressing terminal states."""
    current = state.get("current_phase", "greeting")
    if current in {"wrap_up", "escalate"}:
        return state
    latest = _message_text(state.get("messages", [])[-2:])
    phase = current
    for candidate, phrases in _PHASES:
        if any(phrase in latest for phrase in phrases):
            phase = candidate
            break
    attempts = state.get("verification_attempts", 0)
    if phase == "verify" and re.search(r"\b(incorrect|wrong|no)\b", latest):
        attempts += 1
    return {**state, "current_phase": phase, "verification_attempts": attempts, "turn_count": state.get("turn_count", 0) + 1}


def check_compliance(state: ConversationState) -> ConversationState:
    """Update the required disclosure checklist from the transcript."""
    transcript = _message_text(state.get("messages", []))
    checklist = dict(state.get("compliance_checklist", {}))
    checklist.update({
        "identity_disclosed": any(value in transcript for value in ("my name is", "calling from", "on behalf of")),
        "purpose_stated": any(value in transcript for value in ("payment reminder", "upcoming payment", "emi due", "installment due")),
        "recording_mentioned": any(value in transcript for value in ("recorded", "recording", "quality purposes")),
    })
    return {**state, "compliance_checklist": checklist}


def evaluate_rules(state: ConversationState) -> ConversationState:
    """Apply deterministic safety escalations and injected rule-engine actions."""
    if state.get("verification_attempts", 0) >= 3:
        return {**state, "current_phase": "escalate", "escalation_reason": "Verification failed 3 times"}
    if len(state.get("objections_raised", [])) >= 3:
        return {**state, "current_phase": "escalate", "escalation_reason": "Multiple unresolved objections"}
    for result in state.get("rule_actions", []):
        action = result.get("action", result)
        if action.get("type") in {"escalate", "transfer"} or action.get("escalate"):
            return {**state, "current_phase": "escalate", "escalation_reason": action.get("reason", result.get("name", "Business rule triggered"))}
    return state


def log_transition(state: ConversationState) -> ConversationState:
    logger.info("Call %s: phase=%s turn=%s objections=%s", state.get("call_id"), state.get("current_phase"), state.get("turn_count", 0), len(state.get("objections_raised", [])))
    return state


def should_continue(state: ConversationState) -> str:
    return "end" if state.get("current_phase") in {"wrap_up", "escalate"} else "continue"


def build_conversation_tracker() -> StateGraph:
    graph = StateGraph(ConversationState)
    for node in (extract_signals, update_phase, check_compliance, evaluate_rules, log_transition):
        graph.add_node(node.__name__, node)
    graph.set_entry_point("extract_signals")
    graph.add_edge("extract_signals", "update_phase")
    graph.add_edge("update_phase", "check_compliance")
    graph.add_edge("check_compliance", "evaluate_rules")
    graph.add_edge("evaluate_rules", "log_transition")
    graph.add_conditional_edges("log_transition", should_continue, {"continue": END, "end": END})
    return graph