# Latency Report (Q4)

## Methodology

Audio recordings from Q1 test calls are replayed at real-time speed through the nudge pipeline.
Latency is measured at each component using `time.time()` with millisecond precision.

## Component Latency

| Component | P50 (ms) | P95 (ms) | Notes |
|-----------|---------|---------|-------|
| ASR (Deepgram) | — | — | To be measured |
| Signal Extraction | — | — | To be measured |
| LLM Nudge Gen | — | — | To be measured |
| Delivery (SSE) | — | — | To be measured |
| **End-to-End** | — | — | To be measured |

## Results

*To be populated after running `make simulate` with test audio.*
