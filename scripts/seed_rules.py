"""
Seed Business Rules Script

Populates the database with business rules for:
- Escalation criteria
- Compliance requirements
- Qualification logic
- Payment rules

Usage:
    python -m scripts.seed_rules
"""

import asyncio
import uuid
import sys
import os

# Force the correct backend on the path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
sys.path.insert(0, backend_path)
for p in list(sys.path):
    if p != backend_path and os.path.exists(os.path.join(p, "app", "config.py")):
        sys.path.remove(p)


BUSINESS_RULES = [
    # --- Escalation Rules ---
    {
        "rule_id": "rule_escalation_001",
        "name": "Escalate on repeated objections",
        "description": "Transfer to human agent after 3+ unresolved objections",
        "category": "escalation",
        "rule_type": "threshold",
        "condition": {"field": "objection_count", "operator": "gte", "value": 3},
        "action": {"type": "escalate", "reason": "Multiple unresolved objections", "priority": "high"},
        "priority": 100,
    },
    {
        "rule_id": "rule_escalation_002",
        "name": "Escalate on verification failure",
        "description": "Transfer to human after 3 failed identity verification attempts",
        "category": "escalation",
        "rule_type": "threshold",
        "condition": {"field": "verification_attempts", "operator": "gte", "value": 3},
        "action": {"type": "escalate", "reason": "Identity verification failed", "priority": "urgent"},
        "priority": 200,
    },
    {
        "rule_id": "rule_escalation_003",
        "name": "Escalate on explicit request",
        "description": "Always honor customer request for human agent",
        "category": "escalation",
        "rule_type": "pattern",
        "condition": {"field": "customer_requested_human", "operator": "eq", "value": True},
        "action": {"type": "escalate", "reason": "Customer requested human agent", "priority": "normal"},
        "priority": 300,
    },
    {
        "rule_id": "rule_escalation_004",
        "name": "Escalate on high frustration",
        "description": "Transfer if sentiment drops below -0.7",
        "category": "escalation",
        "rule_type": "threshold",
        "condition": {"field": "sentiment_score", "operator": "lt", "value": -0.7},
        "action": {"type": "escalate", "reason": "High customer frustration detected", "priority": "high"},
        "priority": 150,
    },
    # --- Compliance Rules ---
    {
        "rule_id": "rule_compliance_001",
        "name": "Agent identity disclosure",
        "description": "Agent must identify themselves and company within first 30 seconds",
        "category": "compliance",
        "rule_type": "checklist",
        "condition": {"and": [
            {"field": "turn_count", "operator": "gte", "value": 2},
            {"field": "compliance_checklist.identity_disclosed", "operator": "eq", "value": False},
        ]},
        "action": {"type": "warn", "message": "Agent has not disclosed identity. Required by fair practice code."},
        "priority": 200,
    },
    {
        "rule_id": "rule_compliance_002",
        "name": "Purpose disclosure",
        "description": "Agent must state the purpose of the call",
        "category": "compliance",
        "rule_type": "checklist",
        "condition": {"and": [
            {"field": "turn_count", "operator": "gte", "value": 3},
            {"field": "compliance_checklist.purpose_stated", "operator": "eq", "value": False},
        ]},
        "action": {"type": "warn", "message": "Call purpose not yet stated. Disclose before proceeding."},
        "priority": 190,
    },
    # --- Payment Rules ---
    {
        "rule_id": "rule_payment_001",
        "name": "Offer EMI holiday for long-term customers",
        "description": "Customers with 12+ months of regular payments qualify for EMI holiday",
        "category": "payment",
        "rule_type": "threshold",
        "condition": {"and": [
            {"field": "months_regular_payment", "operator": "gte", "value": 12},
            {"field": "payment_difficulty_expressed", "operator": "eq", "value": True},
        ]},
        "action": {"type": "suggest", "message": "Customer qualifies for EMI holiday. Offer this option."},
        "priority": 80,
    },
    {
        "rule_id": "rule_payment_002",
        "name": "Grace period reminder",
        "description": "Inform about grace period if payment is within 5 days of due date",
        "category": "payment",
        "rule_type": "threshold",
        "condition": {"field": "days_until_due", "operator": "lte", "value": 5},
        "action": {"type": "inform", "message": "Payment is within grace period window. Mention 3-day grace period."},
        "priority": 70,
    },
]


async def main():
    """Seed business rules into the database."""
    from app.core.database import init_db, async_session_factory
    from app.models.business_rule import BusinessRule

    await init_db()

    async with async_session_factory() as session:
        from sqlalchemy import delete
        # Clear existing rules to prevent unique constraint violations on retry
        await session.execute(delete(BusinessRule))
        
        for rule_data in BUSINESS_RULES:
            rule = BusinessRule(
                id=uuid.uuid4(),
                **rule_data,
                active=True,
                market="all",
            )
            session.add(rule)
        
        await session.commit()
        print(f"Seeded {len(BUSINESS_RULES)} business rules")


if __name__ == "__main__":
    asyncio.run(main())
