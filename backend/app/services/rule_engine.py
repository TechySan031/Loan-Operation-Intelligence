"""
Business Rule Engine (Q1)

Declarative rule engine that evaluates business rules against conversation state.

Rule types:
- escalation: When to transfer to a human agent
- compliance: Required disclosures and statements
- qualification: Eligibility checks for programs
- payment: Grace periods, late fees, penalty rules

Rules are stored in PostgreSQL and loaded at startup.
Each rule has a declarative condition (JSON) and action (JSON).

Condition operators: eq, neq, gt, gte, lt, lte, in, contains, matches
"""

import logging
import operator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.business_rule import BusinessRule

logger = logging.getLogger(__name__)

# Operator mapping for declarative conditions
OPERATORS = {
    "eq": operator.eq,
    "neq": operator.ne,
    "gt": operator.gt,
    "gte": operator.ge,
    "lt": operator.lt,
    "lte": operator.le,
    "in": lambda a, b: a in b,
    "contains": lambda a, b: b in a if isinstance(a, str) else b in a,
}


class RuleEngine:
    """
    Declarative business rule engine.
    
    Usage:
        engine = RuleEngine(db)
        actions = await engine.evaluate(conversation_state)
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self._rules_cache: list[BusinessRule] | None = None

    async def load_rules(self, category: str | None = None, market: str = "all") -> list[BusinessRule]:
        """Load active rules from database, optionally filtered by category and market."""
        query = select(BusinessRule).where(BusinessRule.active == True)
        if category:
            query = query.where(BusinessRule.category == category)

        query = query.where(
            (BusinessRule.market == market) | (BusinessRule.market == "all")
        )
        query = query.order_by(BusinessRule.priority.desc())

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def evaluate(self, state: dict, category: str | None = None, market: str = "all") -> list[dict]:
        """
        Evaluate all matching rules against the conversation state.
        
        Args:
            state: Current conversation state dict
            category: Optional category filter
            market: Market filter (default: all)
        
        Returns:
            List of triggered actions: [{"rule_id": "...", "action": {...}}]
        """
        rules = await self.load_rules(category=category, market=market)
        triggered_actions = []

        for rule in rules:
            if self._evaluate_condition(rule.condition, state):
                logger.info(f"Rule triggered: {rule.rule_id} - {rule.name}")
                triggered_actions.append({
                    "rule_id": rule.rule_id,
                    "name": rule.name,
                    "action": rule.action,
                    "priority": rule.priority,
                })

        return triggered_actions

    def _evaluate_condition(self, condition: dict, state: dict) -> bool:
        """
        Evaluate a single declarative condition against state.
        
        Condition format:
            {"field": "objection_count", "operator": "gte", "value": 3}
        
        Compound conditions:
            {"and": [condition1, condition2]}
            {"or": [condition1, condition2]}
        """
        # Compound: AND
        if "and" in condition:
            return all(self._evaluate_condition(c, state) for c in condition["and"])

        # Compound: OR
        if "or" in condition:
            return any(self._evaluate_condition(c, state) for c in condition["or"])

        # Simple condition
        field = condition.get("field", "")
        op_name = condition.get("operator", "eq")
        expected_value = condition.get("value")

        actual_value = self._get_nested_value(state, field)
        if actual_value is None:
            return False

        op_func = OPERATORS.get(op_name)
        if not op_func:
            logger.warning(f"Unknown operator: {op_name}")
            return False

        try:
            return op_func(actual_value, expected_value)
        except (TypeError, ValueError) as e:
            logger.warning(f"Rule evaluation error: {e}")
            return False

    def _get_nested_value(self, state: dict, field: str):
        """Get a potentially nested value from state using dot notation."""
        keys = field.split(".")
        value = state
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return None
        return value

    async def check_compliance(self, state: dict, market: str = "all") -> list[dict]:
        """Check compliance rules and return any violations or required disclosures."""
        return await self.evaluate(state, category="compliance", market=market)

    async def check_escalation(self, state: dict, market: str = "all") -> list[dict]:
        """Check if escalation is required based on current state."""
        return await self.evaluate(state, category="escalation", market=market)
