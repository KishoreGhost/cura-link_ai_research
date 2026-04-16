import uuid

from fastapi import APIRouter, HTTPException

from app.schemas.contracts import SessionCreateRequest, SessionSummary
from app.services.session_store import get_session as load_session
from app.services.session_store import save_session

router = APIRouter(prefix='/sessions', tags=['sessions'])


@router.post('', response_model=SessionSummary)
async def create_session(payload: SessionCreateRequest) -> SessionSummary:
    session = SessionSummary(
        session_id=f'session-{uuid.uuid4().hex[:12]}',
        patient_alias=payload.patient_alias,
        disease=payload.disease,
        location=payload.location,
        message_count=0,
        last_activity_label='created from scaffold store',
    )
    return save_session(session)


@router.get('/{session_id}', response_model=SessionSummary)
async def get_session(session_id: str) -> SessionSummary:
    session = load_session(session_id)
    if session is None:
        raise HTTPException(
            status_code=404,
            detail='Scaffold session not found. Only sessions created during the current backend process are readable until persistence is implemented.',
        )
    return session
