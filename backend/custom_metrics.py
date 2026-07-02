from prometheus_client import Counter, Histogram, Summary

# ── API Metrics ───────────────────────────────────────────
REQUEST_COUNT = Counter(
    name="http_requests_total",
    documentation="Total number of HTTP requests handled by the API",
    labelnames=["method", "endpoint"],
)

REQUEST_DURATION = Histogram(
    name="http_request_duration_seconds",
    documentation="Duration of HTTP requests in seconds",
    labelnames=["method", "endpoint"],
)

REQUEST_ERRORS = Counter(
    name="http_request_errors_total",
    documentation="Count of failed HTTP requests by endpoint and error type",
    labelnames=["method", "endpoint", "error_type"],
)

RESPONSE_LATENCY = Summary(
    name="response_latency_seconds",
    documentation="Latency of prediction requests in seconds",
)

RESPONSE_STATUS = Counter(
    name="http_response_status_total",
    documentation="HTTP response status codes emitted by the API",
    labelnames=["method", "endpoint", "status_code"],
)

# ── Model Metrics ─────────────────────────────────────────
PREDICTION_COUNTER = Counter(
    name="predictions_total",
    documentation="Total predictions by sentiment label",
    labelnames=["sentiment"],
)

MODEL_INFERENCE_DURATION = Histogram(
    name="model_inference_duration_seconds",
    documentation="Duration of model inference in seconds",
)

# ── Input Metrics ─────────────────────────────────────────
TOKENS_COUNTER = Counter(
    name="input_tokens_total",
    documentation="Total number of tokens processed in prediction requests",
)

TOKEN_COUNT_HISTOGRAM = Histogram(
    name="input_token_count_histogram",
    documentation="Distribution of token counts per prediction request",
    buckets=[10, 25, 50, 100, 200, 500, 1000, float("inf")]
)

# Cache metrics
CACHE_HIT = Counter(
    name="cache_hits_total",
    documentation="Total number of cache hits",
    labelnames=["endpoint"],
)

CACHE_MISS = Counter(
    name="cache_misses_total",
    documentation="Total number of cache misses",
    labelnames=["endpoint"],
)

CACHE_WRITES = Counter(
    name="cache_writes_total",
    documentation="Total number of cache writes",
    labelnames=["endpoint"],
)
