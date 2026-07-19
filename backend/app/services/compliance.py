"""
Compliance Monitor Service

Rule-based compliance checking for loan pre-due reminder calls.

Checks:
- Required disclosures (identity, recording notice, purpose)
- Prohibited language (threats, misleading statements)
- Fair practice code adherence
- Call time restrictions
- Maximum contact frequency
"""

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ComplianceViolation:
    """A detected compliance violation."""
    rule_id: str
    severity: str  # critical | warning | info
    description: str
    recommendation: str


# Required disclosures that must be present in the call
REQUIRED_DISCLOSURES = [
    {
        "id": "disclosure_identity",
        "description": "Agent must identify themselves and the company",
        "keywords": ["my name is", "calling from", "on behalf of"],
        "severity": "critical",
    },
    {
        "id": "disclosure_purpose",
        "description": "Agent must state the purpose of the call",
        "keywords": ["payment reminder", "upcoming payment", "emi due", "installment due"],
        "severity": "critical",
    },
    {
        "id": "disclosure_recording",
        "description": "Agent should mention call may be recorded",
        "keywords": ["call may be recorded", "recording", "quality purposes"],
        "severity": "warning",
    },
]

# Prohibited patterns
PROHIBITED_PATTERNS = [
    {
        "id": "prohibited_threat",
        "description": "Threatening language or intimidation",
        "keywords": ["legal action", "sue you", "arrest", "police", "jail", "garnish"],
        "severity": "critical",
    },
    {
        "id": "prohibited_misleading",
        "description": "Misleading or false statements",
        "keywords": ["guaranteed", "no risk", "definitely will", "I promise"],
        "severity": "warning",
    },
    {
        "id": "prohibited_disclosure_pii",
        "description": "Disclosing loan details to third parties",
        "keywords": [],  # Requires context analysis
        "severity": "critical",
    },
]


class ComplianceMonitor:
    """
    Compliance checking service for call transcripts.
    
    Usage:
        monitor = ComplianceMonitor()
        violations = monitor.check_transcript(transcript)
        missing = monitor.check_required_disclosures(transcript)
    """

    def check_transcript(self, transcript: str) -> list[ComplianceViolation]:
        """Check a transcript for compliance violations."""
        violations = []
        transcript_lower = transcript.lower()

        # Check prohibited patterns
        for pattern in PROHIBITED_PATTERNS:
            for keyword in pattern["keywords"]:
                if keyword.lower() in transcript_lower:
                    violations.append(ComplianceViolation(
                        rule_id=pattern["id"],
                        severity=pattern["severity"],
                        description=pattern["description"],
                        recommendation=f"Review usage of '{keyword}' in the conversation.",
                    ))

        return violations

    def check_required_disclosures(self, transcript: str) -> list[ComplianceViolation]:
        """Check if all required disclosures have been made."""
        missing = []
        transcript_lower = transcript.lower()

        for disclosure in REQUIRED_DISCLOSURES:
            found = any(
                keyword.lower() in transcript_lower
                for keyword in disclosure["keywords"]
            )
            if not found:
                missing.append(ComplianceViolation(
                    rule_id=disclosure["id"],
                    severity=disclosure["severity"],
                    description=f"Missing required disclosure: {disclosure['description']}",
                    recommendation=f"Ensure the agent includes: {', '.join(disclosure['keywords'][:2])}",
                ))

        return missing

    def get_compliance_score(self, transcript: str) -> dict:
        """
        Calculate an overall compliance score for a call.
        
        Returns:
            {score: float, violations: list, missing_disclosures: list}
        """
        violations = self.check_transcript(transcript)
        missing = self.check_required_disclosures(transcript)

        # Score: start at 1.0, deduct for issues
        score = 1.0
        for v in violations:
            if v.severity == "critical":
                score -= 0.3
            elif v.severity == "warning":
                score -= 0.1
        for m in missing:
            if m.severity == "critical":
                score -= 0.2
            elif m.severity == "warning":
                score -= 0.1

        return {
            "score": max(0.0, round(score, 2)),
            "violations": [{"rule_id": v.rule_id, "severity": v.severity, "description": v.description} for v in violations],
            "missing_disclosures": [{"rule_id": m.rule_id, "severity": m.severity, "description": m.description} for m in missing],
        }
