"""Request middleware — global rate limiting, request timing, and security headers."""

import hashlib
import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.config import settings

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    # Paths that serve HTML with external resources (Swagger UI, ReDoc)
    _DOCS_PREFIXES = ("/docs", "/redoc", "/openapi")

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        # Prevent MIME-type sniffing and clickjacking
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Referrer policy — send origin only when crossing to HTTPS
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # CSP: permissive for /docs (Swagger UI needs CDN resources),
        # strict for all other API endpoints
        if any(request.url.path.startswith(p) for p in self._DOCS_PREFIXES):
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "img-src 'self' data: https://fastapi.tiangolo.com; "
                "font-src 'self' https://cdn.jsdelivr.net; "
                "frame-ancestors 'none'"
            )
        else:
            response.headers["Content-Security-Policy"] = (
                "default-src 'none'; frame-ancestors 'none'"
            )

        # HSTS only in production — avoids breaking localhost dev flows
        if not settings.app_debug:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )

        # Strip server identification header if present
        if "server" in response.headers:
            del response.headers["server"]

        # Disable access to sensitive browser APIs
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=()"
        )

        return response


# Paths that bypass rate limiting entirely
_EXEMPT_PREFIXES = ("/api/health", "/docs", "/redoc", "/openapi")

# Coarse per-token limit applied at the middleware layer.
# Fine-grained per-plan limits are enforced in the check_rate_limit dep.
_AUTHENTICATED_REQUESTS_PER_MINUTE = 60
_ANONYMOUS_REQUESTS_PER_MINUTE = 10
_WINDOW_SECONDS = 60


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Global sliding-window rate limiter applied to all API routes.

    Uses a two-tier strategy:
    - Authenticated (Bearer token present): keyed on a short hash of the token.
    - Anonymous: keyed on the client IP address.

    If Redis is down the request is allowed through (fail-open) to avoid
    an infrastructure outage taking down the API entirely.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        # Let health checks, docs, and OpenAPI spec through unconditionally
        for prefix in _EXEMPT_PREFIXES:
            if request.url.path.startswith(prefix):
                return await call_next(request)

        from app.core.rate_limiter import rate_limiter

        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            token_hash = hashlib.sha256(auth_header[7:].encode()).hexdigest()[:16]
            key = f"token:{token_hash}"
            max_requests = _AUTHENTICATED_REQUESTS_PER_MINUTE
        else:
            client_ip = request.client.host if request.client else "unknown"
            key = f"ip:{client_ip}"
            max_requests = _ANONYMOUS_REQUESTS_PER_MINUTE

        result: dict = {}
        try:
            result = await rate_limiter.check_rate_limit(key, max_requests, _WINDOW_SECONDS)
            if not result["allowed"]:
                retry_after = max(1, result["reset_at"] - int(time.time()))
                # Build CORS-aware 429 response so browsers don't silently block it
                headers = {
                    "X-RateLimit-Limit": str(result["limit"]),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(result["reset_at"]),
                    "Retry-After": str(retry_after),
                }
                origin = request.headers.get("origin", "")
                if origin and origin in settings.cors_origins:
                    headers["Access-Control-Allow-Origin"] = origin
                    headers["Access-Control-Allow-Credentials"] = "true"
                    headers["Vary"] = "Origin"
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Too many requests. Try again later.", "retry_after": retry_after},
                    headers=headers,
                )
        except Exception as exc:
            logger.warning("Rate limiter error (allowing request): %s", exc)

        start = time.time()
        response = await call_next(request)
        duration_ms = int((time.time() - start) * 1000)

        # Attach rate limit metadata to every response when available
        if result:
            response.headers["X-RateLimit-Limit"] = str(result.get("limit", max_requests))
            response.headers["X-RateLimit-Remaining"] = str(result.get("remaining", "?"))
            response.headers["X-RateLimit-Reset"] = str(result.get("reset_at", "?"))

        if duration_ms > 2000:
            logger.warning(
                "Slow request: %s %s (%dms)",
                request.method,
                request.url.path,
                duration_ms,
            )

        # Record metrics (in-memory, non-blocking)
        try:
            from app.core.monitoring import metrics
            metrics.record(request.url.path, response.status_code, float(duration_ms))
        except Exception:
            pass  # never let metrics recording break a response

        return response
