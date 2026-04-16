import pytest

from app.services.session_store import clear_session_store


@pytest.fixture(autouse=True)
def reset_session_store() -> None:
    clear_session_store()
    yield
    clear_session_store()
