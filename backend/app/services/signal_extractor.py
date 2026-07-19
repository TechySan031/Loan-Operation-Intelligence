"""
Signal Extractor — LLM-Based Signal Detection (Q4)

Analyzes conversation transcript segments to detect:
- Compliance gaps (missed disclosures, risky statements)
- Sentiment shifts (rising frustration, confusion)
- Buying signals (interest in products, upgrade intent)
- Missed opportunities (cross-sell, upsell)
- Payment difficulty indicators
- Callback/escalation needs

Uses GPT-4o for high-quality signal extraction.
"""

import logging
import json
from openai import AsyncOpenAI

from app.config import settings

logger = logging.getLogger(__name__)

SIGNAL_EXTRACTION_PROMPT = """You are a real-time call analysis system for a loan pre-due reminder call center.

Analyze the following conversation segment and detect any actionable signals.

SIGNAL TYPES:
1. compliance_gap — Agent missed a required disclosure, made a risky/misleading statement, or violated fair practice guidelines
2. sentiment — Customer shows frustration, anger, confusion, or significant emotional shift
3. cross_sell — Customer mentions needs that could be addressed by other products or services
4. missed_opportunity — Agent missed a chance to address a concern, offer a solution, or build rapport
5. payment_difficulty — Customer indicates financial hardship, inability to pay, or requests for concessions
6. risk — Agent made a promise they can't keep, or provided potentially incorrect information

For each signal detected, provide:
- type: one of the signal types above
- text: brief description of what was detected
- confidence: 0.0 to 1.0 (how certain you are this is a real signal)
- priority: critical | high | medium | low
- key_entity: the key entity or concept involved (for deduplication)

Return a JSON array of signals. Return empty array [] if no signals detected.
Be conservative — only flag genuine, actionable signals. Avoid false positives.

FULL CONVERSATION SO FAR:
{transcript}

NEW SEGMENT TO ANALYZE:
{new_segment}

Respond with ONLY a valid JSON array:"""

NUDGE_GENERATION_PROMPT = """Generate a short, actionable nudge for a call center agent based on this signal:

Signal Type: {signal_type}
Signal: {signal_text}

Requirements:
- Maximum 2 sentences
- Must be immediately actionable
- Must be specific to the situation
- Do not be vague or generic

Respond with ONLY the nudge text, no JSON or formatting:"""


class SignalExtractor:
    """
    LLM-based signal extraction from conversation transcripts.
    
    Usage:
        extractor = SignalExtractor()
        signals = await extractor.extract(transcript="...", new_segment="...")
    """

    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_LLM_MODEL  # GPT-4o for quality

    async def extract(self, transcript: str, new_segment: str) -> list[dict]:
        """
        Extract signals from a conversation transcript segment.
        
        Args:
            transcript: Full conversation so far
            new_segment: New text to analyze
        
        Returns:
            List of signal dicts: [{type, text, confidence, priority, key_entity}]
        """
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a precise real-time call analysis system. Only detect genuine, actionable signals. Minimize false positives."
                    },
                    {
                        "role": "user",
                        "content": SIGNAL_EXTRACTION_PROMPT.format(
                            transcript=transcript[-2000:],  # Last 2000 chars for context
                            new_segment=new_segment,
                        ),
                    },
                ],
                temperature=0.1,  # Low temperature for consistent detection
                max_tokens=500,
            )

            content = response.choices[0].message.content.strip()

            # Parse JSON response
            signals = json.loads(content)
            if isinstance(signals, list):
                return signals
            return []

        except json.JSONDecodeError:
            logger.warning("Failed to parse signal extraction response as JSON")
            return []
        except Exception as e:
            logger.error(f"Signal extraction failed: {e}")
            return []

    async def generate_nudge(self, signal: dict) -> dict:
        """
        Generate an actionable nudge from a detected signal.
        
        Args:
            signal: Signal dict from extract()
        
        Returns:
            Nudge dict: {text, confidence, signal_type, key_entity}
        """
        try:
            response = await self.client.chat.completions.create(
                model=settings.OPENAI_LLM_MODEL_MINI,  # Use mini for speed
                messages=[
                    {
                        "role": "user",
                        "content": NUDGE_GENERATION_PROMPT.format(
                            signal_type=signal.get("type", ""),
                            signal_text=signal.get("text", ""),
                        ),
                    },
                ],
                temperature=0.3,
                max_tokens=100,
            )

            nudge_text = response.choices[0].message.content.strip()
            return {
                "text": nudge_text,
                "confidence": signal.get("confidence", 0.5),
                "signal_type": signal.get("type", ""),
                "key_entity": signal.get("key_entity", ""),
            }

        except Exception as e:
            logger.error(f"Nudge generation failed: {e}")
            return {
                "text": f"Check: {signal.get('text', 'Signal detected')}",
                "confidence": signal.get("confidence", 0.5),
                "signal_type": signal.get("type", ""),
                "key_entity": signal.get("key_entity", ""),
            }
