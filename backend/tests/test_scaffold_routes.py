from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_ready_reports_scaffold_status() -> None:
    response = client.get("/api/v1/health/ready")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready"
    assert body["api_prefix"] == "/api/v1"
    assert body["ollama_model"] == "gemma4:e4b"


def test_research_query_expands_disease_context() -> None:
    response = client.post(
        "/api/v1/research/query",
        json={
            "query": "Latest treatment",
            "context": {
                "disease": "Lung cancer",
                "intent": "Latest treatment options",
                "location": "Toronto, Canada",
            },
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "foundation_only"
    assert "Latest treatment options + Lung cancer" in body["expanded_queries"]
    assert "Lung cancer + Toronto, Canada" in body["expanded_queries"]


def test_session_create_and_read_round_trip() -> None:
    created = client.post(
        "/api/v1/sessions",
        json={
            "patient_alias": "Case Atlas",
            "disease": "Lung cancer",
            "location": "Toronto, Canada",
        },
    )

    assert created.status_code == 200
    created_body = created.json()

    fetched = client.get(f"/api/v1/sessions/{created_body['session_id']}")
    assert fetched.status_code == 200
    assert fetched.json() == created_body


def test_session_read_returns_404_for_missing_session() -> None:
    response = client.get("/api/v1/sessions/session-missing")

    assert response.status_code == 404
    assert "Scaffold session not found" in response.json()["detail"]


def test_chat_turn_requires_disease_context_for_new_session() -> None:
    response = client.post(
        "/api/v1/chat/turn",
        json={
            "context_update": {"patient_alias": "Case Atlas"},
            "messages": [{"role": "user", "content": "hello"}],
        },
    )

    assert response.status_code == 422
    assert "context_update.disease" in response.json()["detail"][0]["msg"]


def test_chat_turn_rejects_unknown_context_update_field() -> None:
    response = client.post(
        "/api/v1/chat/turn",
        json={
            "context_update": {"disease": "Lung cancer", "intent": "ignored-before"},
            "messages": [{"role": "user", "content": "Latest treatment?"}],
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"][0]["type"] == "extra_forbidden"


def test_chat_turn_returns_404_for_unknown_session_id() -> None:
    response = client.post(
        "/api/v1/chat/turn",
        json={
            "session_id": "session-missing",
            "messages": [{"role": "user", "content": "Latest treatment?"}],
        },
    )

    assert response.status_code == 404
    assert "Scaffold session not found" in response.json()["detail"]


def test_chat_turn_reuses_disease_aware_session_without_resending_context() -> None:
    created = client.post(
        "/api/v1/chat/turn",
        json={
            "context_update": {"disease": "Lung cancer", "patient_alias": "Case Atlas"},
            "messages": [{"role": "user", "content": "Latest treatment?"}],
        },
    )

    assert created.status_code == 200
    session_id = created.json()["session_id"]

    follow_up = client.post(
        "/api/v1/chat/turn",
        json={
            "session_id": session_id,
            "messages": [{"role": "user", "content": "What about vitamin D?"}],
        },
    )

    assert follow_up.status_code == 200
    assert follow_up.json()["session_id"] == session_id


def test_chat_turn_requires_repair_for_session_without_disease_context() -> None:
    session = client.post(
        "/api/v1/sessions",
        json={"patient_alias": "Case Atlas", "location": "Toronto, Canada"},
    )
    session_id = session.json()["session_id"]

    insufficient = client.post(
        "/api/v1/chat/turn",
        json={
            "session_id": session_id,
            "messages": [{"role": "user", "content": "What next?"}],
        },
    )
    assert insufficient.status_code == 422
    assert "lacks disease context" in insufficient.json()["detail"]

    repaired = client.post(
        "/api/v1/chat/turn",
        json={
            "session_id": session_id,
            "context_update": {"disease": "Lung cancer"},
            "messages": [{"role": "user", "content": "What next?"}],
        },
    )
    assert repaired.status_code == 200
    assert repaired.json()["session_id"] == session_id
