# Clinical Risk Copilot

Hackathon MVP that turns wearable data into simple patient monitoring signals.

## Scope
- Patient list
- Patient dashboard
- Deterministic signal classification
- Optional AI narrative
- Demo/stub mode

## Tech
- Frontend: TBD
- Backend: Python
- Data source: VytalLink

## Quick Start

```bash
cd services/health_api
uv sync
uv run uvicorn health_api.main:app --reload --port 8008
```

API available at `http://localhost:8008`.

## Data Source Toggle

The backend supports two modes controlled by the `USE_STUB` env var.

| `USE_STUB` | Behavior |
|---|---|
| `true` (default) | Offline demo data — no VytalLink required |
| `false` | Live VytalLink — requires credentials |

```bash
# Stub mode (default)
USE_STUB=true uv run uvicorn health_api.main:app --reload --port 8008

# Live mode
USE_STUB=false uv run uvicorn health_api.main:app --reload --port 8008
```

Live mode reads VytalLink credentials from `vytallink-health-kit/.env` automatically — no duplication needed.

## Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/api/readiness` | Readiness report (sleep, HR, steps, score) |
| GET | `/health` | Health check — shows current mode |
| GET | `/docs` | Swagger UI |
