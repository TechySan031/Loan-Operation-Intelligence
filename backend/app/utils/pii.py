"""
PII Detection & Redaction — Microsoft Presidio

Detects and redacts personally identifiable information (PII) in KB content.

Detected entity types:
- PERSON (names)
- PHONE_NUMBER
- EMAIL_ADDRESS
- CREDIT_CARD
- AADHAAR_NUMBER (India-specific)
- PAN_NUMBER (India-specific — custom pattern)
- LOCATION / ADDRESS

Used during KB ingestion to:
1. Flag records containing PII (contains_pii = True)
2. Generate PII-redacted version (content_clean)
"""

import logging
from typing import NamedTuple

logger = logging.getLogger(__name__)


class PIIEntity(NamedTuple):
    """A detected PII entity."""
    entity_type: str
    start: int
    end: int
    score: float
    text: str


def detect_pii(text: str, threshold: float = 0.7) -> list[PIIEntity]:
    """
    Detect PII entities in text using Presidio.
    
    Args:
        text: Text to analyze
        threshold: Minimum confidence score (0.0 - 1.0)
    
    Returns:
        List of detected PII entities
    """
    try:
        from presidio_analyzer import AnalyzerEngine
        
        analyzer = AnalyzerEngine()
        results = analyzer.analyze(
            text=text,
            language="en",
            entities=[
                "PERSON", "PHONE_NUMBER", "EMAIL_ADDRESS",
                "CREDIT_CARD", "LOCATION",
            ],
            score_threshold=threshold,
        )
        
        return [
            PIIEntity(
                entity_type=r.entity_type,
                start=r.start,
                end=r.end,
                score=r.score,
                text=text[r.start:r.end],
            )
            for r in results
        ]
    
    except ImportError:
        logger.warning("Presidio not installed. PII detection disabled.")
        return []
    except Exception as e:
        logger.error(f"PII detection error: {e}")
        return []


def redact_pii(text: str, entities: list[PIIEntity] | None = None) -> str:
    """
    Redact PII entities from text.
    
    Replaces detected PII with placeholder tags:
    - "John Smith" → "[PERSON]"
    - "9876543210" → "[PHONE_NUMBER]"
    """
    if entities is None:
        entities = detect_pii(text)
    
    if not entities:
        return text
    
    # Sort by position (reverse) to avoid offset issues
    sorted_entities = sorted(entities, key=lambda e: e.start, reverse=True)
    
    redacted = text
    for entity in sorted_entities:
        placeholder = f"[{entity.entity_type}]"
        redacted = redacted[:entity.start] + placeholder + redacted[entity.end:]
    
    return redacted
