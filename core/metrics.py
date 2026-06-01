"""
Prometheus metrics.
Import and use these counters/histograms anywhere in the app.
They are exposed at GET /api/v1/health/metrics.
"""
from prometheus_client import Counter, Histogram, CollectorRegistry

REGISTRY = CollectorRegistry()

solve_requests_total = Counter(
    "mathbot_solve_requests_total",
    "Total solve requests",
    ["status", "problem_type"],
    registry=REGISTRY,
)

solve_latency_seconds = Histogram(
    "mathbot_solve_latency_seconds",
    "End-to-end solve request latency",
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0],
    registry=REGISTRY,
)

agent_confidence_score = Histogram(
    "mathbot_agent_confidence_score",
    "Confidence score of agent solutions",
    buckets=[0.1, 0.2, 0.5, 0.7, 0.8, 0.9, 0.95, 1.0],
    registry=REGISTRY,
)

cache_operations_total = Counter(
    "mathbot_cache_operations_total",
    "Cache hits and misses",
    ["result"],   # hit | miss
    registry=REGISTRY,
)

tool_calls_total = Counter(
    "mathbot_tool_calls_total",
    "Number of agent tool invocations",
    ["tool_name"],
    registry=REGISTRY,
)

ocr_requests_total = Counter(
    "mathbot_ocr_requests_total",
    "Total OCR extraction requests",
    ["status"],
    registry=REGISTRY,
)

ocr_confidence_score = Histogram(
    "mathbot_ocr_confidence_score",
    "Confidence score of OCR extractions",
    buckets=[0.1, 0.3, 0.5, 0.7, 0.85, 0.9, 0.95, 1.0],
    registry=REGISTRY,
)
