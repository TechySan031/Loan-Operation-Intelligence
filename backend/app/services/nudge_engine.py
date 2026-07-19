"""
Nudge Engine — Real-Time Call Analysis & Nudge Generation (Q4 Core)

Orchestrates the full real-time nudge pipeline:
1. Audio input (live stream or simulated replay)
2. Streaming ASR via Deepgram → transcript segments
3. Signal extraction via LLM (GPT-4o)
4. Nudge generation with actionable recommendations
5. Nudge control (confidence threshold, dedup, cooldown, priority, expiry)
6. Delivery via Redis pub/sub → SSE to dashboard
7. Latency measurement at each component

Pipeline: audio → ASR → buffer → signals → nudges → controls → deliver
"""

import time
import uuid
import json
import asyncio
import logging
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.nudge import Nudge
from app.core.redis import publish_nudge
from app.services.signal_extractor import SignalExtractor
from app.services.streaming_asr import StreamingASR
from app.utils.latency import LatencyTracker

logger = logging.getLogger(__name__)

# --- Nudge Control Constants ---
CONFIDENCE_THRESHOLD = 0.6
COOLDOWN_SECONDS = 15
MAX_NUDGES_PER_CALL = 8
DEDUP_WINDOW_SECONDS = 60
NUDGE_EXPIRY_SECONDS = 45


