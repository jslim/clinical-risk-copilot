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

| `USE_STUB` | Behavior | Patients | Data |
|---|---|---|---|
| `true` (default) | Offline demo data — no VytalLink required | demo-1, demo-2, demo-3 | Fixed fixtures |
| `false` | Live VytalLink — requires credentials | demo-1 only | Real wearable data |

```bash
# Stub mode (default) — offline, three demo scenarios
USE_STUB=true uv run uvicorn health_api.main:app --reload --port 8008

# Live mode — real data from VytalLink
USE_STUB=false uv run uvicorn health_api.main:app --reload --port 8008
```

### Live Mode: VytalLink Credentials

Live mode reads credentials from `.env` in this directory (`services/health_api/.env`).

**Using testmode (synthetic data for hackathon):**
```bash
# .env file
VYTALLINK_BASE_URL="https://vytallink.local.xmartlabs.com"
VYTALLINK_WORD="testmode"
VYTALLINK_CODE="999999"
VYTALLINK_API_MODE="auto"
```

Then run:
```bash
USE_STUB=false uv run uvicorn health_api.main:app --reload --port 8008
```

Patient `demo-1` (Jane Doe) will show live synthetic wearable data: sleep stages, resting HR, steps — all updated from the VytalLink API.

### Stub Mode: Demo Scenarios

When `USE_STUB=true`, three demo patients are available with fixed data representing different risk tiers:

| Patient | Name | Status | Use Case |
|---|---|---|---|
| `demo-1` | Jane Doe | `monitor` | Healthy baseline — good sleep, stable HR, normal load |
| `demo-2` | Robert Chen | `follow_up` | Mild concerns — slight sleep disruption or elevated HR trend |
| `demo-3` | Maria Santos | `review_soon` | High priority — poor sleep, rising HR, elevated load |

Perfect for UI development, client demos, and testing the full three-tier risk classification.

## Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/api/patients` | List all active patients with status (sorted by risk severity) |
| GET | `/api/patients/{patient_id}/summary` | Detailed summary: metrics, signals, warnings, narrative |
| GET | `/api/readiness` | Raw readiness report (internal debug) |
| GET | `/health` | Health check — shows current mode (`stub_mode: true/false`) |
| GET | `/docs` | Swagger UI |
