# API Contracts

These are the Phase 1 foundation contracts. The endpoints are intentionally lightweight and return scaffold responses until retrieval and reasoning are implemented in later phases.

## Endpoints
- `GET /api/v1/health/live`
- `GET /api/v1/health/ready`
- `POST /api/v1/research/query`
- `POST /api/v1/chat/turn`
- `POST /api/v1/sessions`
- `GET /api/v1/sessions/{session_id}`

## Chat turn contract

### `POST /api/v1/chat/turn`
The chat scaffold supports follow-up turns without resending full disease context on every request, but only when the session already has sufficient disease-aware context.

Request shape:
- `session_id?: string`
- `context_update?: QueryContextUpdate`
- `messages: ChatMessage[]`

Rules:
- A new scaffold chat session without `session_id` must provide `context_update.disease`.
- Follow-up turns can send `session_id` plus new `messages` only if the stored session already contains disease context.
- If a stored session lacks disease context, the follow-up request must provide `context_update.disease`.
- `QueryContextUpdate` accepts only `patient_alias`, `disease`, and `location`.
- Unknown `QueryContextUpdate` fields are rejected at the API boundary.

## Shared models
- `QueryContext`
- `QueryContextUpdate`
- `PublicationRecord`
- `ClinicalTrialRecord`
- `CitationRecord`
- `ResearchRequest`
- `ResearchResponse`
- `ChatTurnRequest`
- `ChatTurnResponse`
- `SessionCreateRequest`
- `SessionSummary`

## Notes
- The frontend TypeScript contracts live in `frontend/src/contracts/api.ts`.
- The backend Pydantic contracts live in `backend/app/schemas/contracts.py`.
- JSON field naming is snake_case for parity between FastAPI responses and Python models.
