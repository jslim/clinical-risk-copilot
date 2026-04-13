"""Static patient registry for the hackathon MVP.

No database required. Add demo patients here directly.
Each patient has a name and a data_mode that controls which provider is used:
  - "live_or_stub": respects USE_STUB env var (live VytalLink or stub)
  - "stub": always uses stub, ignores USE_STUB
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

DataMode = Literal["live_or_stub", "stub"]


@dataclass(frozen=True)
class PatientRecord:
    patient_id: str
    name: str
    data_mode: DataMode


PATIENT_REGISTRY: dict[str, PatientRecord] = {
    "demo-1": PatientRecord(
        patient_id="demo-1",
        name="Jane Doe",
        data_mode="live_or_stub",  # uses live VytalLink when USE_STUB=false
    ),
    "demo-2": PatientRecord(
        patient_id="demo-2",
        name="Robert Chen",
        data_mode="stub",  # follow_up scenario
    ),
    "demo-3": PatientRecord(
        patient_id="demo-3",
        name="Maria Santos",
        data_mode="stub",  # review_soon scenario
    ),
}
