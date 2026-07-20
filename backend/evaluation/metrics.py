"""
Evaluation Metrics Module

Provides metric calculation functions for:
- RAG retrieval quality (precision, recall, MRR)
- Nudge quality (precision, false positive rate)
- Latency (P50, P95, component breakdown)
"""

from app.utils.latency import calculate_p50_p95


def rag_precision_at_k(results: list[dict], k: int = 5) -> float:
    """Calculate precision@k for RAG retrieval results."""
    if not results:
        return 0.0
    relevant = sum(1 for r in results[:k] if r.get("verdict") == "correct")
    return relevant / min(k, len(results))


def nudge_precision(nudges: list[dict]) -> float:
    """Calculate nudge precision (delivered relevant / total delivered)."""
    delivered = [n for n in nudges if not n.get("suppressed")]
    if not delivered:
        return 0.0
    relevant = sum(1 for n in delivered if n.get("relevant", False))
    return relevant / len(delivered)


def nudge_false_positive_rate(nudges: list[dict]) -> float:
    """Calculate false positive rate for nudges."""
    delivered = [n for n in nudges if not n.get("suppressed")]
    if not delivered:
        return 0.0
    false_positives = sum(1 for n in delivered if not n.get("relevant", True))
    return false_positives / len(delivered)


def latency_report(latencies: list[dict]) -> dict:
    """Generate latency report from a list of latency measurements."""
    if not latencies:
        return {}

    components = {}
    for entry in latencies:
        for component, value in entry.items():
            if component not in components:
                components[component] = []
            components[component].append(value)

    report = {}
    for component, values in components.items():
        report[component] = calculate_p50_p95(values)

    return report
