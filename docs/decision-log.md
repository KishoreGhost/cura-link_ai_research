# Decision Log

## Resolved decisions

| Date | Decision | Resolution | Approver | Notes |
| --- | --- | --- | --- | --- |
| 2026-04-15 | Backend stack conflict with `MERN` wording | Use `FastAPI` instead of `Express` for the application backend | User | Decision made explicitly in chat and recorded in repo |
| 2026-04-15 | Initial model runtime | Use local `Ollama` on GPU with `gemma4:e4b` as the first reasoning model | User | This is the development and initial integration target |
| 2026-04-15 | Authentication scope for v1 | No auth for the prototype; session-based behavior only | User | Reduces scope for the hackathon build |
| 2026-04-16 | Public deployment and model runtime topology | Deploy the React frontend on a static host, and deploy `FastAPI` plus private host-local `Ollama` together on one GPU-backed Linux host with persistent model storage | User | Chosen live deployment path for the hackathon submission |

## Pending future decisions

- Production MongoDB hosting target
- Final GPU provider and cost ceiling for the public demo
- Whether to add a separate cache layer once retrieval latency is measured
