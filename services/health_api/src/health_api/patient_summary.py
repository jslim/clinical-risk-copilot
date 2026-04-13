"""Adapter layer: maps raw VytalLink/readiness data → normalized PatientSummary.

This module is the only place that knows about both the internal readiness
domain and the product-facing API contract. Keep it thin.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel

from vytallink_health_kit.domain.entities import HealthData
from vytallink_health_kit.domain.readiness import DailyReadiness, ReadinessReport


# ---------------------------------------------------------------------------
# Response model
# ---------------------------------------------------------------------------

class PatientListItem(BaseModel):
    patientId: str
    patientName: str
    status: Literal["monitor", "follow_up", "review_soon"]
    updatedAt: str


class MetricsSummary(BaseModel):
    sleepHoursAvg: float | None
    restingHrAvg: float | None
    stepsAvg: float | None


class PatientSummary(BaseModel):
    patientId: str
    patientName: str
    status: Literal["monitor", "follow_up", "review_soon"]
    updatedAt: str
    metrics: MetricsSummary
    signals: list[str]
    insight: str
    warnings: list[str]


# ---------------------------------------------------------------------------
# Deterministic classification
# ---------------------------------------------------------------------------

def classify_status(readiness: DailyReadiness) -> Literal["monitor", "follow_up", "review_soon"]:
    """Return patient status based on readiness metrics. First match wins."""
    score = readiness.readiness_score
    hr_trend = readiness.resting_hr_trend
    load = readiness.load_ratio
    n_warnings = len(readiness.warnings)

    # review_soon: strongest signal combinations
    if score is not None and score < 50:
        return "review_soon"
    if hr_trend is not None and hr_trend > 1.0 and load is not None and load > 1.5:
        return "review_soon"
    if n_warnings >= 3:
        return "review_soon"

    # follow_up: relevant changes detected
    if score is not None and score < 70:
        return "follow_up"
    if n_warnings >= 1:
        return "follow_up"

    return "monitor"


# ---------------------------------------------------------------------------
# Deterministic signal generation
# ---------------------------------------------------------------------------

def generate_signals(readiness: DailyReadiness) -> list[str]:
    """Return short observation bullets derived from DailyReadiness fields."""
    signals: list[str] = []

    if readiness.sleep_efficiency_pct is not None:
        pct = readiness.sleep_efficiency_pct
        if pct >= 90:
            signals.append("Sleep efficiency strong")
        elif pct >= 85:
            signals.append("Sleep efficiency adequate")
        else:
            signals.append(f"Sleep efficiency low ({pct:.0f}%)")

    if readiness.resting_hr_trend is not None:
        trend = readiness.resting_hr_trend
        if trend <= 0:
            signals.append("Resting HR stable or improving")
        elif trend <= 0.5:
            signals.append("Resting HR slightly elevated trend")
        else:
            signals.append(f"Resting HR trending up ({trend:+.2f} bpm/day)")

    if readiness.load_ratio is not None:
        ratio = readiness.load_ratio
        if 0.8 <= ratio <= 1.2:
            signals.append("Activity load balanced")
        elif ratio > 1.5:
            signals.append(f"Activity load elevated ({ratio:.1f}x baseline)")
        elif ratio < 0.6:
            signals.append(f"Activity load well below baseline ({ratio:.1f}x)")

    if readiness.data_gaps:
        signals.append(f"{len(readiness.data_gaps)} day(s) with missing data")

    return signals


# ---------------------------------------------------------------------------
# Metric averages from raw health data
# ---------------------------------------------------------------------------

def compute_metrics(health_data: HealthData) -> MetricsSummary:
    """Compute 7-day averages. Days with None values are excluded, not zeroed."""
    sleep_hours = [
        s.total_minutes / 60
        for s in health_data.sleep.values()
        if s.total_minutes is not None
    ]
    hr_values = [
        h.resting_bpm
        for h in health_data.heart_rate.values()
        if h.resting_bpm is not None
    ]
    steps_values = [
        a.steps
        for a in health_data.activity.values()
        if a.steps is not None
    ]

    return MetricsSummary(
        sleepHoursAvg=round(sum(sleep_hours) / len(sleep_hours), 1) if sleep_hours else None,
        restingHrAvg=round(sum(hr_values) / len(hr_values), 1) if hr_values else None,
        stepsAvg=round(sum(steps_values) / len(steps_values)) if steps_values else None,
    )


# ---------------------------------------------------------------------------
# Main builder
# ---------------------------------------------------------------------------

def build_patient_summary(
    *,
    patient_id: str,
    patient_name: str,
    report: ReadinessReport,
    health_data: HealthData,
) -> PatientSummary:
    """Map internal readiness domain objects to the product-facing PatientSummary."""
    readiness = report.readiness
    return PatientSummary(
        patientId=patient_id,
        patientName=patient_name,
        status=classify_status(readiness),
        updatedAt=datetime.now(timezone.utc).isoformat(),
        metrics=compute_metrics(health_data),
        signals=generate_signals(readiness),
        insight=report.narrative,
        warnings=readiness.warnings,
    )
