from __future__ import annotations

import os
from datetime import date

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from vytallink_health_kit.application.use_cases import (
    BuildReadinessReportInput,
    BuildReadinessReportUseCase,
)
from health_api.stub_provider import StubHealthDataProvider

# ---------------------------------------------------------------------------
# Data provider selection
#
# USE_STUB=true  → offline demo data, no VytalLink required (default)
# USE_STUB=false → live VytalLink (requires VYTALLINK_BASE_URL, VYTALLINK_WORD, VYTALLINK_CODE)
#
# Example:
#   USE_STUB=true  uv run uvicorn health_api.main:app --reload --port 8008
#   USE_STUB=false uv run uvicorn health_api.main:app --reload --port 8008
# ---------------------------------------------------------------------------
_USE_STUB = os.getenv("USE_STUB", "true").lower() == "true"

if _USE_STUB:
    _provider = StubHealthDataProvider()
else:
    from vytallink_health_kit.infrastructure.settings import load_vytallink_settings
    from vytallink_health_kit.infrastructure.vytallink_client import VytalLinkRESTClient
    _provider = VytalLinkRESTClient(settings=load_vytallink_settings())

app = FastAPI(title="Clinical Risk Copilot API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_use_case = BuildReadinessReportUseCase(health_data_provider=_provider)


@app.get("/api/readiness")
def get_readiness(days: int = 7):
    """Return readiness report. Source depends on USE_STUB env var."""
    report = _use_case.execute(
        BuildReadinessReportInput(
            end_date=date.today(),
            days=days,
            include_narrative=False,
        )
    )
    return report.model_dump()


@app.get("/health")
def health():
    return {"status": "ok", "stub_mode": _USE_STUB}


def run():
    uvicorn.run("health_api.main:app", host="0.0.0.0", port=8008, reload=True)


if __name__ == "__main__":
    run()
