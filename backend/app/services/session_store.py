from app.schemas.contracts import SessionSummary


_session_store: dict[str, SessionSummary] = {}


def save_session(session: SessionSummary) -> SessionSummary:
    _session_store[session.session_id] = session
    return session


def get_session(session_id: str) -> SessionSummary | None:
    return _session_store.get(session_id)


def clear_session_store() -> None:
    _session_store.clear()
