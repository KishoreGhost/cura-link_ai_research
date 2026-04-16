# Task Tracker

## Active Task

- [x] Review `project_summary.md` and extract requirements
- [x] Research React, FastAPI, and local-LLM integration via Context7
- [x] Draft the phased architecture and delivery plan
- [x] Resolve open questions before implementation begins
- [x] Bring the Phase 1 scaffold up to approval standard through single-step review gates
- [ ] Begin Phase 2 with source connectors and normalization through single-step review gates

## Approval Status

- Phase 1 scaffold and correction cycle are approved.
- Phase 2 has not started yet and should continue under single-step review gates.
- No active remediation submission is open.

## Remediation Steps

### Step 1 - Tracker and Lessons
- [x] Re-scope the tracker so review happens one completed step at a time
- [x] Record the workflow and contract mistakes in `tasks/lessons.md`
- [x] Stop for review before touching scaffold code or plan docs

### Step 2 - Session Contract Consistency
- [x] Fix `GET /sessions/{session_id}` so the scaffold is consistent with session creation
- [x] Return explicit scaffold or not-found behavior instead of fabricated unrelated patient data

### Step 3 - Chat Contract Follow-Ups
- [x] Revisit the chat contract so follow-up turns are not forced to resend disease context every time
- [x] Enforce disease-aware minimum context for new chat sessions
- [x] Remove unused `intent` and `follow_up_question` fields from `QueryContextUpdate`
- [x] Reject unknown `QueryContextUpdate` fields at the API boundary
- [x] Reject follow-up reuse when stored session context is insufficient and no replacement disease context is provided
- [x] Update the shared backend and frontend contracts to reflect that shape
- [x] Re-prove the Step 3 edge cases in isolation

### Step 4 - Frontend Scaffold Cleanup
- [x] Remove leftover Vite starter files instead of excluding them from TypeScript
- [x] Keep the frontend build green after cleanup

### Step 5 - Dependency Review
- [x] Trim unused phase-ahead dependencies from the scaffold
- [x] Document the justification for dependencies that remain ahead of implementation

### Step 6 - Minimal Automated Tests
- [x] Add automated tests for scaffold routes and contract shapes
- [x] Cover the previously fixed `404` failure modes for missing session read and unknown chat session reuse
- [x] Isolate in-memory session-store state per test
- [x] Verify the scaffold with test execution, not only build/import checks

### Step 7 - Plan and Documentation Corrections
- [x] Add an explicit deployment strategy for the open-source model runtime so the live deployed app requirement is satisfiable
- [x] Add a short architecture decision record or decision-log section capturing the resolved questions, approver, and approval date
- [x] Pull parser and API contract testing forward into Phases 1-2 in the written plan

### Step 8 - Final Verification of Corrections
- [x] Re-verify scaffold behavior, tests, and corrected plan docs
- [x] Stop for review before Phase 2 begins

## Locked Decisions

- Backend stack: `FastAPI` replaces `Express` for the application backend.
- Frontend stack: `React + TypeScript + Vite`.
- Persistence target: `MongoDB` for sessions, evidence snapshots, and conversation history.
- LLM runtime target: local `Ollama` on `GPU` using the installed `gemma4:e4b` model as the initial reasoning model.
- Authentication: no auth in v1; ship as a session-based prototype.
- Retrieval architecture: live API fetches first, normalization plus transparent reranking before introducing heavier infra.

## Phased Plan

### Phase 1 - Foundation and Monorepo Setup
- [x] Create `frontend/` with React + TypeScript + Vite
- [x] Create `backend/` with FastAPI, Pydantic models, environment config, and health routes
- [x] Define shared API contracts for chat, evidence, trials, publications, and sessions
- [x] Establish local development workflow, `.env` templates, and basic CI checks
- [x] Add contract-validation and scaffold-route tests during the foundation phase

### Phase 2 - Data Connectors and Normalization
- [ ] Implement async clients for `OpenAlex`, `PubMed`, and `ClinicalTrials.gov`
- [ ] Add request validation, retries, timeouts, and source-specific parsers
- [ ] Normalize publications and trials into a single internal evidence schema
- [ ] Add parser fixtures and normalization regression tests for source payloads
- [ ] Persist raw fetch metadata and normalized records for traceability/debugging

### Phase 3 - Retrieval and Ranking Pipeline
- [ ] Build query understanding pipeline for disease, intent, optional location, and follow-up context
- [ ] Implement intelligent query expansion so user intent is merged with disease context automatically
- [ ] Retrieve a broad candidate pool from all sources before filtering (`50-300` target)
- [ ] Deduplicate, score, and rerank evidence using a hybrid strategy (lexical + metadata + optional embeddings)
- [ ] Select top evidence packs for final answer generation and UI display

### Phase 4 - LLM Reasoning Layer
- [ ] Integrate a local open-source model runtime via `Ollama`
- [ ] Add structured output schemas so answers remain machine-parseable and source-backed
- [ ] Compose prompts from normalized evidence, conversation context, and response format requirements
- [ ] Add hallucination controls: only answer from retrieved evidence, cite every claim, and abstain when evidence is weak