class NudgeEngine:
    """
    Real-time nudge generation engine.
    
    Usage:
        engine = NudgeEngine(db)
        session_id = await engine.start_session(call_id="...", audio_source="file.wav")
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.signal_extractor = SignalExtractor()
        self.streaming_asr = StreamingASR()
        self._active_sessions: dict[str, asyncio.Task] = {}
        self._nudge_history: dict[str, list] = {}  # call_id → list of recent nudges
        self._last_nudge_time: dict[str, float] = {}  # call_id → timestamp

    async def start_session(
        self,
        call_id: str,
        audio_source: str,
        chunk_ms: int = 250,
    ) -> str:
        """
        Start a nudge processing session.
        
        Args:
            call_id: The call to monitor
            audio_source: "live" or path to audio file for simulation
            chunk_ms: Audio chunk size in milliseconds
        
        Returns:
            Session ID
        """
        session_id = str(uuid.uuid4())
        self._nudge_history[call_id] = []
        self._last_nudge_time[call_id] = 0

        if audio_source == "live":
            task = asyncio.create_task(self._process_live(call_id))
        else:
            task = asyncio.create_task(
                self._process_simulated(call_id, audio_source, chunk_ms)
            )

        self._active_sessions[call_id] = task
        return session_id

    async def stop_session(self, call_id: str):
        """Stop an active nudge session."""
        task = self._active_sessions.pop(call_id, None)
        if task:
            task.cancel()

    async def _process_simulated(self, call_id: str, audio_path: str, chunk_ms: int):
        """
        Process a recorded audio file at real-time speed.
        
        Reads audio, chunks it, sends to Deepgram streaming,
        processes transcript for signals, generates nudges.
        """
        latency = LatencyTracker()
        transcript_buffer = ""
        last_processed_pos = 0

        try:
            async for segment in self.streaming_asr.transcribe_file(audio_path, chunk_ms):
                # Measure ASR latency
                asr_latency = segment.get("latency_ms", 0)

                # Buffer transcript
                transcript_buffer += " " + segment.get("text", "")

                # Process every ~500 words or significant new content
                new_text = transcript_buffer[last_processed_pos:]
                if len(new_text.split()) >= 30:  # Process every ~30 words
                    # Extract signals
                    signal_start = time.time()
                    signals = await self.signal_extractor.extract(
                        transcript=transcript_buffer,
                        new_segment=new_text,
                    )
                    signal_latency = (time.time() - signal_start) * 1000

                    for signal in signals:
                        # Generate nudge
                        llm_start = time.time()
                        nudge = await self.signal_extractor.generate_nudge(signal)
                        llm_latency = (time.time() - llm_start) * 1000

                        # Apply controls
                        delivery_start = time.time()
                        should_deliver, suppression_reason = self._apply_controls(
                            call_id, nudge
                        )
                        delivery_latency = (time.time() - delivery_start) * 1000

                        # Build latency breakdown
                        latency_ms = {
                            "asr": round(asr_latency, 2),
                            "signal": round(signal_latency, 2),
                            "llm": round(llm_latency, 2),
                            "delivery": round(delivery_latency, 2),
                            "total": round(asr_latency + signal_latency + llm_latency + delivery_latency, 2),
                        }

                        # Save nudge to DB
                        db_nudge = Nudge(
                            id=uuid.uuid4(),
                            call_id=uuid.UUID(call_id) if self._is_uuid(call_id) else uuid.uuid4(),
                            signal_type=signal["type"],
                            signal_text=signal["text"],
                            nudge_text=nudge["text"],
                            confidence=signal["confidence"],
                            priority=signal.get("priority", "medium"),
                            displayed=should_deliver,
                            suppressed=not should_deliver,
                            suppression_reason=suppression_reason,
                            latency_ms=latency_ms,
                            transcript_position=len(transcript_buffer.split()),
                        )
                        self.db.add(db_nudge)

                        # Deliver if not suppressed
                        if should_deliver:
                            await publish_nudge(call_id, {
                                "id": str(db_nudge.id),
                                "signal_type": signal["type"],
                                "signal_text": signal["text"],
                                "nudge_text": nudge["text"],
                                "confidence": signal["confidence"],
                                "priority": signal.get("priority", "medium"),
                                "latency_ms": latency_ms,
                                "timestamp": datetime.utcnow().isoformat(),
                            })
                            self._last_nudge_time[call_id] = time.time()

                    last_processed_pos = len(transcript_buffer)

            await self.db.flush()

        except asyncio.CancelledError:
            logger.info(f"Nudge session cancelled for call {call_id}")
        except Exception as e:
            logger.error(f"Nudge session error for call {call_id}: {e}")

    async def _process_live(self, call_id: str):
        """Process live call audio (hooks into Vapi real-time events)."""
        # TODO: Implement live call processing
        # This would subscribe to Vapi's real-time transcript events
        # and process them through the same signal extraction pipeline
        pass

    def _apply_controls(self, call_id: str, nudge: dict) -> tuple[bool, str | None]:
        """
        Apply nudge control rules.
        
        Returns: (should_deliver, suppression_reason)
        """
        # 1. Confidence threshold
        if nudge.get("confidence", 0) < CONFIDENCE_THRESHOLD:
            return False, "low_confidence"

        # 2. Cooldown
        last_time = self._last_nudge_time.get(call_id, 0)
        if time.time() - last_time < COOLDOWN_SECONDS:
            return False, "cooldown"

        # 3. Max per call
        history = self._nudge_history.get(call_id, [])
        delivered_count = sum(1 for n in history if not n.get("suppressed"))
        if delivered_count >= MAX_NUDGES_PER_CALL:
            return False, "max_per_call"

        # 4. Duplicate suppression
        nudge_key = f"{nudge.get('signal_type')}:{nudge.get('key_entity', '')}"
        recent_keys = [n.get("key") for n in history[-10:]]
        if nudge_key in recent_keys:
            return False, "duplicate"

        # Record in history
        history.append({
            "key": nudge_key,
            "time": time.time(),
            "suppressed": False,
        })
        self._nudge_history[call_id] = history

        return True, None

    def _is_uuid(self, value: str) -> bool:
        """Check if a string is a valid UUID."""
        try:
            uuid.UUID(value)
            return True
        except ValueError:
            return False

    async def analyze_call(self, call_id: str) -> dict | None:
        """Generate nudge quality analysis for a call."""
        result = await self.db.execute(
            select(Nudge).where(Nudge.call_id == call_id)
        )
        nudges = result.scalars().all()
        if not nudges:
            return None

        delivered = [n for n in nudges if not n.suppressed]
        suppressed = [n for n in nudges if n.suppressed]

        # Latency calculations
        latencies = [n.latency_ms.get("total", 0) for n in nudges if n.latency_ms]
        latencies.sort()

        p50 = latencies[len(latencies) // 2] if latencies else 0
        p95_idx = int(len(latencies) * 0.95) if latencies else 0
        p95 = latencies[min(p95_idx, len(latencies) - 1)] if latencies else 0

        return {
            "call_id": call_id,
            "total_nudges": len(nudges),
            "delivered_nudges": len(delivered),
            "suppressed_nudges": len(suppressed),
            "suppression_breakdown": {},  # TODO: aggregate by reason
            "avg_confidence": sum(n.confidence for n in nudges) / len(nudges) if nudges else 0,
            "avg_latency_ms": {},
            "p50_latency_ms": p50,
            "p95_latency_ms": p95,
            "signal_type_breakdown": {},
            "false_positive_estimate": 0.0,
        }

    async def generate_latency_report(self) -> dict:
        """Generate aggregate latency report across all calls."""
        # TODO: Aggregate latency data across all nudges
        return {
            "total_calls_analyzed": 0,
            "total_nudges_generated": 0,
            "total_nudges_delivered": 0,
            "total_nudges_suppressed": 0,
            "component_latency": {},
            "end_to_end_latency": {"p50": 0, "p95": 0},
            "signal_type_accuracy": {},
        }
