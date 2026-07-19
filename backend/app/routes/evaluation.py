"""
Evaluation Routes (Assessment Deliverable)

Endpoints for running and viewing evaluation results:
- POST /run — Run evaluation suite (RAG, voice, nudge, multilingual)
- GET /results — List evaluation results
- GET /results/{eval_type} — Get results for a specific eval type
"""

import json
import logging
import os
import time
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.rag_service import RAGService

logger = logging.getLogger(__name__)
router = APIRouter()

# Path to test cases
TEST_CASES_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
    "evaluation", "test_cases",
)


@router.post("/run")
async def run_evaluation(
    eval_type: str = Query(
        "all", description="all | rag_retrieval | voice_flow | nudge_quality | latency"
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    Run evaluation suite.
    
    Eval types:
    - rag_retrieval: 5+ test queries against KB with verdicts
    - voice_flow: Test call scenario validation
    - nudge_quality: False positive analysis
    - latency: P50/P95 latency measurements
    - all: Run all evaluations
    """
    results = {}

    if eval_type in ("all", "rag_retrieval"):
        results["rag_retrieval"] = await _run_rag_retrieval(db)

    if eval_type in ("all", "nudge_quality"):
        results["nudge_quality"] = await _run_nudge_quality(db)

    if eval_type in ("all", "voice_flow"):
        results["voice_flow"] = _load_voice_scenarios()

    if eval_type in ("all", "latency"):
        results["latency"] = {"status": "requires_audio_file", "message": "Run `make simulate` with test audio to generate latency data."}

    return {"eval_type": eval_type, "results": results}


@router.get("/results")
async def list_results(
    eval_type: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """List evaluation results with optional type filter."""
    # Load results from saved files if available
    results_dir = os.path.join(
        os.path.dirname(TEST_CASES_DIR), "results"
    )
    available = []
    if os.path.exists(results_dir):
        for f in os.listdir(results_dir):
            if f.endswith(".json") and (eval_type is None or eval_type in f):
                available.append(f)
    return {"available_results": available, "total": len(available)}


@router.get("/results/{eval_type}")
async def get_results_by_type(
    eval_type: str,
    db: AsyncSession = Depends(get_db),
):
    """Get detailed evaluation results for a specific type."""
    results_file = os.path.join(
        os.path.dirname(TEST_CASES_DIR), "results", f"{eval_type}.json"
    )
    if os.path.exists(results_file):
        with open(results_file, "r") as f:
            return json.load(f)
    return {"eval_type": eval_type, "results": [], "summary": {}, "status": "not_run"}


# --- Internal evaluation runners ---

async def _run_rag_retrieval(db: AsyncSession) -> dict:
    """
    Q2 Evaluation: RAG Retrieval Test
    
    Runs 7 predefined queries, evaluates results against expected keywords,
    generates verdicts (correct | partially_correct | incorrect).
    """
    test_cases_path = os.path.join(TEST_CASES_DIR, "rag_retrieval.json")
    if not os.path.exists(test_cases_path):
        return {"error": "Test cases file not found", "path": test_cases_path}

    with open(test_cases_path, "r") as f:
        test_cases = json.load(f)

    rag = RAGService(db)
    results = []
    verdicts = {"correct": 0, "partially_correct": 0, "incorrect": 0, "error": 0}
    total_retrieval_time = 0

    for tc in test_cases:
        try:
            start = time.time()
            search_result = await rag.search(
                query=tc["query"],
                category=tc.get("expected_category"),
                top_k=3,
            )
            elapsed_ms = (time.time() - start) * 1000
            total_retrieval_time += elapsed_ms

            # Evaluate: check if expected keywords appear in results
            result_text = " ".join(
                r.get("content", "") + " " + r.get("title", "")
                for r in search_result.get("results", [])
            ).lower()

            expected_keywords = tc.get("expected_keywords", [])
            matched = [kw for kw in expected_keywords if kw.lower() in result_text]
            match_ratio = len(matched) / len(expected_keywords) if expected_keywords else 0

            # Determine verdict
            if match_ratio >= 0.6:
                verdict = "correct"
            elif match_ratio >= 0.3:
                verdict = "partially_correct"
            else:
                verdict = "incorrect"

            verdicts[verdict] += 1

            top_result = search_result["results"][0] if search_result.get("results") else None

            results.append({
                "test_id": tc["test_id"],
                "query": tc["query"],
                "description": tc.get("description", ""),
                "expected_category": tc.get("expected_category"),
                "expected_keywords": expected_keywords,
                "matched_keywords": matched,
                "match_ratio": round(match_ratio, 2),
                "verdict": verdict,
                "top_result": {
                    "record_id": top_result["record_id"] if top_result else None,
                    "title": top_result["title"] if top_result else None,
                    "relevance_score": top_result["relevance_score"] if top_result else None,
                    "source": top_result["source"] if top_result else None,
                    "content_preview": top_result["content"][:200] if top_result else None,
                } if top_result else None,
                "total_results": search_result.get("total", 0),
                "retrieval_time_ms": round(elapsed_ms, 2),
            })

        except Exception as e:
            verdicts["error"] += 1
            results.append({
                "test_id": tc["test_id"],
                "query": tc["query"],
                "verdict": "error",
                "error": str(e),
            })

    total_tests = len(test_cases)
    accuracy = verdicts["correct"] / total_tests if total_tests else 0

    summary = {
        "total_tests": total_tests,
        "verdicts": verdicts,
        "accuracy": round(accuracy, 2),
        "partial_or_better": round(
            (verdicts["correct"] + verdicts["partially_correct"]) / total_tests, 2
        ) if total_tests else 0,
        "avg_retrieval_time_ms": round(total_retrieval_time / total_tests, 2) if total_tests else 0,
    }

    # Save results to file
    output = {"summary": summary, "results": results}
    _save_results("rag_retrieval", output)

    return output


async def _run_nudge_quality(db: AsyncSession) -> dict:
    """
    Q4 Evaluation: Nudge quality test using transcript scenarios.
    
    Runs signal extraction on predefined transcript segments,
    checks if expected signals are detected, measures false positives.
    """
    test_cases_path = os.path.join(TEST_CASES_DIR, "nudge_scenarios.json")
    if not os.path.exists(test_cases_path):
        return {"error": "Test cases file not found"}

    with open(test_cases_path, "r") as f:
        test_cases = json.load(f)

    from app.services.signal_extractor import SignalExtractor
    extractor = SignalExtractor()

    results = []
    true_positives = 0
    false_positives = 0
    false_negatives = 0
    true_negatives = 0

    for tc in test_cases:
        try:
            start = time.time()
            signals = await extractor.extract(
                transcript=tc["transcript_segment"],
                new_segment=tc["transcript_segment"],
            )
            elapsed_ms = (time.time() - start) * 1000

            expected_signal = tc.get("expected_signal")
            detected_types = [s.get("type") for s in signals]

            if expected_signal is None:
                # Should detect NO signals (negative case)
                if not signals:
                    verdict = "true_negative"
                    true_negatives += 1
                else:
                    verdict = "false_positive"
                    false_positives += 1
            else:
                # Should detect the expected signal
                if expected_signal in detected_types:
                    verdict = "true_positive"
                    true_positives += 1
                else:
                    verdict = "false_negative"
                    false_negatives += 1

            results.append({
                "test_id": tc["test_id"],
                "scenario": tc["scenario"],
                "expected_signal": expected_signal,
                "detected_signals": signals,
                "verdict": verdict,
                "latency_ms": round(elapsed_ms, 2),
            })

        except Exception as e:
            results.append({
                "test_id": tc["test_id"],
                "scenario": tc["scenario"],
                "verdict": "error",
                "error": str(e),
            })

    total = true_positives + false_positives + false_negatives + true_negatives
    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) else 0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) else 0

    summary = {
        "total_tests": len(test_cases),
        "true_positives": true_positives,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
        "true_negatives": true_negatives,
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1_score": round(f1, 3),
        "false_positive_rate": round(false_positives / total, 3) if total else 0,
    }

    output = {"summary": summary, "results": results}
    _save_results("nudge_quality", output)
    return output


def _load_voice_scenarios() -> dict:
    """Load voice test scenarios as evaluation reference."""
    test_cases_path = os.path.join(TEST_CASES_DIR, "voice_scenarios.json")
    if not os.path.exists(test_cases_path):
        return {"error": "Test cases file not found"}

    with open(test_cases_path, "r") as f:
        scenarios = json.load(f)

    return {
        "total_scenarios": len(scenarios),
        "scenarios": scenarios,
        "note": "Voice scenarios require live Vapi call testing. Use /api/voice/outbound-call to trigger test calls.",
    }


def _save_results(eval_type: str, data: dict):
    """Save evaluation results to file."""
    results_dir = os.path.join(os.path.dirname(TEST_CASES_DIR), "results")
    os.makedirs(results_dir, exist_ok=True)
    filepath = os.path.join(results_dir, f"{eval_type}.json")
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2, default=str)
    logger.info(f"Saved {eval_type} results to {filepath}")
