# TukiJuris JavaScript/TypeScript SDK

JavaScript and TypeScript client for the [TukiJuris](https://tukijuris.net.pe) Legal AI API — intelligent legal research powered by Peruvian law.

**Zero runtime dependencies.** Uses the native `fetch` API (Node.js 18+, browsers, Deno, Bun).

## Installation

```bash
npm install tukijuris
```

```bash
yarn add tukijuris
```

```bash
pnpm add tukijuris
```

## Quick Start

```typescript
import TukiJurisClient from "tukijuris";

const client = new TukiJurisClient("ak_your_key");

const result = await client.query(
  "Cuales son los requisitos para un despido justificado en Peru?"
);

console.log(result.answer);
result.citations.forEach((c) => {
  console.log(`${c.document} — ${c.article}`);
});
```

Get your API key at [tukijuris.net.pe/dashboard](https://tukijuris.net.pe/dashboard).

---

## TypeScript Types

All methods are fully typed. Key types exported from the package:

```typescript
import type {
  QueryResult,
  SearchResult,
  AnalyzeResult,
  AreaInfo,
  DocumentsResult,
  UsageResult,
  QueryOptions,
  SearchOptions,
  TukiJurisError,
} from "tukijuris";
```

---

## Methods

### `query(query, options?)`

Submit a legal question. Returns an AI-generated answer with citations.

```typescript
const result = await client.query(
  "Plazo de prescripcion para cobro de deudas civiles",
  { legalArea: "civil" }
);

console.log(result.answer);
console.log(result.area_detected);  // "civil"
console.log(result.latency_ms);     // e.g. 3412
```

**Options:**
| Name | Type | Description |
|------|------|-------------|
| `legalArea` | `string` | Area hint: `civil`, `penal`, `laboral`, `tributario`, `constitucional`, `administrativo`, `corporativo`, `registral`, `competencia`, `compliance`, `comercio_exterior` |
| `model` | `string` | LLM model override |

**Response:** `QueryResult` — `answer`, `citations`, `area_detected`, `agent_used`, `model_used`, `tokens_used`, `latency_ms`

---

### `search(query, options?)`

Search the legal knowledge base. Returns ranked document chunks.

```typescript
const { results, total } = await client.search(
  "articulo 34 CTS trabajadores",
  { area: "laboral", limit: 5 }
);

results.forEach((item) => {
  console.log(`[${item.score.toFixed(2)}] ${item.document} — ${item.article}`);
  console.log(`  ${item.content.slice(0, 120)}...`);
});
```

**Response:** `SearchResult` — `results[]`, `total`, `query`

Each result: `content`, `document`, `article`, `score`, `legal_area`

---

### `analyze(caseDescription, areas?)`

Analyze a legal case description.

```typescript
const result = await client.analyze(
  `Un trabajador fue despedido verbalmente despues de 5 anos de servicio.
   No recibio carta de despido ni liquidacion. Quiere demandar a la empresa.`,
  ["laboral"]
);

console.log(result.analysis);
console.log(result.areas_detected);  // ["laboral"]
```

**Response:** `AnalyzeResult` — `areas_detected`, `analysis`, `model_used`, `latency_ms`

---

### `areas()`

List all available legal areas.

```typescript
const areas = await client.areas();
areas.forEach((a) => console.log(`${a.id.padEnd(20)} ${a.name}`));
// civil                Derecho Civil
// penal                Derecho Penal
// laboral              Derecho Laboral
// tributario           Derecho Tributario
// ...
```

**Response:** `AreaInfo[]` — `id`, `name`, `chunks`

---

### `documents(options?)`

Browse the indexed document catalog.

```typescript
const { documents, total } = await client.documents({
  area: "tributario",
  limit: 10,
});

console.log(`Total: ${total}`);
documents.forEach((d) => {
  console.log(`${d.title} (${d.chunk_count} chunks)`);
});
```

**Response:** `DocumentsResult` — `documents[]`, `total`

---

### `usage()`

Get usage statistics for your API key.

```typescript
const stats = await client.usage();
console.log(`Today: ${stats.queries_today} queries`);
console.log(`This month: ${stats.queries_month} queries`);
console.log(`Rate limit: ${stats.limit_per_minute} req/min`);
```

**Response:** `UsageResult` — `queries_today`, `queries_month`, `limit_per_minute`, `key_name`

---

## Error Handling

All methods throw `TukiJurisError` on non-2xx responses.

```typescript
import TukiJurisClient, { TukiJurisError } from "tukijuris";

const client = new TukiJurisClient("ak_your_key");

try {
  const result = await client.query("Consulta legal...");
} catch (err) {
  if (err instanceof TukiJurisError) {
    console.error(`Status ${err.status}: ${err.detail}`);
    if (err.status === 429) {
      // rate limited — implement exponential backoff
    }
  } else {
    // network error, timeout, etc.
    throw err;
  }
}
```

Common status codes:
| Code | Meaning |
|------|---------|
| 401 | Invalid or missing API key |
| 403 | API key lacks required scope |
| 422 | Validation error (check request body) |
| 429 | Rate limit exceeded |
| 502 | AI processing error — retry with backoff |

---

## Local Development

Point the SDK at a local instance:

```typescript
const client = new TukiJurisClient(
  "ak_dev_key",
  "http://localhost:8000/api/v1"
);
```

---

## Browser / CDN Usage

```html
<script type="module">
  import TukiJurisClient from "https://esm.sh/tukijuris@0.1.0";

  const client = new TukiJurisClient("ak_your_key");
  const result = await client.areas();
  console.log(result);
</script>
```

---

## Examples

### Concurrent queries with Promise.all

```typescript
const [queryResult, searchResult, areaList] = await Promise.all([
  client.query("Derechos del consumidor en Peru"),
  client.search("ley 29571 codigo consumidor"),
  client.areas(),
]);
```

### React hook example

```typescript
import { useState, useEffect } from "react";
import TukiJurisClient from "tukijuris";

const client = new TukiJurisClient(process.env.NEXT_PUBLIC_TUKIJURIS_KEY!);

function useLegalAreas() {
  const [areas, setAreas] = useState([]);

  useEffect(() => {
    client.areas().then(setAreas).catch(console.error);
  }, []);

  return areas;
}
```

---

## License

MIT — see [LICENSE](LICENSE).
