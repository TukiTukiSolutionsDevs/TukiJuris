"""Monitoring, error tracking, and structured logging."""

import logging
import time
from contextlib import asynccontextmanager

from app.config import settings


def init_sentry() -> None:
    """Initialize Sentry error tracking (if DSN configured)."""
    if not settings.sentry_dsn:
        logging.getLogger(__name__).info("Sentry not configured (SENTRY_DSN empty)")
        return
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            environment=settings.app_env,
            release=f"agente-derecho@{settings.app_version}",
            traces_sample_rate=0.1 if settings.app_env == "production" else 1.0,
            profiles_sample_rate=0.1,
            integrations=[FastApiIntegration(), SqlalchemyIntegration()],
            send_default_pii=False,  # GDPR compliance
        )
        logging.getLogger(__name__).info(f"Sentry initialized ({settings.app_env})")
    except ImportError:
        logging.getLogger(__name__).warning("sentry-sdk not installed, skipping")


class RequestMetrics:
    """Track request metrics in memory (lightweight, no external deps)."""

    def __init__(self) -> None:
        self._requests: int = 0
        self._errors: int = 0
        self._total_latency_ms: float = 0.0
        self._slow_requests: int = 0  # >2s
        self._status_codes: dict[int, int] = {}
        self._endpoint_latency: dict[str, list[float]] = {}  # last 100 per endpoint

    def record(self, path: str, status_code: int, latency_ms: float) -> None:
        self._requests += 1
        self._total_latency_ms += latency_ms
        self._status_codes[status_code] = self._status_codes.get(status_code, 0) + 1
        if status_code >= 500:
            self._errors += 1
        if latency_ms > 2000:
            self._slow_requests += 1
        # Track per-endpoint (keep last 100)
        if path not in self._endpoint_latency:
            self._endpoint_latency[path] = []
        self._endpoint_latency[path].append(latency_ms)
        if len(self._endpoint_latency[path]) > 100:
            self._endpoint_latency[path] = self._endpoint_latency[path][-100:]

    def get_stats(self) -> dict:
        avg_latency = (
            self._total_latency_ms / self._requests if self._requests > 0 else 0
        )
        error_rate = (
            self._errors / self._requests * 100 if self._requests > 0 else 0
        )
        # Top 5 slowest endpoints
        slowest = sorted(
            [
                (k, sum(v) / len(v))
                for k, v in self._endpoint_latency.items()
                if v
            ],
            key=lambda x: x[1],
            reverse=True,
        )[:5]
        return {
            "total_requests": self._requests,
            "total_errors": self._errors,
            "error_rate_pct": round(error_rate, 2),
            "avg_latency_ms": round(avg_latency, 1),
            "slow_requests": self._slow_requests,
            "status_codes": dict(self._status_codes),
            "slowest_endpoints": [
                {"path": p, "avg_ms": round(ms, 1)} for p, ms in slowest
            ],
        }

    def reset(self) -> None:
        self.__init__()


metrics = RequestMetrics()
