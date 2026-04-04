# TukiJuris Python SDK

Python client for the [TukiJuris](https://tukijuris.net.pe) Legal AI API — intelligent legal research powered by Peruvian law.

## Installation

```bash
pip install tukijuris
```

Requires Python 3.9+ and `httpx`.

## Quick Start

```python
from tukijuris import TukiJurisClient

with TukiJurisClient(api_key="ak_your_key") as client:
    result = client.query("Cuales son los requisitos para un despido justificado en Peru?")
    print(result["answer"])
    for citation in result["citations"]:
        print(f"  - {citation['document']}: {citation['article']}")
```

Get your API key at [tukijuris.net.pe/dashboard](https://tukijuris.net.pe/dashboard).

---

## Methods

### `query(query, legal_area=None, model=None)`

Submit a legal question. Returns an AI-generated answer with citations.

```python
result = client.query(
    "Plazo de prescripcion para cobro de deudas civiles",
    legal_area="civil",
)
print(result["answer"])
print(result["area_detected"])   # "civil"
print(result["latency_ms"])      # e.g. 3412
```

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| `query` | `str` | Legal question (3–2000 chars) |
| `legal_area` | `str \| None` | Area hint: `civil`, `penal`, `laboral`, `tributario`, `constitucional`, `administrativo`, `corporativo`, `registral`, `competencia`, `compliance`, `comercio_exterior` |
| `model` | `str \| None` | LLM model override |

**Response keys:** `answer`, `citations`, `area_detected`, `agent_used`, `model_used`, `tokens_used`, `latency_ms`

---

### `search(query, area=None, limit=10)`

Search the legal knowledge base. Returns ranked document chunks.

```python
results = client.search("articulo 34 CTS trabajadores", area="laboral", limit=5)
for item in results["results"]:
    print(f"[{item['score']:.2f}] {item['document']} — {item['article']}")
    print(f"  {item['content'][:120]}...")
```

**Response keys:** `results` (list), `total`, `query`

Each result: `content`, `document`, `article`, `score`, `legal_area`

---

### `analyze(case_description, areas=None)`

Analyze a legal case description. Returns a structured legal analysis.

```python
case = """
Un trabajador fue despedido verbalmente despues de 5 anos de servicio.
No se le entrego carta de despido ni liquidacion. Quiere saber si puede
demandar y en que plazos.
"""
analysis = client.analyze(case, areas=["laboral"])
print(analysis["analysis"])
print(analysis["areas_detected"])  # ["laboral"]
```

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| `case_description` | `str` | Case description (10–5000 chars) |
| `areas` | `list[str] \| None` | Limit analysis to these areas |

**Response keys:** `areas_detected`, `analysis`, `model_used`, `latency_ms`

---

### `areas()`

List all available legal areas.

```python
for area in client.areas():
    print(f"{area['id']:20} {area['name']}")
# civil                Derecho Civil
# penal                Derecho Penal
# laboral              Derecho Laboral
# ...
```

---

### `documents(area=None, limit=20, offset=0)`

Browse the indexed document catalog.

```python
docs = client.documents(area="tributario", limit=10)
print(f"Total: {docs['total']}")
for doc in docs["documents"]:
    print(f"  {doc['title']} ({doc['chunk_count']} chunks)")
```

---

### `usage()`

Get usage statistics for your API key.

```python
stats = client.usage()
print(f"Today: {stats['queries_today']} queries")
print(f"This month: {stats['queries_month']} queries")
print(f"Rate limit: {stats['limit_per_minute']} req/min")
```

---

## Async Usage

For async frameworks (FastAPI, aiohttp, etc.) use `TukiJurisAsyncClient`:

```python
import asyncio
from tukijuris import TukiJurisAsyncClient

async def main():
    async with TukiJurisAsyncClient(api_key="ak_your_key") as client:
        # Run multiple queries concurrently
        results = await asyncio.gather(
            client.query("Derechos del consumidor en Peru"),
            client.query("Contrato de arrendamiento requisitos"),
            client.search("codigo civil articulo 1764"),
        )
        for r in results:
            print(r)

asyncio.run(main())
```

The async client is a drop-in replacement — all methods are identical but prefixed with `await`.

---

## Error Handling

All methods raise `httpx.HTTPStatusError` on non-2xx responses.

```python
import httpx
from tukijuris import TukiJurisClient

with TukiJurisClient(api_key="ak_your_key") as client:
    try:
        result = client.query("mi consulta legal")
    except httpx.HTTPStatusError as e:
        print(f"API error {e.response.status_code}: {e.response.text}")
    except httpx.TimeoutException:
        print("Request timed out")
```

Common status codes:
| Code | Meaning |
|------|---------|
| 401 | Invalid or missing API key |
| 403 | API key lacks required scope |
| 422 | Validation error (check request body) |
| 429 | Rate limit exceeded |
| 502 | AI processing error (retry with backoff) |

---

## Local Development

Point the SDK at a local instance:

```python
client = TukiJurisClient(
    api_key="ak_dev_key",
    base_url="http://localhost:8000/api/v1",
)
```

---

## License

MIT — see [LICENSE](LICENSE).
