"""OpenAlex service — fetches and normalises research publications."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from app.schemas.contracts import PublicationRecord

logger = logging.getLogger(__name__)

_BASE_URL = "https://api.openalex.org/works"
_HEADERS = {"User-Agent": "Curalink/1.0 (mailto:curalink@example.org)"}


def _build_queries(query: str, disease: str, intent: str | None) -> list[str]:
    """Expand the base query into multiple search variants."""
    queries: list[str] = []
    if intent:
        queries.append(f"{intent} {disease}")
    queries.append(f"{query} {disease}")
    queries.append(disease)
    # deduplicate while preserving order
    seen: set[str] = set()
    unique: list[str] = []
    for q in queries:
        key = q.strip().lower()
        if key not in seen:
            seen.add(key)
            unique.append(q.strip())
    return unique


def _parse_work(work: dict[str, Any]) -> PublicationRecord | None:
    try:
        title: str = work.get("title") or ""
        if not title:
            return None

        abstract_inverted = work.get("abstract_inverted_index") or {}
        abstract = _reconstruct_abstract(abstract_inverted)

        authors: list[str] = [
            auth.get("author", {}).get("display_name", "")
            for auth in (work.get("authorships") or [])
            if auth.get("author", {}).get("display_name")
        ]

        year: int | None = work.get("publication_year")
        doi: str = work.get("doi") or ""
        openalex_id: str = work.get("id") or ""
        url: str = doi if doi.startswith("http") else (f"https://doi.org/{doi}" if doi else openalex_id)

        return PublicationRecord(
            id=openalex_id.split("/")[-1] if openalex_id else f"oa-{hash(title)}",
            title=title,
            authors=authors[:5],
            publication_year=year,
            source="openalex",
            url=url or "https://api.openalex.org/",
            abstract_snippet=abstract[:300] if abstract else None,
            supporting_snippet=abstract[:200] if abstract else None,
            relevance_reason="Retrieved via OpenAlex full-text search",
        )
    except Exception as exc:  # noqa: BLE001
        logger.debug("Failed to parse OpenAlex work: %s", exc)
        return None


def _reconstruct_abstract(inverted: dict[str, list[int]]) -> str:
    """Reconstruct an abstract from OpenAlex inverted index format."""
    if not inverted:
        return ""
    positions: list[tuple[int, str]] = []
    for word, idxs in inverted.items():
        for idx in idxs:
            positions.append((idx, word))
    positions.sort(key=lambda x: x[0])
    return " ".join(w for _, w in positions)


async def fetch_openalex(
    query: str,
    disease: str,
    intent: str | None = None,
    candidate_target: int = 150,
) -> list[PublicationRecord]:
    """Fetch a broad candidate pool from OpenAlex (up to candidate_target results)."""
    expanded = _build_queries(query, disease, intent)
    per_page = min(200, candidate_target)
    all_records: dict[str, PublicationRecord] = {}

    async with httpx.AsyncClient(headers=_HEADERS, timeout=20.0) as client:
        for q in expanded:
            if len(all_records) >= candidate_target:
                break
            remaining = candidate_target - len(all_records)
            batch_size = min(per_page, remaining, 200)
            params = {
                "search": q,
                "per-page": batch_size,
                "page": 1,
                "sort": "relevance_score:desc",
                "filter": "from_publication_date:2015-01-01",
            }
            try:
                response = await client.get(_BASE_URL, params=params)
                response.raise_for_status()
                data = response.json()
                for work in data.get("results", []):
                    record = _parse_work(work)
                    if record and record.id not in all_records:
                        all_records[record.id] = record
            except Exception as exc:  # noqa: BLE001
                logger.warning("OpenAlex fetch failed for query '%s': %s", q, exc)

    return list(all_records.values())
