"""Research router — full pipeline: query expand → retrieve → rerank → respond."""

from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, HTTPException

from app.schemas.contracts import ResearchRequest, ResearchResponse
from app.services.clinicaltrials_service import fetch_clinical_trials
from app.services.openalex_service import fetch_openalex
from app.services.pubmed_service import fetch_pubmed
from app.services.reranker import rerank_publications, rerank_trials

logger = logging.getLogger(__name__)
router = APIRouter(prefix='/research', tags=['research'])


@router.post('/query', response_model=ResearchResponse)
async def run_research_query(payload: ResearchRequest) -> ResearchResponse:
    disease = payload.context.disease
    intent = payload.context.intent
    location = payload.context.location
    query = payload.query
    candidate_target = payload.candidate_target

    # --- Phase 1: Query expansion ---
    expanded_queries: list[str] = []
    if intent:
        expanded_queries.append(f"{intent} + {disease}")
    else:
        expanded_queries.append(f"{query} + {disease}")
    if location:
        expanded_queries.append(f"{disease} + {location}")
    expanded_queries.insert(0, query)
    # deduplicate
    seen: set[str] = set()
    unique_queries: list[str] = []
    for q in expanded_queries:
        key = q.strip().lower()
        if key not in seen:
            seen.add(key)
            unique_queries.append(q.strip())

    # --- Phase 2: Parallel retrieval ---
    pubs_per_source = candidate_target // 2

    try:
        openalex_task = fetch_openalex(query, disease, intent, candidate_target=pubs_per_source)
        pubmed_task = fetch_pubmed(query, disease, intent, candidate_target=pubs_per_source)

        if payload.include_trials:
            trials_task = fetch_clinical_trials(disease, intent=intent, location=location)
            openalex_results, pubmed_results, trials_raw = await asyncio.gather(
                openalex_task, pubmed_task, trials_task
            )
        else:
            openalex_results, pubmed_results = await asyncio.gather(openalex_task, pubmed_task)
            trials_raw = []

    except Exception as exc:
        logger.error("Retrieval pipeline error: %s", exc)
        raise HTTPException(status_code=502, detail=f"Evidence retrieval failed: {exc}") from exc

    # --- Phase 3: Merge + deduplicate candidate pool ---
    all_publications = openalex_results + pubmed_results
    # Deduplicate by approximate title match
    seen_titles: set[str] = set()
    deduped_publications = []
    for pub in all_publications:
        title_key = pub.title.lower()[:60]
        if title_key not in seen_titles:
            seen_titles.add(title_key)
            deduped_publications.append(pub)

    logger.info(
        "Candidate pool: %d publications (%d OA + %d PM), %d trials",
        len(deduped_publications),
        len(openalex_results),
        len(pubmed_results),
        len(trials_raw),
    )

    # --- Phase 4: Rerank ---
    top_publications = rerank_publications(
        deduped_publications, query, disease, intent, top_k=8
    )
    top_trials = rerank_trials(trials_raw, query, disease, intent, top_k=6)

    return ResearchResponse(
        session_id=payload.session_id or 'session-research',
        status='ready',
        note=(
            f"Retrieved {len(deduped_publications)} candidate publications "
            f"({len(openalex_results)} OpenAlex + {len(pubmed_results)} PubMed) and "
            f"{len(trials_raw)} trials. Reranked to top {len(top_publications)} publications "
            f"and {len(top_trials)} trials."
        ),
        expanded_queries=unique_queries,
        publications=top_publications,
        clinical_trials=top_trials,
        evidence_count=len(top_publications) + len(top_trials),
    )