### Phase 5 - Conversation Memory and Personalization
- [ ] Model conversation sessions, message history, inferred disease context, and user preferences in MongoDB
- [ ] Distinguish when a follow-up should reuse context vs trigger a fresh retrieval pass
- [ ] Add lightweight session summarization so long chats remain performant
- [ ] Persist generated answers, ranked evidence, and source snippets for replay/debugging

### Phase 6 - Frontend Experience
- [ ] Build the main research workspace with context intake, chat, and evidence panels
- [ ] Support structured inputs plus free-form follow-up questions in the same experience
- [ ] Stream answer generation status and show retrieval/ranking progress states
- [ ] Render publications, clinical trials, and citations as first-class UI artifacts
- [ ] Add empty, loading, error, and no-evidence states that still feel intentional

### Phase 7 - Quality, Safety, and Evaluation
- [ ] Add tests for query expansion, reranking behavior, and benchmark evaluation flows
- [ ] Add medical-safety UX guardrails and research-only disclaimers
- [ ] Add rate limiting, secret handling, and basic abuse protections
- [ ] Prepare benchmark/demo queries from the hackathon brief and verify output quality

### Phase 8 - Deployment and Demo Readiness
- [ ] Deploy frontend and backend to stable public URLs
- [ ] Deploy the open-source model runtime on a GPU-backed host with persistent storage
- [ ] Validate end-to-end flows against live sources and the selected model runtime
- [ ] Prepare Loom demo script covering architecture, retrieval pipeline, ranking logic, and live use cases
- [ ] Final polish for the hackathon submission

## Step Review

- 2026-04-15: Read `project_summary.md` and extracted the required capabilities, mandatory sources, and delivery constraints.
- 2026-04-15: Researched official docs via Context7 for `FastAPI` (`/fastapi/fastapi`), `React` (`/reactjs/react.dev`), and `Ollama Python` (`/ollama/ollama-python`).
- 2026-04-15: Drafted the phased build plan, architecture direction, and open questions required before implementation.
- 2026-04-15: Locked the architecture with the user: `FastAPI`, local GPU with `gemma4:e4b` on `Ollama`, and no-auth session-based v1.
- 2026-04-15: Implemented the initial scaffold for the React workspace shell, FastAPI app skeleton, shared contracts, env templates, and CI workflow.
- 2026-04-15: Verified the backend by compiling `backend/app` and importing `app.main:app`; verified the frontend with a successful `npm run build` production build.
- 2026-04-15: Re-scoped the remediation work into single review gates after the user rejected batching the whole phase behind one approval step.
- 2026-04-15: Fixed the scaffold session contract by storing created sessions in-process and returning an explicit `404` for unknown session IDs; verified `POST /api/v1/sessions`, `GET /api/v1/sessions/{created_id}`, and `GET /api/v1/sessions/session-missing` via `TestClient`.
- 2026-04-16: Reworked Step 3 so new chat sessions require disease-aware context, follow-up turns can reuse `session_id` without resending disease context, and `QueryContextUpdate` only includes fields the scaffold actually stores.
- 2026-04-16: Tightened Step 3 runtime validation: unknown `QueryContextUpdate` fields now fail with `422`, disease-less stored sessions cannot be reused without `context_update.disease`, and the API contract doc now matches the enforced behavior exactly.
- 2026-04-16: Re-verified Step 4 in isolation: the frontend source tree contains only live app files, the TypeScript config no longer uses starter-file exclusions, and `npm run build` passes.
- 2026-04-16: Completed Step 5 by trimming unused backend runtime dependencies (`httpx`, `motor`, `ollama`) from `backend/pyproject.toml`, documenting the remaining dependency scope in `README.md`, reinstalling the editable backend package, re-importing `app.main`, and re-running the frontend production build.
- 2026-04-16: Completed Step 6 by adding backend route tests and contract-model tests, moving backend CI verification to `pytest`, isolating the in-memory session store per test with an autouse fixture, covering the fixed `404` failure modes for missing session read and unknown chat session reuse, and passing `12` local tests with `python -m pytest -q`.
- 2026-04-16: Completed Step 7 by adding a source-backed model-runtime deployment strategy, creating a repo decision log with approver/date records, and moving contract/parser testing explicitly into Phases 1-2 of the written plan.
- 2026-04-16: Corrected Step 7 planning docs by recording the public deployment/runtime decision in the repo decision log, removing duplicated later-phase ownership for API contract and source-normalization testing, and adding the corresponding planning lessons.
- 2026-04-16: Completed Step 8 final verification by re-running the backend test suite (`12 passed`), re-running the frontend production build, re-checking FastAPI readiness and scaffold research-query behavior via `TestClient`, and re-reading the corrected planning docs for deployment, decisions, and API contracts.
- 2026-04-16: User approved the Phase 1 scaffold and remediation cycle after Step 8 verification.
