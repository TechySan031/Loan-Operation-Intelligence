# Architecture

> See implementation_plan.md for the full architecture document.

## Component Diagram

```
┌─────────────────────────────────────────────────────┐
│                    Client Layer                      │
│  Next.js Dashboard │ Vapi Web Widget │ SSE Client    │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│              API Layer — FastAPI                      │
│  Voice Webhooks │ KB API │ Nudge SSE │ Calls │ Eval  │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│                Service Layer                         │
│  RAG │ Voice │ Rules │ Nudge Engine │ Compliance     │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│              Infrastructure Layer                    │
│  PostgreSQL │ Redis │ Pinecone │ Langfuse │ Deepgram │
└─────────────────────────────────────────────────────┘
```

## Data Flow

1. **Voice Call**: User → Vapi (ASR/TTS) → FastAPI webhook → RAG/Rules → Response → Vapi → User
2. **KB Search**: Query → Embed → Pinecone → Rerank → Cite → Response
3. **Real-time Nudges**: Audio → Deepgram Streaming → Signal Extractor → Nudge Generator → Controls → SSE → Dashboard
