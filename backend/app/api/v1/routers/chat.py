import uuid

from fastapi import APIRouter, HTTPException

from app.schemas.contracts import AnswerSection, ChatMessage, ChatTurnRequest, ChatTurnResponse, SessionSummary
from app.services.session_store import get_session as load_session
from app.services.session_store import save_session

router = APIRouter(prefix='/chat', tags=['chat'])


def apply_context_update(session: SessionSummary, payload: ChatTurnRequest) -> SessionSummary:
    context_update = payload.context_update
    if context_update is None:
        return session

    if context_update.patient_alias is not None:
        session.patient_alias = context_update.patient_alias
    if context_update.disease is not None:
        session.disease = context_update.disease
    if context_update.location is not None:
        session.location = context_update.location

    return session


@router.post('/turn', response_model=ChatTurnResponse)
async def create_chat_turn(payload: ChatTurnRequest) -> ChatTurnResponse:
    if payload.session_id is None:
        session = SessionSummary(
            session_id=f'session-{uuid.uuid4().hex[:12]}',
            last_activity_label='created from chat scaffold',
        )
        context_mode = 'request context established a new disease-aware scaffold session'
    else:
        session = load_session(payload.session_id)
        if session is None:
            raise HTTPException(
                status_code=404,
                detail='Scaffold session not found. Create a session first or omit session_id to start a new scaffold chat session.',
            )

        if session.disease is None and (payload.context_update is None or payload.context_update.disease is None):
            raise HTTPException(
                status_code=422,
                detail='Stored scaffold session lacks disease context. Provide context_update.disease before reusing this session.',
            )

        context_mode = 'existing scaffold session context reused'

    session = apply_context_update(session, payload)
    session.message_count += len(payload.messages)
    session.last_activity_label = 'chat scaffold updated'
    save_session(session)

    if payload.context_update is not None and payload.session_id is not None:
        context_mode = 'existing scaffold session context reused with request updates'

    return ChatTurnResponse(
        session_id=session.session_id,
        status='foundation_only',
        message=ChatMessage(
            role='assistant',
            content='Phase 1 scaffold chat is active. Follow-up turns can reuse session_id without resending full disease context.',
        ),
        answer_sections=[
            AnswerSection(
                heading='System status',
                body=f'Chat contract ready: {context_mode}. Live retrieval and LLM synthesis are not wired yet.',
            )
        ],
        citations=[],
    )
