from prometheus_client import Counter, Histogram

URLS_CREATED = Counter(
    "url_shortener_urls_created_total",
    "Total number of URLs successfully shortened",
)

URL_REDIRECTS = Counter(
    "url_shortener_url_redirects_total",
    "Total number of URL redirection attempts",
    ["status"],
)

CACHE_HITS = Counter(
    "url_shortener_cache_hits_total",
    "Total number of cache hits in Redis for URL redirects",
)

CACHE_MISSES = Counter(
    "url_shortener_cache_misses_total",
    "Total number of cache misses in Redis requiring database lookup for URL redirects",
)

URL_LOOKUP_DURATION = Histogram(
    "url_shortener_url_lookup_duration_seconds",
    "Latency of resolving short URLS in seconds",
    buckets=[0.0005, 0.001, 0.0025, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
)