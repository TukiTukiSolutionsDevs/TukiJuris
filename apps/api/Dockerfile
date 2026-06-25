FROM python:3.12-slim

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

# Application code
COPY . .

# Boot via the orchestrator: it waits for Postgres, applies Alembic migrations
# (stamping the legacy SQL baseline if needed), verifies the schema, then
# exec()s into uvicorn with the same flags as before.
#
# uvicorn flags rationale (preserved through the exec in scripts/bootstrap.py):
#
# --proxy-headers + --forwarded-allow-ips: the API sits behind the Next.js
# dev proxy (apps/web/next.config.ts rewrites /api/* to this service). Without
# these flags, FastAPI treats `Host: api:8000` (the internal container
# hostname) as authoritative. Any implicit redirect it emits — e.g. the
# auto-slash redirect when a route is defined as `/foo/` and hit as `/foo` —
# gets a Location header pointing at the backend's private URL. The browser
# then follows that cross-origin, drops the refresh cookie, and the request
# lands unauthenticated at 127.0.0.1:8000 → 401.
#
# With --proxy-headers enabled, uvicorn honours X-Forwarded-Host / -Proto /
# -For set by Next on every rewrite, so `request.url_for(...)` (and
# redirect Locations) use the public origin (http://localhost:3000) and
# stay same-origin with the browser.
#
# --forwarded-allow-ips="*" is correct for dev (any source trusted inside
# docker-compose); in production this should be narrowed to the reverse
# proxy's IP range.
CMD ["python", "scripts/bootstrap.py"]
