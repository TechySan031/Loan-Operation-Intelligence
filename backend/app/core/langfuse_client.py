"""
Langfuse Client — LLM Observability

Provides:
- Trace creation for LLM calls
- Span tracking for RAG pipeline components
- Evaluation scoring
- Used across voice agent, RAG service, and nudge engine

Pattern reused from Production GenAI MLOps Platform.
"""

import logging

from app.config import settings

logger = logging.getLogger(__name__)

# Try to import Langfuse, gracefully handle if not installed
try:
    from langfuse import Langfuse
    LANGFUSE_AVAILABLE = True
except ImportError:
    LANGFUSE_AVAILABLE = False


# --- Global Client ---
langfuse_client: Langfuse | None = None


def init_langfuse():
    """Initialize Langfuse client. Called on app startup."""
    global langfuse_client

    if not LANGFUSE_AVAILABLE:
        logger.warning("Langfuse package not installed. Observability disabled.")
        return
    
    if not settings.LANGFUSE_PUBLIC_KEY or not settings.LANGFUSE_SECRET_KEY:
        logger.warning("Langfuse keys not configured. Observability disabled.")
        return
    
    langfuse_client = Langfuse(
        public_key=settings.LANGFUSE_PUBLIC_KEY,
        secret_key=settings.LANGFUSE_SECRET_KEY,
        host=settings.LANGFUSE_HOST,
    )


def get_langfuse() -> Langfuse | None:
    """Get the Langfuse client. Returns None if not configured."""
    return langfuse_client


def create_trace(name: str, metadata: dict | None = None, **kwargs):
    """
    Create a Langfuse trace if supported.
    Otherwise, disable tracing gracefully.
    """
    if langfuse_client is None:
        return None

    # Older/newer SDK compatibility
    if not hasattr(langfuse_client, "trace"):
        logger.warning(
            "Langfuse SDK does not support .trace(); tracing disabled."
        )
        return None

    return langfuse_client.trace(
        name=name,
        metadata=metadata or {},
        **kwargs,
    )


def score_trace(trace_id: str, name: str, value: float, comment: str = ""):
    if langfuse_client is None:
        return

    if not hasattr(langfuse_client, "score"):
        return

    langfuse_client.score(
        trace_id=trace_id,
        name=name,
        value=value,
        comment=comment,
    )


def flush():
    """Flush pending Langfuse events. Call before shutdown."""
    if langfuse_client:
        langfuse_client.flush()
