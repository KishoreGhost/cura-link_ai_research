"""Reranker — scores and selects the top-K evidence from a broad candidate pool.

Scoring factors (per project_summary.md §4):
  - Keyword relevance: how many query tokens appear in title + abstract
  - Recency: publications newer than 2020 score higher
  - Source credibility: PubMed abstracts get a slight boost
  - Abstract completeness: longer abstracts indicate richer evidence
"""

from __future__ import annotations

import math
import re
from datetime import date

from app.schemas.contracts import ClinicalTrialRecord, PublicationRecord

_CURRENT_YEAR = date.today().year
_STOP_WORDS = {
    "a", "an", "the", "and", "or", "of", "in", "to", "for",
    "with", "on", "at", "by", "is", "was", "are", "were",
    "be", "been", "has", "have", "had", "that", "this", "from",
}


def _tokenize(text: str) -> set[str]:
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    return {t for t in tokens if t not in _STOP_WORDS and len(t) > 2}


def _keyword_score(record_text: str, query_tokens: set[str]) -> float:
    """Fraction of query tokens found in the record text."""
    if not query_tokens:
        return 0.0
    record_tokens = _tokenize(record_text)
    hits = query_tokens & record_tokens
    return len(hits) / len(query_tokens)


def _recency_score(year: int | None) -> float:
    """Sigmoid-style recency score — recent years score near 1.0."""
    if year is None:
        return 0.3
    age = max(0, _CURRENT_YEAR - year)
    return 1.0 / (1.0 + math.exp(0.4 * (age - 5)))


def _credibility_score(source: str) -> float:
    return {"pubmed": 1.0, "openalex": 0.85, "clinicaltrials": 0.9}.get(source, 0.7)


def _abstract_length_score(snippet: str | None) -> float:
    if not snippet:
        return 0.0
    length = len(snippet)
    return min(1.0, length / 250)


def score_publication(pub: PublicationRecord, query_tokens: set[str]) -> float:
    text = f"{pub.title} {pub.abstract_snippet or ''}"
    kw = _keyword_score(text, query_tokens) * 0.45
    rec = _recency_score(pub.publication_year) * 0.30
    cred = _credibility_score(pub.source) * 0.15
    length = _abstract_length_score(pub.abstract_snippet) * 0.10
    return kw + rec + cred + length


def score_trial(trial: ClinicalTrialRecord, query_tokens: set[str]) -> float:
    text = f"{trial.title} {trial.supporting_snippet or ''} {trial.eligibility_criteria or ''}"
    kw = _keyword_score(text, query_tokens) * 0.50
    # Recruiting trials score higher
    status_bonus = 0.20 if "recruiting" in trial.recruiting_status.lower() else 0.05
    cred = _credibility_score(trial.source) * 0.10
    length = _abstract_length_score(trial.supporting_snippet) * 0.20
    return kw + status_bonus + cred + length


def rerank_publications(
    publications: list[PublicationRecord],
    query: str,
    disease: str,
    intent: str | None = None,
    top_k: int = 8,
) -> list[PublicationRecord]:
    """Score and return top_k publications from the candidate pool."""
    combined_text = f"{query} {disease} {intent or ''}"
    query_tokens = _tokenize(combined_text)

    scored = [
        (score_publication(pub, query_tokens), pub)
        for pub in publications
    ]
    scored.sort(key=lambda x: x[0], reverse=True)

    # Attach relevance reason
    results: list[PublicationRecord] = []
    for score, pub in scored[:top_k]:
        pub_copy = pub.model_copy(
            update={"relevance_reason": f"Relevance score: {score:.2f} (keyword + recency + credibility)"}
        )
        results.append(pub_copy)
    return results


def rerank_trials(
    trials: list[ClinicalTrialRecord],
    query: str,
    disease: str,
    intent: str | None = None,
    top_k: int = 6,
) -> list[ClinicalTrialRecord]:
    """Score and return top_k clinical trials."""
    combined_text = f"{query} {disease} {intent or ''}"
    query_tokens = _tokenize(combined_text)

    scored = [
        (score_trial(trial, query_tokens), trial)
        for trial in trials
    ]
    scored.sort(key=lambda x: x[0], reverse=True)

    results: list[ClinicalTrialRecord] = []
    for score, trial in scored[:top_k]:
        t_copy = trial.model_copy(
            update={"relevance_reason": f"Relevance score: {score:.2f} (keyword + status + credibility)"}
        )
        results.append(t_copy)
    return results
