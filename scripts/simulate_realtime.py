"""
Real-Time Call Simulator (Q4)

Replays a recorded audio file at real-time speed through the
nudge pipeline to demonstrate live analysis capabilities.

Usage:
    python -m scripts.simulate_realtime --audio data/test_audio/call_01.wav
"""

import asyncio
import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def main():
    parser = argparse.ArgumentParser(description="Simulate real-time call for nudge testing")
    parser.add_argument("--audio", required=True, help="Path to audio file")
    parser.add_argument("--call-id", default="sim-001", help="Call ID for the simulation")
    parser.add_argument("--chunk-ms", type=int, default=250, help="Audio chunk size in ms")
    args = parser.parse_args()

    from app.core.database import init_db, async_session_factory
    from app.core.redis import init_redis
    from app.services.nudge_engine import NudgeEngine

    # Initialize
    await init_db()
    await init_redis()

    print(f"Starting real-time simulation:")
    print(f"  Audio: {args.audio}")
    print(f"  Call ID: {args.call_id}")
    print(f"  Chunk size: {args.chunk_ms}ms")
    print()

    async with async_session_factory() as session:
        engine = NudgeEngine(session)
        session_id = await engine.start_session(
            call_id=args.call_id,
            audio_source=args.audio,
            chunk_ms=args.chunk_ms,
        )
        print(f"Session started: {session_id}")
        
        # Wait for processing to complete
        task = engine._active_sessions.get(args.call_id)
        if task:
            await task
        
        # Generate analysis
        analysis = await engine.analyze_call(args.call_id)
        if analysis:
            print(f"\n=== Nudge Analysis ===")
            print(f"Total nudges: {analysis['total_nudges']}")
            print(f"Delivered: {analysis['delivered_nudges']}")
            print(f"Suppressed: {analysis['suppressed_nudges']}")
            print(f"P50 latency: {analysis['p50_latency_ms']}ms")
            print(f"P95 latency: {analysis['p95_latency_ms']}ms")

        await session.commit()


if __name__ == "__main__":
    asyncio.run(main())
