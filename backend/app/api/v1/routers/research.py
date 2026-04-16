from fastapi import APIRouter

from app.schemas.contracts import ResearchRequest, ResearchResponse

router = APIRouter(prefix='/research', tags=['research'])


@router.post('/query', response_model=ResearchResponse)
async def run_research_query(payload: ResearchRequest) -> ResearchResponse:
    expanded_queries: list[str] = [payload.query]

    if payload.context.intent:
        expanded_queries.append(f'{payload.context.intent} + {payload.context.disease}')
    else:
        expanded_queries.append(f'{payload.query} + {payload.context.disease}')

    if payload.context.location:
        expanded_queries.append(f'{payload.context.disease} + {payload.context.location}')

    deduped_queries = list(dict.fromkeys(item.strip() for item in expanded_queries if item.strip()))

    return ResearchResponse(
        session_id=payload.session_id or 'session-scaffold',
        status='foundation_only',
        note='Phase 1 scaffold only. Retrieval, normalization, reranking, and grounded generation begin in the next phases.',
        expanded_queries=deduped_queries,
        publications=[],
        clinical_trials=[],
        evidence_count=0,
    )
