# Codex Proxy

OpenAI-compatible HTTP shim that routes `/v1/chat/completions` requests to
the user's authenticated `codex` CLI session.

**Development only.** Each request invokes `codex exec` fresh — slow and
wasteful in tokens. Swap for a real OpenAI key before going live.

## Run

```bash
cd services/codex_proxy
python3 -m venv .venv
source .venv/bin/activate
pip install fastapi uvicorn pydantic
python main.py
# → http://localhost:5050
```

Or one-shot with the system python:

```bash
pip install --user fastapi uvicorn pydantic
python3 services/codex_proxy/main.py
```

### Env vars

| Var | Default | Purpose |
|---|---|---|
| `CODEX_PROXY_HOST` | `0.0.0.0` | listen address |
| `CODEX_PROXY_PORT` | `5050` | listen port |
| `CODEX_PROXY_MODEL` | `gpt-5.4` | model name reported to clients |
| `CODEX_PROXY_TIMEOUT` | `300` | seconds per request |
| `CODEX_PROXY_CWD` | `$HOME` | cwd for `codex exec` (must be trusted in config.toml) |

## Connect TukiJuris to the proxy

The Docker API container reaches the host at `host.docker.internal`.

1. Add a dummy OpenAI key to the platform (any string ≥4 chars works):

```bash
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@tukijuris.com","password":"Admin123!Tuki"}' \
  | python3 -c "import json,sys; print(json.load(sys.stdin)['access_token'])")

curl -s -X POST http://localhost:8000/api/admin/platform-keys/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"provider":"openai","api_key":"codex-proxy-dummy","label":"Codex proxy (dev)"}'
```

2. Point the API at the proxy by adding to `.env`:

```
OPENAI_BASE_URL=http://host.docker.internal:5050/v1
OPENAI_API_KEY=codex-proxy-dummy
```

3. Restart the API container so litellm picks up the base URL:

```bash
docker compose restart api
```

## Smoke test

```bash
# Health
curl -s http://localhost:5050/health | jq

# Chat completion
curl -s -X POST http://localhost:5050/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-5.4",
    "messages": [{"role":"user","content":"Di hola en una palabra"}]
  }' | jq
```

## Why not embeddings?

Codex CLI doesn't expose embedding endpoints — it's an agent runtime, not
a model server. For embeddings (RAG), get a free Google AI key
(https://aistudio.google.com/apikey, 768-dim Gemini embeddings, free tier)
and add it via `/admin?tab=claves`.
