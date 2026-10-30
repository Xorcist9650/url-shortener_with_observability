# High-Performance URL Shortener with Observability & Caching

[CI Pipeline](https://www.google.com/search?q=https://github.com/Xorcist9650/url-shortener_with_observability/actions/workflows/ci.yml)
[](https://fastapi.tiangolo.com/)
[](https://www.postgresql.org/)
[](https://redis.io/)
[](https://prometheus.io/)
[](https://grafana.com/)
[](https://docs.docker.com/compose/)

A production-grade, highly scalable URL shortener service built with **FastAPI**, backed by **PostgreSQL** and an in-memory **Redis** cache-aside layer, fully instrumented with **Prometheus** metrics, and visualized via pre-provisioned **Grafana** dashboards. Packaged into a self-healing **Docker Compose** multi-container network with automated **GitHub Actions** continuous integration.

---

## Architecture

```text
       +-------------------------------------------------------------------------+
       |                               Docker Host                               |
       |                                                                         |
       |                   +--------------------+                                |
Client |                   |                    |  Cache Hit (<1ms)              |
------>|------------------>|  FastAPI Service   |----------------->+-----------+ |
       |                   |  (Port 8000)       |                  | Redis     | |
       |                   |                    |<-----------------+ (Port     | |
       |                   +---------+----------+  Cache Miss /    |  6379)    | |
       |                             |             Async Click Log +-----------+ |
       |                             |                                           |
       |                             | Fallback / Persistence                    |
       |                             v                                           |
       |                   +--------------------+                                |
       |                   |  PostgreSQL (DB)   |                                |
       |                   |  (Port 5432)       |                                |
       |                   +--------------------+                                |
       |                             |                                           |
       |                             | /metrics (Every 5s)                       |
       |                             v                                           |
       |                   +--------------------+         +--------------------+ |
       |                   |  Prometheus        |-------->|  Grafana           | |
       |                   |  (Port 9090)       |         |  (Port 3000)       | |
       |                   +--------------------+         +----------+---------+ |
       +-------------------------------------------------------------|-----------+
                                                                     v
                                                            Browser Dashboard
```

---

## Key Features

* **100% Collision-Free Design**: Short codes are generated using deterministic Base62 encoding mapped directly to PostgreSQL's sequence IDs, eliminating collision retry loops and race conditions.
* **Sub-Millisecond Redis Caching**: Implements the cache-aside pattern to serve frequent redirects directly from RAM in under 1ms, using asynchronous background tasks to record database click analytics.
* **Full-Stack Observability**: Tracks incoming request rates, error codes, database latency, and Redis cache hit ratios across p50, p90, and p95 percentiles.
* **Zero-Touch Dashboard Provisioning**: Automatically registers Prometheus datasources and dashboard JSON files into Grafana on startup with zero manual UI configuration.
* **Production Containerization**: Fully isolated Docker network with health checks, automatic restart policies, and persistent storage volumes.
* **Automated CI Pipeline**: GitHub Actions workflow verifies Python linting (`flake8`) and validates Docker Compose configurations on every push and pull request.

---

## Tech Stack & Services

| Service | Technology | Port | Purpose |
| :--- | :--- | :--- | :--- |
| **API Backend** | FastAPI / Uvicorn | `8000` | REST API for shortening, redirection, and telemetry |
| **Database** | PostgreSQL 16 Alpine | `5432` | Relational storage for URLs, short codes, and click logs |
| **Cache Layer** | Redis 7 Alpine | `6379` | In-memory key-value cache with LFU eviction |
| **Metrics Collector** | Prometheus v2.54.1 | `9090` | Time-series scraper collecting `/metrics` every 5 seconds |
| **Visualizer** | Grafana 11.2.0 | `3000` | Pre-built monitoring dashboards and performance alerts |

---

## Project Structure

```text
.
├── .github/
│   └── workflows/
│       └── ci.yml              # GitHub Actions CI pipeline
├── app/
│   ├── __init__.py
│   ├── config.py               # Pydantic environment configuration
│   ├── database.py             # SQLAlchemy engine & session management
│   ├── main.py                 # FastAPI endpoints & route controllers
│   ├── metrics.py              # Custom Prometheus metric declarations
│   ├── models.py               # PostgreSQL SQLAlchemy database schema
│   ├── schemas.py              # Pydantic request/response models
│   └── utils.py                # Base62 ID encoder & alias validator
├── monitoring/
│   ├── grafana/
│   │   ├── dashboards/
│   │   │   ├── dashboard.yml   # Grafana dashboard provider
│   │   │   └── url_shortener_dashboard.json # Pre-built dashboard panels
│   │   └── datasources/
│   │       └── datasource.yml  # Prometheus datasource auto-provisioner
│   └── prometheus/
│       └── prometheus.yml      # Scrape configuration for FastAPI
├── .dockerignore
├── .env.example                # Template for environment configuration
├── .gitignore                  # Prevents committing secrets and caches
├── docker-compose.yml          # Multi-container orchestration definition
├── Dockerfile                  # Lightweight Python 3.11-slim container
└── requirements.txt            # Python dependencies
```

---

## Quick Start & Running the Project

### Prerequisites
* [Docker Desktop](https://www.docker.com/products/docker-desktop/) (ensure WSL 2 backend is enabled on Windows)
* [Git](https://git-scm.com/)

### 1. Clone the Repository
```bash
git clone https://github.com/Xorcist9650/url-shortener_with_observability.git
cd url-shortener_with_observability
```

### 2. Configure Environment Variables
Copy the template configuration to create your local `.env` file:

```bash
# On Linux / macOS
cp .env.example .env

# On Windows PowerShell
Copy-Item .env.example .env
```

Ensure your `.env` contains your desired credentials:
```env
POSTGRES_USER=xorcist9650
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=url_shortener_db
POSTGRES_HOST=db
POSTGRES_PORT=5432

REDIS_HOST=redis
REDIS_PORT=6379
REDIS_CACHE_TTL_SECONDS=86400

APP_PORT=8000
BASE_URL=http://localhost:8000
```

### 3. Launch the Multi-Container Stack
Start all five services in detached mode:

```bash
docker compose up -d --build
```

### 4. Verify Service Health
Check that all containers are `Up (healthy)`:
```bash
docker compose ps
```

---

## Service Dashboards & Endpoints

| Resource | URL | Credentials / Notes |
| :--- | :--- | :--- |
| **FastAPI Swagger UI** | [http://localhost:8000/docs](http://localhost:8000/docs) | Interactive API exploration |
| **FastAPI ReDoc** | [http://localhost:8000/redoc](http://localhost:8000/redoc) | Alternative API documentation |
| **System Health Check** | [http://localhost:8000/health](http://localhost:8000/health) | Reports DB and Redis connectivity |
| **Prometheus Web UI** | [http://localhost:9090](http://localhost:9090) | PromQL query editor and targets |
| **Grafana Dashboard** | [http://localhost:3000](http://localhost:3000) | **User:** `admin` \| **Pass:** `admin` |

---

## API Reference & Usage Examples

### 1. Check API & Database Health
```bash
curl -X GET http://localhost:8000/health
```
**Response (200 OK):**
```json
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected"
}
```

### 2. Shorten a URL (Auto-Generated Slug)
```bash
curl -X POST http://localhost:8000/shorten \
  -H "Content-Type: application/json" \
  -d '{"url": "https://fastapi.tiangolo.com/"}'
```
**Response (201 Created):**
```json
{
  "short_code": "4c93",
  "short_url": "http://localhost:8000/4c93",
  "original_url": "https://fastapi.tiangolo.com/",
  "created_at": "2026-10-30T06:20:00"
}
```

### 3. Shorten with a Custom Alias
```bash
curl -X POST http://localhost:8000/shorten \
  -H "Content-Type: application/json" \
  -d '{"url": "https://redis.io/docs/", "custom_alias": "redis-docs"}'
```
**Response (201 Created):**
```json
{
  "short_code": "redis-docs",
  "short_url": "http://localhost:8000/redis-docs",
  "original_url": "https://redis.io/docs/",
  "created_at": "2026-10-30T06:21:00"
}
```

### 4. Visit Short URL (HTTP 307 Redirect)
```bash
curl -i http://localhost:8000/4c93
```
**Response Headers:**
```http
HTTP/1.1 307 Temporary Redirect
location: https://fastapi.tiangolo.com/
```

### 5. Inspect Click Analytics
```bash
curl -X GET http://localhost:8000/analytics/4c93
```
**Response (200 OK):**
```json
{
  "short_code": "4c93",
  "original_url": "https://fastapi.tiangolo.com/",
  "clicks": 42,
  "created_at": "2026-10-30T06:20:00"
}
```

---

## Observability & Metrics

Prometheus automatically scrapes the `/metrics` endpoint every 5 seconds.

### Key Metrics Tracked
* `http_requests_total`: Total count of HTTP requests segmented by `status` (2xx, 3xx, 4xx, 5xx) and `handler`.
* `http_request_duration_seconds_bucket`: Latency histogram for HTTP requests by status code.
* `url_shortener_urls_created_total`: Total number of URLs successfully shortened.
* `url_shortener_redirects_total`: Redirection outcomes labeled by `status="success"` or `status="not_found"`.
* `url_shortener_cache_hits_total`: Total redirects served from Redis RAM.
* `url_shortener_cache_misses_total`: Total redirects requiring PostgreSQL lookups.

### Grafana Dashboard Panels
Open [http://localhost:3000](http://localhost:3000) > **Dashboards** > **URL Shortener Observability Dashboard**:
1. **Total URLs Shortened**: All-time count of generated short links.
2. **Cache Hits vs. Cache Misses**: Real-time ratio of Redis hits versus database fallbacks.
3. **Cache Hit Ratio (%)**: Gauge calculating $\frac{\text{Hits}}{\text{Hits} + \text{Misses}} \times 100$.
4. **HTTP Request Rate (req/s)**: Traffic volume broken down by status code (2xx, 3xx, 4xx, 5xx).
5. **Latency Percentiles**: Live time-series charts displaying **p50 (Median)**, **p90**, and **p95** request latencies.

---

## Stopping and Cleaning Up

To stop all running services:
```bash
docker compose down
```

To stop containers and reset database / cache storage volumes:
```bash
docker compose down -v
```

---

## License

Distributed under the MIT License. See `LICENSE` for more information.
