# TriggersAPI

A unified RESTful interface for event ingestion, persistence, and delivery — the foundation for event-driven automation at scale.

## Quick Start

```bash
git clone https://github.com/jpwilson/triggers-api.git
cd triggers-api
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn src.main:app --reload
```

Visit `http://localhost:8000` for the dashboard, or `http://localhost:8000/docs` for interactive API docs.

---

## Full Project Description

The TriggersAPI is a public, reliable, and developer-friendly way for any system to send events into an automation platform. It abstracts away low-level infrastructure (Kafka, SQS) behind a clean REST interface, handles delivery semantics with retry logic, and provides inbox-style retrieval for consumers.

**Core capabilities:**
- **Event Ingestion** — Accept POST requests from any external source with structured JSON payloads
- **Event Persistence** — Store events durably with metadata (ID, timestamp, status, payload)
- **Inbox Retrieval** — Pull-based access for consumers with cursor pagination and filtering
- **Push Delivery** — Deliver events to registered subscription endpoints with exponential backoff retry
- **Subscriptions & Filtering** — Subscribe to specific event types or sources
- **Monitoring** — Real-time stats on event counts, delivery rates, and system health

---

## Architecture

```
External Source → POST /api/v1/events → SQLite (persistence)
                                            ↓
                                    Background delivery
                                            ↓
                              Subscription endpoints (push)

Consumer → GET /api/v1/inbox → Pull undelivered events
         → POST /api/v1/inbox/ack → Acknowledge receipt
```

**Key decisions:**
- **FastAPI** for async request handling and auto-generated OpenAPI docs
- **SQLite with WAL mode** for lightweight durability (swappable to PostgreSQL for production)
- **Background tasks** for non-blocking push delivery after ingestion
- **Exponential backoff** retry (1s, 2s, 4s, 8s, 16s) for failed deliveries

---

## Technology Selection & Reasoning

| Technology | Used For | Why |
|------------|----------|-----|
| FastAPI | REST API framework | Async, auto OpenAPI docs, Pydantic validation, high performance |
| SQLite (WAL) | Event persistence | Zero-config, durable, perfect for prototype (easy to swap to Postgres) |
| Pydantic | Request/response validation | Type-safe, auto-documentation, FastAPI native |
| httpx | Push delivery HTTP client | Async, timeout support, modern Python HTTP |
| Tailwind CSS (CDN) | Frontend styling | Rapid UI development, matches provided design system |
| pytest | Testing | Industry standard, async support, coverage reporting |
| Ruff | Linting & formatting | Fast, replaces flake8+black+isort in one tool |

---

## API Endpoints

### Event Ingestion

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/events` | Ingest a new event |
| `GET` | `/api/v1/events` | List all events (filterable) |
| `GET` | `/api/v1/events/{id}` | Get specific event |
| `DELETE` | `/api/v1/events/{id}` | Delete an event |

### Inbox (Pull Delivery)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/inbox` | Get undelivered events (cursor pagination) |
| `POST` | `/api/v1/inbox/ack` | Acknowledge event receipt |

### Subscriptions (Push Delivery)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/subscriptions` | Create subscription |
| `GET` | `/api/v1/subscriptions` | List all subscriptions |
| `GET` | `/api/v1/subscriptions/{id}` | Get specific subscription |
| `PATCH` | `/api/v1/subscriptions/{id}` | Update subscription |
| `DELETE` | `/api/v1/subscriptions/{id}` | Delete subscription |
| `GET` | `/api/v1/subscriptions/{id}/deliveries` | Get delivery attempts |

### System

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/stats` | System-wide statistics |
| `GET` | `/health` | Health check |
| `GET` | `/docs` | Interactive Swagger UI |
| `GET` | `/redoc` | ReDoc documentation |

---

## Example Usage

### Ingest an event
```bash
curl -X POST http://localhost:8000/api/v1/events \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "order.created",
    "source": "shopify",
    "payload": {
      "order_id": "12345",
      "amount": 49.99,
      "currency": "USD"
    }
  }'
```

Response:
```json
{
  "status": "accepted",
  "event_id": "evt_a1b2c3d4e5f6",
  "received_at": "2024-01-15T10:30:00Z",
  "message": "Event ingested successfully"
}
```

### Poll inbox for undelivered events
```bash
curl http://localhost:8000/api/v1/inbox
```

### Acknowledge events
```bash
curl -X POST http://localhost:8000/api/v1/inbox/ack \
  -H "Content-Type: application/json" \
  -d '{"event_ids": ["evt_a1b2c3d4e5f6"]}'
