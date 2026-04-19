"""Pydantic schema for HTTP 429 quota-exceeded responses.

Shape matches spec §4 contract exactly:
    {
        "code": "quota_exceeded",
        "plan": "free",
        "used": 10,
        "limit": 10,
        "reset_at": "2026-04-20T00:00:00Z",
        "upgrade_url": "/planes"
    }
"""

from datetime import datetime

from pydantic import BaseModel, Field


class QuotaExceededDetail(BaseModel):
    """Body of HTTPException.detail when the daily quota is exceeded."""

    code: str = Field(default="quota_exceeded", frozen=True)
    plan: str
    used: int
    limit: int
    reset_at: datetime  # timezone-aware UTC; serializes as ISO 8601
    upgrade_url: str | None = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "code": "quota_exceeded",
                "plan": "free",
                "used": 10,
                "limit": 10,
                "reset_at": "2026-04-20T00:00:00Z",
                "upgrade_url": "/planes",
            }
        }
    }
