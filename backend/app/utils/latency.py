"""
Latency Measurement Utilities (Q4)

Provides:
- LatencyTracker: Per-component latency tracking
- @measure_latency decorator for automatic timing
- P50/P95 calculation helpers
"""

import time
import functools
import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class LatencyTracker:
    """
    Track latency across pipeline components.
    
    Usage:
        tracker = LatencyTracker()
        with tracker.measure("asr"):
            result = await asr.transcribe(chunk)
        with tracker.measure("signal"):
            signals = await extractor.extract(transcript)
        
        report = tracker.get_report()
        # {"asr": 180.5, "signal": 95.2, "total": 275.7}
    """
    
    measurements: dict = field(default_factory=dict)
    _start_times: dict = field(default_factory=dict)
    
    class _MeasureContext:
        """Context manager for measuring a component."""
        def __init__(self, tracker, component_name):
            self.tracker = tracker
            self.component = component_name
            
        def __enter__(self):
            self.tracker._start_times[self.component] = time.time()
            return self
            
        def __exit__(self, *args):
            elapsed = (time.time() - self.tracker._start_times[self.component]) * 1000
            if self.component not in self.tracker.measurements:
                self.tracker.measurements[self.component] = []
            self.tracker.measurements[self.component].append(elapsed)
    
    def measure(self, component_name: str):
        """Create a context manager for measuring a component."""
        return self._MeasureContext(self, component_name)
    
    def get_report(self) -> dict:
        """Get the latest measurement for each component."""
        report = {}
        for component, times in self.measurements.items():
            report[component] = round(times[-1], 2) if times else 0
        report["total"] = round(sum(report.values()), 2)
        return report
    
    def get_all_measurements(self) -> dict:
        """Get all measurements for analysis."""
        return self.measurements


def calculate_percentile(values: list[float], percentile: float) -> float:
    """
    Calculate the Nth percentile of a list of values.
    
    Args:
        values: List of numeric values
        percentile: Percentile to calculate (0-100)
    
    Returns:
        The Nth percentile value
    """
    if not values:
        return 0.0
    
    sorted_values = sorted(values)
    idx = int(len(sorted_values) * percentile / 100)
    idx = min(idx, len(sorted_values) - 1)
    return round(sorted_values[idx], 2)


def calculate_p50_p95(values: list[float]) -> dict:
    """Calculate P50 and P95 for a list of values."""
    return {
        "p50": calculate_percentile(values, 50),
        "p95": calculate_percentile(values, 95),
        "min": round(min(values), 2) if values else 0,
        "max": round(max(values), 2) if values else 0,
        "avg": round(sum(values) / len(values), 2) if values else 0,
        "count": len(values),
    }


def measure_latency(component_name: str):
    """
    Decorator to measure function execution latency.
    
    Usage:
        @measure_latency("rag_search")
        async def search(query: str):
            ...
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            start = time.time()
            result = await func(*args, **kwargs)
            elapsed_ms = (time.time() - start) * 1000
            logger.debug(f"{component_name} latency: {elapsed_ms:.2f}ms")
            
            # Attach latency to result if it's a dict
            if isinstance(result, dict):
                result["_latency_ms"] = round(elapsed_ms, 2)
            
            return result
        return wrapper
    return decorator
