"""
Reranker Service — cross-encoder scoring for RAG result refinement.

Uses a lightweight approach: LLM scoring via litellm/google-generativeai
as primary strategy, with a manual TF-IDF cross-scoring fallback that
requires zero external dependencies beyond the Python standard library.

Reranking strategy (in order of preference):
  1. LLM reranking via litellm (gemini-2.0-flash) — single API call,
     scores all candidates in one prompt, fast and accurate.
  2. LLM reranking via google-generativeai directly — fallback if
     litellm is not installed.
  3. TF-IDF cross-scoring — pure stdlib, deterministic, <100ms,
     no API calls required.
"""

import asyncio
import json
import logging
import math
import re
import time
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)

# Spanish stopwords — covers the most frequent noise terms
_STOPWORDS = frozenset(
    {
        "a", "al", "ante", "bajo", "cabe", "con", "contra", "de", "desde",
        "durante", "en", "entre", "hacia", "hasta", "mediante", "para", "por",
        "pro", "segun", "sin", "so", "sobre", "tras", "versus", "via",
        "el", "la", "los", "las", "un", "una", "unos", "unas",
        "y", "e", "ni", "o", "u", "pero", "mas", "aunque", "sino", "si",
        "que", "cual", "quien", "cuyo", "cuya", "donde", "cuando", "como",
        "este", "esta", "estos", "estas", "ese", "esa", "esos", "esas",
        "aquel", "aquella", "aquellos", "aquellas",
        "me", "te", "se", "nos", "le", "les", "lo", "les",
        "es", "son", "fue", "eran", "ser", "estar", "ha", "han", "hay",
        "del", "no", "se", "su", "sus", "yo", "tu", "el", "ella",
        "todo", "toda", "todos", "todas", "cada", "otro", "otra",
    }
)


def _tokenize(text: str) -> list[str]:
    """
    Lowercase, strip accents (basic), split on non-alphanumeric, remove stopwords.
    Returns a list of meaningful tokens.
    """
    text = text.lower()
    # Basic accent normalization — avoids needing unicodedata for common chars
    replacements = str.maketrans("áéíóúüàèìòùâêîôûäëïöü", "aeiouuaeiouaeiouaeiou")
    text = text.translate(replacements)
    tokens = re.findall(r"[a-z0-9]+", text)
    return [t for t in tokens if t not in _STOPWORDS and len(t) > 1]


def _score_tfidf_single(query_tokens: list[str], candidate_tokens: list[str]) -> float:
    """
    Compute a TF-IDF-inspired relevance score between query tokens and one candidate.

    Score components:
      - keyword_overlap: fraction of unique query terms found in candidate
      - term_frequency: sum of TF (term count / doc length) for matching terms
      - position_boost: bonus for query terms appearing in the first 30% of candidate

    Returns a float in [0, 1].
    """
    if not query_tokens or not candidate_tokens:
        return 0.0

    query_set = set(query_tokens)
    doc_len = len(candidate_tokens)
    doc_set = set(candidate_tokens)

    # keyword_overlap: fraction of query terms present in document
    overlap = query_set & doc_set
    keyword_overlap = len(overlap) / len(query_set)

    # term_frequency: normalized count of all query token occurrences
    tf_sum = 0.0
    for token in candidate_tokens:
        if token in query_set:
            tf_sum += 1.0
    term_frequency = min(tf_sum / doc_len, 1.0)  # cap at 1

    # position_boost: query terms in first 30% of document
    early_window = max(1, int(doc_len * 0.30))
    early_matches = sum(1 for t in candidate_tokens[:early_window] if t in query_set)
    position_boost = min(early_matches / len(query_set), 1.0)

    return keyword_overlap * 0.5 + term_frequency * 0.3 + position_boost * 0.2


