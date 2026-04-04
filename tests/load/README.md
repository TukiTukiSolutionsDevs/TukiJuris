# Load Testing — TukiJuris

## Setup

```bash
pip install locust
```

## Run locally (with UI)

```bash
locust -f tests/load/locustfile.py --host=http://localhost:8000
# Open http://localhost:8089 in your browser
```

## Run headless (CI/CD)

```bash
locust -f tests/load/locustfile.py \
  --host=http://localhost:8000 \
  --headless \
  -u 50 \
  -r 5 \
  --run-time 2m \
  --html=tests/load/report.html
```

## Run against production

```bash
locust -f tests/load/locustfile.py --host=https://tukijuris.net.pe
```

## User mix

| Class | Weight | Description |
|---|---|---|
| `AnonymousUser` | 30% | No auth — only health checks and root |
| `AuthenticatedUser` | 70% | Registers on start, then exercises all main endpoints |

## Task distribution (AuthenticatedUser)

| Task | Weight | Endpoint |
|---|---|---|
| `legal_query` | 10 | `POST /api/chat/query` |
| `search_documents` | 5 | `GET /api/documents/search` |
| `list_areas` | 3 | `GET /api/v1/areas` |
| `v1_query` | 2 | `POST /api/v1/query` |
| `v1_search` | 2 | `POST /api/v1/search` |
| `feedback_stats` | 1 | `GET /api/feedback/stats` |
| `billing_plans` | 1 | `GET /api/billing/plans` |

## Target metrics

| Endpoint | p95 target |
|---|---|
| `/api/chat/query` | < 3 000 ms |
| `/api/documents/search` | < 500 ms |
| `/api/v1/query` | < 3 000 ms |
| `/api/v1/search` | < 500 ms |
| `/api/health` | < 100 ms |

| Concurrency | Max error rate |
|---|---|
| 50 users | 0% |
| 100 users | < 1% |

## Slow request logging

Any request that takes longer than **5 000 ms** is printed to stdout with the
`[SLOW]` prefix for easy grep during a run:

```
[SLOW] POST /api/chat/query: 6234ms
```
