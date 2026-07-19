"""
Nudge Schemas — Pydantic Models

Request/response schemas for nudge streaming and analysis endpoints.
"""

from datetime import datetime
from pydantic import BaseModel, Field


class NudgeResponse(BaseModel):
    """Schema for a nudge delivered via SSE/WebSocket."""
    id: str
    call_id: str
    signal_type: str
    signal_text: str
    nudge_text: str
    confidence: float
    priority: str
    latency_ms: dict | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class NudgeAnalysis(BaseModel):
    """Schema for nudge quality analysis."""
    call_id: str
    total_nudges: int
    delivered_nudges: int
    suppressed_nudges: int
    suppression_breakdown: dict = Field(
        default_factory=dict,
        description='{"duplicate": 2, "cooldown": 1, "low_confidence": 3}'
    )
    avg_confidence: float
    avg_latency_ms: dict = Field(
        default_factory=dict,
        description='{"asr": 180, "signal": 95, "llm": 320, "delivery": 15, "total": 610}'
    )
    p50_latency_ms: float
    p95_latency_ms: float
    signal_type_breakdown: dict = Field(
        default_factory=dict,
        description='{"compliance_gap": 2, "sentiment": 1, ...}'
    )
    false_positive_estimate: float = Field(
        0.0, description="Estimated false positive rate (0.0 - 1.0)"
    )


class StartNudgeSessionRequest(BaseModel):
    """Schema for starting a real-time nudge session."""
    call_id: str
    audio_source: str = Field(
        ..., description="live | file_path to audio for simulation"
    )
    chunk_ms: int = Field(250, description="Audio chunk size in milliseconds")


class LatencyReport(BaseModel):
    """Schema for the Q4 latency report."""
    total_calls_analyzed: int
    total_nudges_generated: int
    total_nudges_delivered: int
    total_nudges_suppressed: int
    component_latency: dict = Field(
        description="Per-component P50/P95 latency in ms"
    )
    end_to_end_latency: dict = Field(
        description='{"p50": 610, "p95": 890}'
    )
    signal_type_accuracy: dict = Field(
        description="Per signal type: delivered vs false positive"
    )
