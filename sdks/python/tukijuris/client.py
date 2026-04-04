"""TukiJuris API Client — synchronous version."""

from typing import Any

import httpx


class TukiJurisClient:
    """Client for the TukiJuris Legal AI API.

    Usage:
        client = TukiJurisClient(api_key="ak_your_key")
        result = client.query("Requisitos para despido justificado")
        print(result["answer"])

    Context manager:
        with TukiJurisClient(api_key="ak_your_key") as client:
            result = client.query("Plazo de prescripcion en contratos civiles")
    """

    DEFAULT_BASE_URL = "https://tukijuris.net.pe/api/v1"

    def __init__(
        self,
        api_key: str,
        base_url: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        """
        Args:
            api_key: Your TukiJuris API key (starts with ak_).
            base_url: Override the API base URL. Useful for local development.
            timeout: Request timeout in seconds. Default 30.
        """
        self.api_key = api_key
        self.base_url = (base_url or self.DEFAULT_BASE_URL).rstrip("/")
        self._client = httpx.Client(
            base_url=self.base_url,
            headers={
                "X-API-Key": api_key,
                "Content-Type": "application/json",
            },
            timeout=timeout,
        )

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    def query(
        self,
        query: str,
        legal_area: str | None = None,
        model: str | None = None,
    ) -> dict[str, Any]:
        """Submit a legal query.

        The system classifies the question by area of Peruvian law, retrieves
        relevant context from the knowledge base (BM25 + semantic), and returns
        an AI-generated answer with citations to the original legal texts.

        Args:
            query: The legal question (3–2000 characters).
            legal_area: Optional area hint — e.g. "laboral", "penal", "civil".
                        Pass None to let the model auto-detect.
            model: LLM model override. Pass None to use the default.

        Returns:
            dict with keys: answer, citations, area_detected, agent_used,
                            model_used, tokens_used, latency_ms.

        Raises:
            httpx.HTTPStatusError: On non-2xx responses.
        """
        payload: dict[str, Any] = {"query": query}
        if legal_area:
            payload["legal_area"] = legal_area
        if model:
            payload["model"] = model
        res = self._client.post("/query", json=payload)
        res.raise_for_status()
        return res.json()

    def search(
        self,
        query: str,
        area: str | None = None,
        limit: int = 10,
    ) -> dict[str, Any]:
        """Search the legal knowledge base.

        Performs hybrid BM25 + semantic search and returns ranked document
        chunks with relevance scores. Use this when you need raw search
        results rather than a generated answer.

        Args:
            query: Search query (2–500 characters).
            area: Filter results to a specific legal area (e.g. "tributario").
            limit: Maximum number of results (1–50). Default 10.

        Returns:
            dict with keys: results (list), total, query.

        Raises:
            httpx.HTTPStatusError: On non-2xx responses.
        """
        payload: dict[str, Any] = {"query": query, "limit": limit}
        if area:
            payload["area"] = area
        res = self._client.post("/search", json=payload)
        res.raise_for_status()
        return res.json()

    def analyze(
        self,
        case_description: str,
        areas: list[str] | None = None,
    ) -> dict[str, Any]:
        """Analyze a legal case.

        Retrieves applicable regulations from the knowledge base and produces
        a structured analysis covering: areas of law, applicable regulations,
        rights and obligations, legal courses of action, deadlines, and a
        general recommendation.

        Args:
            case_description: Description of the case (10–5000 characters).
                              More detail produces better analysis.
            areas: Limit analysis to specific areas (e.g. ["laboral", "civil"]).
                   Pass None to detect areas automatically.

        Returns:
            dict with keys: areas_detected, analysis, model_used, latency_ms.

        Raises:
            httpx.HTTPStatusError: On non-2xx responses.
        """
        payload: dict[str, Any] = {"case_description": case_description}
        if areas:
            payload["areas"] = areas
        res = self._client.post("/analyze", json=payload)
        res.raise_for_status()
        return res.json()

    def areas(self) -> list[dict[str, Any]]:
        """List available legal areas.

        Returns all 11 areas of Peruvian law in the knowledge base.
        Use the `id` value as the `legal_area` parameter in query() and search().

        Returns:
            List of dicts with keys: id, name, chunks.

        Raises:
            httpx.HTTPStatusError: On non-2xx responses.
        """
        res = self._client.get("/areas")
        res.raise_for_status()
        return res.json().get("areas", [])

    def documents(
        self,
        area: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> dict[str, Any]:
        """List documents in the knowledge base.

        Browse the catalog of indexed legal documents with metadata
        including title, document number, legal area, and chunk count.

        Args:
            area: Filter by legal area. Pass None to list all areas.
            limit: Maximum number of results (1–100). Default 20.
            offset: Pagination offset. Default 0.

        Returns:
            dict with keys: documents (list), total.

        Raises:
            httpx.HTTPStatusError: On non-2xx responses.
        """
        params: dict[str, str] = {"limit": str(limit), "offset": str(offset)}
        if area:
            params["area"] = area
        res = self._client.get("/documents", params=params)
        res.raise_for_status()
        return res.json()

    def usage(self) -> dict[str, Any]:
        """Get API key usage statistics.

        Returns usage counters for the API key used in the request.
        Includes query counts for today and the current month, and the
        rate limit configured for the key.

        Returns:
            dict with keys: queries_today, queries_month,
                            limit_per_minute, key_name.

        Raises:
            httpx.HTTPStatusError: On non-2xx responses.
        """
        res = self._client.get("/usage")
        res.raise_for_status()
        return res.json()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def close(self) -> None:
        """Close the underlying HTTP connection pool."""
        self._client.close()

    def __enter__(self) -> "TukiJurisClient":
        return self

    def __exit__(self, *args: object) -> None:
        self.close()
