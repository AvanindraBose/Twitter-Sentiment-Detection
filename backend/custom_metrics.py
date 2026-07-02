from prometheus_client import Summary,Counter

# define the metrics
RESPONSE_LATENCY = Summary(name="response_latency_seconds",
                  documentation="Latency of prediction requests in seconds")

TOKENS_COUNTER = Counter(name="input_tokens_total",
                  documentation="Total number of tokens processed in prediction requests")

HAPPY_COUNTER = Counter(name="happy_predictions_total",
                  documentation="Total number of happy predictions made")

SAD_COUNTER = Counter(name="sad_predictions_total",
                  documentation="Total number of sad predictions made")