"""documents-search unit cluster — filter validator + query builder.

Spec IDs:
  documents-search.unit.001  test_search_filter_date_range_invalid
  documents-search.unit.002  test_search_filter_unknown_area_rejected
  documents-search.unit.003  test_search_pagination_offset_limit

Run:
  docker exec tukijuris-api-1 pytest tests/unit/test_search_filters.py -v
"""

from __future__ import annotations

import pytest
from fastapi import HTTPException

from app.api.routes.search import SearchFilters, _build_search_query, _validate_filters


class TestSearchFilterValidator:
    """T-E-06 — _validate_filters + _build_search_query unit tests."""

    async def test_search_filter_date_range_invalid(self) -> None:
        """documents-search.unit.001 — date_to before date_from → raises 422.

        Contract: _validate_filters must reject inverted date ranges to prevent
        queries that would always return zero results silently.
        """
        filters = SearchFilters(date_from="2024-06-01", date_to="2024-01-01")
        with pytest.raises(HTTPException) as exc_info:
            _validate_filters(filters)
        assert exc_info.value.status_code == 422, (
            f"Expected 422 for inverted date range, got {exc_info.value.status_code}"
        )

    async def test_search_filter_unknown_area_rejected(self) -> None:
        """documents-search.unit.002 — area='unknown' not in whitelist → raises 422.

        Contract: _validate_filters must reject any area not in _VALID_LEGAL_AREAS
        to prevent SQL injection via dynamic IN clauses.
        """
        filters = SearchFilters(areas=["unknown"])
        with pytest.raises(HTTPException) as exc_info:
            _validate_filters(filters)
        assert exc_info.value.status_code == 422, (
            f"Expected 422 for unknown area, got {exc_info.value.status_code}"
        )
        assert "unknown" in exc_info.value.detail, (
            f"Detail should name the invalid area, got: {exc_info.value.detail}"
        )

    async def test_search_pagination_offset_limit(self) -> None:
        """documents-search.unit.003 — page=3, per_page=10 → offset=20, limit=10 in params.

        Contract: _build_search_query must translate page/per_page into the correct
        OFFSET/LIMIT bind parameters. offset=(page-1)*per_page.
        """
        _, _, params = _build_search_query(
            query_text="arrendamiento",
            filters=None,
            sort="relevance",
            page=3,
            per_page=10,
        )
        assert params["limit"] == 10, (
            f"Expected limit=10, got {params['limit']}"
        )
        assert params["offset"] == 20, (
            f"Expected offset=20 for page=3/per_page=10, got {params['offset']}"
        )
