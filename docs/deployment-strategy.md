# Deployment Strategy

## Goal

Make the hackathon's `live deployed app` requirement realistic for an open-source model stack instead of assuming the backend can keep depending on a developer laptop.

## Recommended live deployment

### Frontend

- Deploy the React frontend as a static site on a commodity frontend host such as Vercel or Netlify.
- Point `VITE_API_BASE_URL` at the public FastAPI endpoint.

### Backend and model runtime

- Deploy FastAPI and Ollama together on a single GPU-backed Linux host.
- Preferred demo path: one GPU Pod or VM with persistent storage, using a container-based deployment.
- Keep FastAPI public and keep Ollama private on the same machine, bound to the local network path used by the backend.

### Preferred topology

```txt
Browser
  -> Static frontend host
  -> HTTPS FastAPI API
       -> local Ollama runtime on same GPU host
       -> MongoDB
       -> external research APIs
```

### Why this is the preferred topology

- It satisfies the `live deployed` requirement without relying on the developer's local GPU being online.
- It avoids shipping model traffic over the public internet between FastAPI and Ollama.
- It keeps model warmup, GPU memory, and restart behavior on one machine.
- It allows the frontend to stay cheap and separately deployable.

## Concrete implementation plan

### GPU host

- Use one GPU host for the backend and Ollama runtime.
- Mount persistent storage for model files so `gemma4:e4b` does not need to be re-pulled on every restart.
- Run a startup step that verifies the target model is present before the API is marked ready.
- Expose only FastAPI publicly; keep Ollama internal to the host.

### Process model

- Run one FastAPI process per GPU host for the model-serving path.
- Do not scale FastAPI workers on the same machine by default while Ollama is sharing the same GPU memory budget.
- Scale horizontally later with additional GPU hosts only after latency and memory are measured.

### Containers

- Package FastAPI into a Linux container image.
- Run Ollama as a sibling service on the same host or as part of the same compose stack.
- Use a container orchestrator or provider startup mechanism for restarts and boot-time recovery.

### Persistent data

- Persist Ollama model storage on a provider volume.
- Persist MongoDB separately from the GPU runtime.
- Persist application logs and request traces outside the container filesystem.

## Hackathon-ready deployment modes

### Preferred submission mode

- Frontend on a static host
- FastAPI + Ollama on a GPU Pod/VM with persistent volume
- MongoDB on a managed cluster or separate VM

### Fallback demo mode

- Local GPU with Ollama plus a secure tunnel for the API
- Acceptable only as an emergency demo fallback
- Not the intended final interpretation of `live deployed`

## Operational notes

- Readiness must fail if Ollama is unreachable or the target model is unavailable.
- Health checks should distinguish API liveness from model readiness.
- If a provider restart happens, the platform must restart FastAPI automatically and preserve model files on mounted storage.

## Sources

- FastAPI deployment concepts: https://fastapi.tiangolo.com/deployment/concepts/
- FastAPI in containers: https://fastapi.tiangolo.com/deployment/docker/
- Ollama API base URL and runtime model access: https://docs.ollama.com/api
- Runpod Pods overview: https://docs.runpod.io/pods
- Runpod storage options: https://docs.runpod.io/pods/storage/sync-volumes
