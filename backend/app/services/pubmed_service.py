"""PubMed service — two-step esearch → efetch pipeline."""

from __future__ import annotations

import logging
import xml.etree.ElementTree as ET
from typing import Any

import httpx

from app.schemas.contracts import PublicationRecord

logger = logging.getLogger(__name__)

_ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
_EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
_TOOL = "curalink"
_EMAIL = "curalink@example.org"


def _build_term(query: str, disease: str, intent: str | None) -> str:
    """Build a PubMed search term with disease context."""
    if intent:
        return f"({intent}[Title/Abstract]) AND ({disease}[Title/Abstract])"
    return f"({query}[Title/Abstract]) AND ({disease}[Title/Abstract])"


def _text(element: ET.Element | None) -> str:
    if element is None:
        return ""
    return (element.text or "").strip()


def _parse_article(article: ET.Element) -> PublicationRecord | None:
    """Parse a single PubmedArticle XML element into a PublicationRecord."""
    try:
        medline = article.find("MedlineCitation")
        if medline is None:
            return None

        pmid_el = medline.find("PMID")
        pmid = _text(pmid_el)

        art_el = medline.find("Article")
        if art_el is None:
            return None

        title = _text(art_el.find("ArticleTitle"))
        if not title:
            return None

        # Abstract
        abstract_parts: list[str] = []
        for ab_text in art_el.findall(".//AbstractText"):
            part = (ab_text.text or "").strip()
            if part:
                abstract_parts.append(part)
        abstract = " ".join(abstract_parts)

        # Authors
        authors: list[str] = []
        for author in art_el.findall(".//Author"):
            last = _text(author.find("LastName"))
            fore = _text(author.find("ForeName"))
            if last:
                authors.append(f"{last} {fore}".strip())

        # Year
        year: int | None = None
        year_el = art_el.find(".//PubDate/Year")
        if year_el is not None and year_el.text:
            try:
                year = int(year_el.text.strip())
            except ValueError:
                pass

        url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else "https://pubmed.ncbi.nlm.nih.gov/"

        return PublicationRecord(
            id=f"pmid-{pmid}" if pmid else f"pubmed-{hash(title)}",
            title=title,
            authors=authors[:5],
            publication_year=year,
            source="pubmed",
            url=url,
            abstract_snippet=abstract[:300] if abstract else None,
            supporting_snippet=abstract[:200] if abstract else None,
            relevance_reason="Retrieved via PubMed NCBI esearch/efetch pipeline",
        )
    except Exception as exc:  # noqa: BLE001
        logger.debug("Failed to parse PubMed article: %s", exc)
        return None


async def fetch_pubmed(
    query: str,
    disease: str,
    intent: str | None = None,
    candidate_target: int = 100,
) -> list[PublicationRecord]:
    """Two-step PubMed retrieval: esearch for IDs, efetch for full records."""
    term = _build_term(query, disease, intent)
    retmax = min(candidate_target, 200)

    async with httpx.AsyncClient(timeout=25.0) as client:
        # Step 1: Search
        try:
            search_params: dict[str, Any] = {
                "db": "pubmed",
                "term": term,
                "retmax": retmax,
                "sort": "pub date",
                "retmode": "json",
                "tool": _TOOL,
                "email": _EMAIL,
            }
            search_resp = await client.get(_ESEARCH_URL, params=search_params)
            search_resp.raise_for_status()
            search_data = search_resp.json()
            id_list: list[str] = search_data.get("esearchresult", {}).get("idlist", [])
        except Exception as exc:  # noqa: BLE001
            logger.warning("PubMed esearch failed: %s", exc)
            return []

        if not id_list:
            return []

        # Step 2: Fetch details in batches of 50
        records: list[PublicationRecord] = []
        batch_size = 50
        for i in range(0, len(id_list), batch_size):
            batch_ids = id_list[i : i + batch_size]
            fetch_params: dict[str, Any] = {
                "db": "pubmed",
                "id": ",".join(batch_ids),
                "retmode": "xml",
                "tool": _TOOL,
                "email": _EMAIL,
            }
            try:
                fetch_resp = await client.get(_EFETCH_URL, params=fetch_params)
                fetch_resp.raise_for_status()
                root = ET.fromstring(fetch_resp.text)
                for article_el in root.findall("PubmedArticle"):
                    record = _parse_article(article_el)
                    if record:
                        records.append(record)
            except Exception as exc:  # noqa: BLE001
                logger.warning("PubMed efetch batch failed: %s", exc)

    return records
