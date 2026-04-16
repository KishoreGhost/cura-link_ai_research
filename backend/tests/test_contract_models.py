import pytest
from pydantic import ValidationError

from app.schemas.contracts import ChatTurnRequest, QueryContextUpdate


def test_query_context_update_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        QueryContextUpdate.model_validate({"disease": "Lung cancer", "intent": "ignore me"})


def test_new_chat_turn_requires_disease_context() -> None:
    with pytest.raises(ValidationError):
        ChatTurnRequest.model_validate(
            {
                "context_update": {"patient_alias": "Case Atlas"},
                "messages": [{"role": "user", "content": "hello"}],
            }
        )


def test_follow_up_chat_turn_can_reuse_session_without_context_update() -> None:
    payload = ChatTurnRequest.model_validate(
        {
            "session_id": "session-123",
            "messages": [{"role": "user", "content": "What about vitamin D?"}],
        }
    )

    assert payload.session_id == "session-123"
    assert payload.context_update is None