```

### Create a push subscription
```bash
curl -X POST http://localhost:8000/api/v1/subscriptions \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Order Notifications",
    "endpoint_url": "https://api.example.com/webhooks/orders",
    "event_types": ["order.created", "order.updated"],
    "retry_enabled": true,
    "max_retries": 5
  }'
```

---

## Reliability Approach

### Delivery Guarantees: At-Least-Once

The TriggersAPI implements **at-least-once delivery** semantics:

1. **Events are persisted before acknowledgment** — No data loss on ingestion
2. **Push delivery retries with exponential backoff** — Failed deliveries retry up to 5 times (1s, 2s, 4s, 8s, 16s)
3. **Inbox provides pull-based access** — Consumers can always fetch undelivered events
4. **Acknowledgment flow** — Events stay in inbox until explicitly acknowledged

**Tradeoffs:**
- Consumers may receive duplicate events (idempotency recommended on consumer side)
- SQLite limits write throughput (~1000 writes/sec) — production would use PostgreSQL
- Background task delivery is in-process; a production system would use a dedicated worker queue

---

## Frontend Pages

| Page | URL | Description |
|------|-----|-------------|
| Dashboard | `/` | System overview with metrics, charts, recent events |
| Explorer | `/explorer` | Real-time event log with expandable payloads |
| API Reference | `/api-reference` | Interactive docs with "Try it out" panel |
| Subscriptions | `/subscriptions-page` | Subscription management with delivery stats |

---

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=term-missing --cov-fail-under=70

# Lint
ruff check .

# Format check
ruff format --check .
```

**41 tests** covering events, inbox, subscriptions, delivery, stats, and database operations.

---

## CI/CD Pipeline

GitHub Actions runs on every push/PR to main:
- Format check (ruff format)
- Lint (ruff check)
- Tests with coverage (pytest, 70% minimum)

---

## Deployment

### Docker
```bash
docker build -t triggers-api .
docker run -p 8000:8000 triggers-api
```

### Railway
```bash
railway up
```

The project includes `Dockerfile`, `Procfile`, and `railway.json` for one-click Railway deployment.

---

## Project Structure

```
├── src/
│   ├── main.py              # FastAPI app, routes, static file serving
│   ├── config.py             # Environment configuration
│   ├── database.py           # SQLite persistence layer
│   ├── delivery.py           # Push delivery with retry logic
│   ├── models.py             # Pydantic models (Event, Subscription, etc.)
│   └── routes/
│       ├── events.py         # POST/GET/DELETE /events
│       ├── inbox.py          # GET /inbox, POST /inbox/ack
│       └── subscriptions.py  # Subscription CRUD + delivery history
├── static/
│   ├── dashboard.html        # System overview dashboard
│   ├── explorer.html         # Real-time event explorer
│   ├── api_reference.html    # Interactive API documentation
│   └── subscriptions.html    # Subscription manager
├── tests/
│   ├── conftest.py           # Test fixtures
│   ├── test_events.py        # Event ingestion tests
│   ├── test_inbox.py         # Inbox & acknowledgment tests
│   ├── test_subscriptions.py # Subscription CRUD tests
│   ├── test_stats.py         # Stats & health check tests
│   └── test_database.py      # Database layer unit tests
├── .github/workflows/ci.yml  # GitHub Actions CI
├── Dockerfile                # Container deployment
├── Procfile                  # Railway/Heroku process file
├── railway.json              # Railway configuration
├── requirements.txt          # Production dependencies
├── requirements-dev.txt      # Development dependencies
├── pyproject.toml            # Project config (ruff, pytest, coverage)
└── .env.example              # Environment variable template
```

---

## Cost Estimates

| Scale | Hosting | Database | Total/mo |
|-------|---------|----------|----------|
| Prototype | $0 (local) | SQLite (free) | **$0** |
| 1,000 users | $5 (Railway) | SQLite/Postgres ($0-$25) | **$5-$30** |
| 10,000 users | $20 (Railway) | PostgreSQL ($25) | **$45** |

---

## Sub-Problems Explored

1. **Subscriptions and Filtering** — Consumers subscribe to specific event types and sources. Events are filtered at delivery time.
2. **Push Delivery with Retry** — Events are delivered to registered URLs with exponential backoff (up to 5 retries). Delivery attempts are logged.

---

*Built for the GauntletAI x Zapier Partner Challenge*
