"""Chat router — wires session context + evidence retrieval + Ollama LLM reasoning."""

from __future__ import annotations

import asyncio
import logging
import uuid

from fastapi import APIRouter, HTTPException

from app.schemas.contracts import (
    ChatMessage,
    ChatTurnRequest,
    ChatTurnResponse,
    SessionSummary,
)
from app.services.clinicaltrials_service import fetch_clinical_trials
from app.services.llm_service import (
    generate_research_answer,
    generate_conversational_response,
    is_conversational,
)
from app.services.openalex_service import fetch_openalex
from app.services.pubmed_service import fetch_pubmed
from app.services.reranker import rerank_publications, rerank_trials
from app.services.session_store import get_session as load_session
from app.services.session_store import save_session

logger = logging.getLogger(__name__)
router = APIRouter(prefix='/chat', tags=['chat'])

# In-memory conversation history per session
_conversation_store: dict[str, list[ChatMessage]] = {}


def _apply_context_update(session: SessionSummary, payload: ChatTurnRequest) -> SessionSummary:
    if payload.context_update is None:
        return session
    cu = payload.context_update
    if cu.patient_alias is not None:
        session.patient_alias = cu.patient_alias
    if cu.disease is not None:
        session.disease = cu.disease
    if cu.location is not None:
        session.location = cu.location
    return session


def _get_user_message(payload: ChatTurnRequest) -> str:
    """Extract the latest user message from the payload."""
    user_msgs = [m for m in payload.messages if m.role == 'user']
    return user_msgs[-1].content if user_msgs else ''


@router.post('/turn', response_model=ChatTurnResponse)
async def create_chat_turn(payload: ChatTurnRequest) -> ChatTurnResponse:
    # --- Session resolution ---
    if payload.session_id is None:
        session = SessionSummary(
            session_id=f'session-{uuid.uuid4().hex[:12]}',
            last_activity_label='new session',
        )
    else:
        session = load_session(payload.session_id)
        if session is None:
            raise HTTPException(
                status_code=404,
                detail='Session not found. Omit session_id to start a new session.',
            )
        if session.disease is None and (payload.context_update is None or payload.context_update.disease is None):
            raise HTTPException(
                status_code=422,
                detail='Session lacks disease context. Provide context_update.disease.',
            )

    session = _apply_context_update(session, payload)
    disease = session.disease or ''
    location = session.location

    # --- Determine user query ---
    user_message = _get_user_message(payload)
    intent = payload.context_update.disease if payload.context_update else None

    # --- Load conversation history ---
    history = _conversation_store.get(session.session_id, [])

    # ───────────────────────────────────────────────────────────
    # FAST PATH: conversational / greeting — skip retrieval entirely
    # ───────────────────────────────────────────────────────────
    if is_conversational(user_message):
        logger.info("Conversational message detected — skipping retrieval: '%s'", user_message)
        answer_sections, citations, raw_llm = await generate_conversational_response(user_message)
        assistant_msg = ChatMessage(role='assistant', content=raw_llm[:500])

        # Still track history so follow-up medical queries have context
        history.extend(payload.messages)
        history.append(assistant_msg)
        _conversation_store[session.session_id] = history[-20:]
        session.message_count += len(payload.messages) + 1
        session.last_activity_label = 'updated'
        save_session(session)

        return ChatTurnResponse(
            session_id=session.session_id,
            status='completed',
            message=assistant_msg,
            answer_sections=answer_sections,
            citations=[],
        )

    # ───────────────────────────────────────────────────────────
    # RESEARCH PATH: full retrieval + reranking + LLM synthesis
    # ───────────────────────────────────────────────────────────
    logger.info("Research query: disease='%s' query='%s'", disease, user_message)
    try:
        oa_task = fetch_openalex(user_message, disease, intent, candidate_target=60)
        pm_task = fetch_pubmed(user_message, disease, intent, candidate_target=60)
        ct_task = fetch_clinical_trials(disease, intent=intent, location=location)
        oa_results, pm_results, trials_raw = await asyncio.gather(oa_task, pm_task, ct_task)
    except Exception as exc:
        logger.error("Retrieval failed in chat turn: %s", exc)
        oa_results, pm_results, trials_raw = [], [], []

    # --- Merge + rerank ---
    all_pubs = oa_results + pm_results
    seen_titles: set[str] = set()
    deduped = []
    for pub in all_pubs:
        key = pub.title.lower()[:60]
        if key not in seen_titles:
            seen_titles.add(key)
            deduped.append(pub)

    top_pubs = rerank_publications(deduped, user_message, disease, intent, top_k=6)
    top_trials = rerank_trials(trials_raw, user_message, disease, intent, top_k=4)

    # --- LLM reasoning ---
    answer_sections, citations, raw_llm = await generate_research_answer(
        query=user_message,
        disease=disease,
        intent=intent,
        location=location,
        conversation_history=history,
        publications=top_pubs,
        trials=top_trials,
    )

    # --- Update conversation history ---
    history.extend(payload.messages)
    assistant_msg = ChatMessage(role='assistant', content=raw_llm[:1000] if raw_llm else 'Research complete.')
    history.append(assistant_msg)
    _conversation_store[session.session_id] = history[-20:]  # Keep last 20 messages

    # --- Persist session ---
    session.message_count += len(payload.messages) + 1
    session.last_activity_label = 'updated'
    save_session(session)

    return ChatTurnResponse(
        session_id=session.session_id,
        status='completed',
        message=assistant_msg,
        answer_sections=answer_sections,
        citations=citations,
    )
