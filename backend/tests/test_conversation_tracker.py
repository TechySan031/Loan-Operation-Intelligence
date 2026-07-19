from app.agents.conversation_tracker import check_compliance, evaluate_rules, update_phase


def state(message: str, **updates):
    base = {"call_id": "call-1", "messages": [{"content": message}], "current_phase": "greeting", "verification_attempts": 0, "objections_raised": [], "compliance_checklist": {}, "turn_count": 0}
    return {**base, **updates}


def test_detects_commitment_phase():
    result = update_phase(state("I will pay on Friday"))
    assert result["current_phase"] == "commit"
    assert result["turn_count"] == 1


def test_updates_compliance_checklist():
    result = check_compliance(state("My name is Ana calling from LOI. This is a payment reminder and the call may be recorded."))
    assert all(result["compliance_checklist"].values())


def test_escalates_after_three_failed_verifications():
    result = evaluate_rules(state("", verification_attempts=3))
    assert result["current_phase"] == "escalate"