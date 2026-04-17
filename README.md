# Curalink

Phase 1 foundation for the AI medical research assistant prototype.

## Stack
- Frontend: React + TypeScript + Vite
- Backend: FastAPI + Pydantic
- Persistence target: MongoDB
- Model runtime target: Ollama with `gemma4:e4b`

## Dependency scope
- Backend runtime dependencies are limited to what the scaffold uses today: `fastapi`, `uvicorn`, and `pydantic-settings`.
- Backend test dependencies stay in `.[dev]` because Step 6 adds scaffold route and contract tests next.
- Frontend keeps `@tanstack/react-query` because the app shell already mounts `QueryClientProvider` as the server-state boundary.

## Local development

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Backend
```bash
cd backend
python -m venv .venv
.venv\\Scripts\\activate
python -m pip install --upgrade pip
pip install -e .[dev]
uvicorn app.main:app --reload
```

The backend serves under `http://localhost:8000` and the frontend expects `VITE_API_BASE_URL=http://localhost:8000/api/

## Phase 1 scope
- React application shell for the research workspace
- FastAPI application scaffold with health, research, chat, and session contract routes
- Shared request/response contracts mirrored in TypeScript and Pydantic
- Environment templates and baseline CI workflow

## Planning docs
- API contracts: `docs/api-contracts.md`
- Deployment strategy: `docs/deployment-strategy.md`
- Decision log: `docs/decision-log.md`