class RerankerService:
    """Reranks RAG candidates using cross-encoder scoring."""

    def __init__(self) -> None:
        self._llm_available: Optional[bool] = None
        self._llm_checked_at: float = 0.0
        # Re-check availability every 5 minutes in case the key is set at runtime
        self._llm_cache_ttl: float = 300.0

    # ──────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────

    async def rerank(
        self,
        query: str,
        candidates: list[dict],
        top_k: int = 6,
    ) -> list[dict]:
        """
        Rerank candidates by relevance to query.

        Strategy (in order of preference):
          1. LLM reranking (Gemini Flash) — single API call, all candidates in one prompt.
          2. TF-IDF cross-scoring fallback — zero external deps, <100ms.

        Returns candidates sorted by descending relevance, limited to top_k.
        Falls back gracefully: any error in LLM reranking triggers TF-IDF.
        """
        if not candidates:
            return candidates

        if not settings.reranking_enabled:
            return candidates[:top_k]

        if await self.is_available():
            try:
                result = await asyncio.wait_for(
                    self._rerank_with_llm(query, candidates, top_k),
                    timeout=settings.reranking_timeout_seconds,
                )
                return result
            except asyncio.TimeoutError:
                logger.warning(
                    "RAG Reranker: LLM reranking timed out after "
                    f"{settings.reranking_timeout_seconds}s — falling back to TF-IDF"
                )
            except Exception as exc:
                logger.warning(f"RAG Reranker: LLM reranking failed: {exc} — falling back to TF-IDF")

        return await self._rerank_with_tfidf(query, candidates, top_k)

    async def is_available(self) -> bool:
        """
        Returns True if LLM reranking is available.
        Checks for google_api_key (primary) or any other provider key.
        Result is cached for 5 minutes.
        """
        now = time.monotonic()
        if (
            self._llm_available is not None
            and now - self._llm_checked_at < self._llm_cache_ttl
        ):
            return self._llm_available

        available = bool(
            settings.google_api_key
            or settings.openai_api_key
            or settings.anthropic_api_key
        )
        self._llm_available = available
        self._llm_checked_at = now
        return available

    # ──────────────────────────────────────────
    # LLM reranking
    # ──────────────────────────────────────────

    async def _rerank_with_llm(
        self, query: str, candidates: list[dict], top_k: int
    ) -> list[dict]:
        """
        Use an LLM (Gemini Flash via litellm or google-generativeai) to score
        all candidates in a single prompt.

        Each candidate is truncated to 200 chars before being sent to keep
        the prompt compact and within the latency budget.

        The model is asked to return a JSON array like:
          [{"id": 1, "score": 8}, {"id": 2, "score": 3}, ...]

        Candidates are then sorted by score descending, and the top_k are returned
        with their original data intact (score is added as 'rerank_score').
        """
        # Build the prompt
        # FIX 7: Increased from 200 to 500 chars — gives the reranker more signal
        snippets = []
        for idx, c in enumerate(candidates, 1):
            content = c.get("content", "")[:500].replace("\n", " ")
            snippets.append(f"[{idx}] {content}")

        documents_block = "\n".join(snippets)

        prompt = (
            "You are a legal document relevance ranker. "
            "Score each document on a scale from 0 to 10 for relevance to the query. "
            "10 = directly answers the query, 0 = completely unrelated.\n\n"
            f"Query: {query}\n\n"
            f"Documents:\n{documents_block}\n\n"
            "Return ONLY a valid JSON array. Example: "
            '[{"id": 1, "score": 8}, {"id": 2, "score": 3}]\n'
            "JSON:"
        )

        raw_response = await self._call_llm(prompt)
        if not raw_response:
            raise ValueError("Empty response from LLM")

        scores = self._parse_score_response(raw_response, len(candidates))
        if not scores:
            raise ValueError(f"Could not parse LLM response: {raw_response[:200]}")

        # Merge scores back into candidates
        scored = []
        for item in scores:
            idx = item["id"] - 1  # convert 1-based to 0-based
            if 0 <= idx < len(candidates):
                candidate = dict(candidates[idx])
                candidate["rerank_score"] = float(item["score"])
                scored.append(candidate)

        # Any candidate not mentioned in the LLM response gets score 0
        mentioned_ids = {item["id"] - 1 for item in scores}
        for idx, c in enumerate(candidates):
            if idx not in mentioned_ids:
                candidate = dict(c)
                candidate["rerank_score"] = 0.0
                scored.append(candidate)

        scored.sort(key=lambda x: x.get("rerank_score", 0.0), reverse=True)
        logger.info(f"RAG Reranker: LLM scored {len(scored)} candidates")
        return scored[:top_k]

    async def _call_llm(self, prompt: str) -> Optional[str]:
        """
        Call an LLM with the reranking prompt.

        Tries (in order):
          1. litellm — provider-agnostic, uses reranking_model from settings
          2. google-generativeai — direct SDK, always available if google_api_key is set
        """
        # ── litellm (primary, provider-agnostic) ──────────────────────────────
        try:
            import litellm  # type: ignore

            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: litellm.completion(
                    model=settings.reranking_model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.0,
                    max_tokens=512,
                ),
            )
            return response.choices[0].message.content
        except ImportError:
            pass  # litellm not installed — try next
        except Exception as exc:
            logger.warning(f"RAG Reranker: litellm call failed: {exc}")

        # ── google-generativeai (fallback) ─────────────────────────────────────
        if settings.google_api_key:
            try:
                import google.generativeai as genai  # type: ignore

                genai.configure(api_key=settings.google_api_key)
                model = genai.GenerativeModel("gemini-2.0-flash")

                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: model.generate_content(
                        prompt,
                        generation_config={"temperature": 0.0, "max_output_tokens": 512},
                    ),
                )
                return response.text
            except ImportError:
                logger.warning(
                    "RAG Reranker: google-generativeai not installed — falling back to TF-IDF"
                )
            except Exception as exc:
                logger.warning(f"RAG Reranker: google-generativeai call failed: {exc}")

        return None

    @staticmethod
    def _parse_score_response(raw: str, expected_count: int) -> list[dict]:
        """
        Extract JSON array from LLM response.

        The model may wrap the array in markdown code fences or add extra text.
        This method tries several extraction strategies before giving up.

        Returns a list of {"id": int, "score": float} dicts, or empty list on failure.
        """
        text = raw.strip()

        # Strip markdown code fences if present
        if "```" in text:
            text = re.sub(r"```(?:json)?", "", text).replace("```", "").strip()

        # Try direct parse first
        try:
            data = json.loads(text)
            if isinstance(data, list):
                return [{"id": int(d["id"]), "score": float(d["score"])} for d in data]
        except (json.JSONDecodeError, KeyError, TypeError, ValueError):
            pass

        # Try extracting the first [...] block from the text
        match = re.search(r"\[.*?\]", text, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(0))
                if isinstance(data, list):
                    return [{"id": int(d["id"]), "score": float(d["score"])} for d in data]
            except (json.JSONDecodeError, KeyError, TypeError, ValueError):
                pass

        return []

    # ──────────────────────────────────────────
    # TF-IDF fallback
    # ──────────────────────────────────────────

    async def _rerank_with_tfidf(
        self, query: str, candidates: list[dict], top_k: int
    ) -> list[dict]:
        """
        TF-IDF cross-scoring — no API calls, no external dependencies.

        Score for each candidate is a weighted combination of:
          - TF-IDF cross-score (70%) — keyword overlap + term frequency + position boost
          - Original score normalized (30%) — preserves hybrid search ordering

        The original_score is taken from 'hybrid_score', 'score', or 0.0.
        It is normalized to [0, 1] across all candidates before combining.
        """
        query_tokens = _tokenize(query)

        if not query_tokens:
            # No usable query terms — preserve original order
            return candidates[:top_k]

        # Gather original scores for normalization
        raw_scores = [
            float(c.get("hybrid_score") or c.get("score") or 0.0) for c in candidates
        ]
        max_orig = max(raw_scores) if raw_scores else 1.0
        min_orig = min(raw_scores) if raw_scores else 0.0
        orig_range = max_orig - min_orig if max_orig != min_orig else 1.0

        scored = []
        for idx, c in enumerate(candidates):
            candidate_tokens = _tokenize(c.get("content", ""))
            tfidf_score = _score_tfidf_single(query_tokens, candidate_tokens)

            # Normalize original score to [0, 1]
            raw = raw_scores[idx]
            orig_normalized = (raw - min_orig) / orig_range

            combined = tfidf_score * 0.7 + orig_normalized * 0.3

            result = dict(c)
            result["rerank_score"] = round(combined, 4)
            scored.append(result)

        scored.sort(key=lambda x: x.get("rerank_score", 0.0), reverse=True)
        logger.info(f"RAG Reranker: TF-IDF scored {len(scored)} candidates")
        return scored[:top_k]


# Module-level singleton
reranker_service = RerankerService()
