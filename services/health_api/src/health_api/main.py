from __future__ import annotations

import os
from datetime import date

from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from vytallink_health_kit.application.use_cases import (
    BuildReadinessReportInput,
    BuildReadinessReportUseCase,
)
from health_api.patient_registry import PATIENT_REGISTRY
from health_api.patient_summary import PatientListItem, build_patient_summary
from health_api.stub_provider import StubHealthDataProvider

# ---------------------------------------------------------------------------
# Live provider (only instantiated when USE_STUB=false)
#
# USE_STUB=true  → offline stub data, no VytalLink required (default)
# USE_STUB=false → live VytalLink (requires VYTALLINK_BASE_URL, VYTALLINK_WORD, VYTALLINK_CODE)
#
# Example:
#   USE_STUB=true  uv run uvicorn health_api.main:app --reload --port 8008
#   USE_STUB=false uv run uvicorn health_api.main:app --reload --port 8008
# ---------------------------------------------------------------------------
_USE_STUB = os.getenv("USE_STUB", "true").lower() == "true"

if _USE_STUB:
    _live_provider = StubHealthDataProvider(patient_id="demo-1")
else:
    from vytallink_health_kit.infrastructure.settings import load_vytallink_settings
    from vytallink_health_kit.infrastructure.vytallink_client import VytalLinkRESTClient
    _live_provider = VytalLinkRESTClient(settings=load_vytallink_settings())

app = FastAPI(title="Clinical Risk Copilot API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _active_patients():
    """Patients visible in the current mode.

    USE_STUB=false → only live_or_stub patients (real devices only).
    USE_STUB=true  → all patients (full demo set).
    """
    if _USE_STUB:
        return list(PATIENT_REGISTRY.values())
    return [p for p in PATIENT_REGISTRY.values() if p.data_mode == "live_or_stub"]


@app.get("/api/patients")
def list_patients():
    """Return active patients with their current status. Sorted by severity."""
    items: list[PatientListItem] = []
    for patient in _active_patients():
        provider = (
            _live_provider
            if patient.data_mode == "live_or_stub"
            else StubHealthDataProvider(patient_id=patient.patient_id)
        )
        use_case = BuildReadinessReportUseCase(health_data_provider=provider)
        health_data = provider.fetch_window(end_date=date.today(), days=7)
        report = use_case.execute(
            BuildReadinessReportInput(end_date=date.today(), days=7, include_narrative=False)
        )
        summary = build_patient_summary(
            patient_id=patient.patient_id,
            patient_name=patient.name,
            report=report,
            health_data=health_data,
        )
        items.append(
            PatientListItem(
                patientId=summary.patientId,
                patientName=summary.patientName,
                status=summary.status,
                updatedAt=summary.updatedAt,
            )
        )

    _severity = {"review_soon": 0, "follow_up": 1, "monitor": 2}
    items.sort(key=lambda x: _severity[x.status])
    return [item.model_dump() for item in items]


@app.get("/api/patients/{patient_id}/summary")
def get_patient_summary(patient_id: str):
    """Normalized patient summary. Unknown patient_id → 404."""
    patient = PATIENT_REGISTRY.get(patient_id)
    if patient is None or (not _USE_STUB and patient.data_mode != "live_or_stub"):
        raise HTTPException(status_code=404, detail=f"Patient '{patient_id}' not found.")

    # live_or_stub: respects USE_STUB env var (live VytalLink or demo-1 stub)
    # stub: always uses the patient-specific fixture regardless of USE_STUB
    if patient.data_mode == "live_or_stub":
        provider = _live_provider
    else:
        provider = StubHealthDataProvider(patient_id=patient_id)

    use_case = BuildReadinessReportUseCase(health_data_provider=provider)
    health_data = provider.fetch_window(end_date=date.today(), days=7)
    report = use_case.execute(
        BuildReadinessReportInput(
            end_date=date.today(),
            days=7,
            include_narrative=False,
        )
    )
    return build_patient_summary(
        patient_id=patient.patient_id,
        patient_name=patient.name,
        report=report,
        health_data=health_data,
    ).model_dump()


@app.get("/api/readiness")
def get_readiness(days: int = 7):
    """Raw readiness report (internal). Source depends on USE_STUB env var."""
    use_case = BuildReadinessReportUseCase(health_data_provider=_live_provider)
    report = use_case.execute(
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


_frontend = Path(__file__).parent.parent.parent / "frontend"
if _frontend.exists():
    app.mount("/", StaticFiles(directory=str(_frontend), html=True), name="frontend")


def run():
    uvicorn.run("health_api.main:app", host="0.0.0.0", port=8008, reload=True)


if __name__ == "__main__":
    run()
