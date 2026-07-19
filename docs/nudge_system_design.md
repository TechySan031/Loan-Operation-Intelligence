# Real-Time Nudge System Design (Q4)

## Pipeline

Audio → Deepgram Streaming ASR → Transcript Buffer → Signal Extractor (GPT-4o) → Nudge Generator → Controls → SSE → Dashboard

## Signal Types

| Signal | Description | Example |
|--------|-------------|---------|
| compliance_gap | Missing disclosure, risky statement | Agent didn't identify themselves |
| sentiment | Frustration, anger, confusion | Customer raising voice |
| cross_sell | Opportunity for additional products | Customer mentions another loan |
| missed_opportunity | Agent missed a chance to help | Didn't offer hardship program |
| payment_difficulty | Financial hardship indicators | Job loss, medical bills |
| risk | Incorrect or misleading information | False promises |

## Nudge Controls

| Control | Configuration |
|---------|--------------|
| Confidence threshold | 0.6 minimum |
| Cooldown | 15 seconds between nudges |
| Max per call | 8 nudges |
| Dedup window | 60 seconds |
| Expiry | 45 seconds |

## Latency Targets

| Component | Target P95 |
|-----------|-----------|
| ASR | < 300ms |
| Signal extraction | < 150ms |
| LLM nudge generation | < 500ms |
| Delivery | < 50ms |
| End-to-end | < 1000ms |

## Latency Report

See `evaluation/results/` for actual measurements.
