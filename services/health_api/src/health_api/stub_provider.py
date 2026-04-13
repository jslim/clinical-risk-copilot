"""Stub health data provider — lives in clinical-risk-copilot, not in vytallink-health-kit.

Each patient ID maps to a distinct scenario designed to produce a specific clinical status:
  demo-1 → monitor   (healthy baseline, strong sleep, stable HR, balanced activity)
  demo-2 → follow_up (mild sleep disruption, one threshold warning)
  demo-3 → review_soon (poor sleep, rising HR trend, elevated recent activity load)
"""

from __future__ import annotations

from datetime import date, timedelta

from vytallink_health_kit.domain.entities import (
    ActivityRecord,
    HealthData,
    HRRecord,
    SleepRecord,
)

# ---------------------------------------------------------------------------
# Per-patient fixture data
# Each tuple: (sleep_total_min, deep_min, rem_min, awake_min, hr_bpm, steps)
# All lists are 7 days, oldest first.
# ---------------------------------------------------------------------------

_FIXTURES: dict[str, dict[str, list]] = {
    # monitor: sleep efficiency ~96% on last day, flat HR trend, balanced load
    "demo-1": {
        "sleep": [440, 395, 460, 420, 380, 410, 445],
        "deep":  [85,  70,  95,  80,  60,  75,  90],
        "rem":   [90,  80, 100,  85,  70,  88,  95],
        "awake": [20,  30,  15,  25,  35,  22,  18],
        "hr":    [54.0, 56.0, 53.0, 55.0, 58.0, 54.0, 52.0],
        "steps": [8200, 6500, 9800, 7100, 4200, 8800, 10200],
    },
    # follow_up: last-day sleep efficiency ~83% → 1 warning → follow_up
    # HR trend ~+0.18 bpm/day (below 0.5 threshold, no extra warning)
    # Load ratio ~1.01 (balanced, no warning)
    "demo-2": {
        "sleep": [380, 360, 370, 355, 365, 375, 340],
        "deep":  [75,  70,  80,  65,  70,  75,  60],
        "rem":   [80,  75,  85,  70,  75,  80,  65],
        "awake": [55,  60,  50,  65,  55,  50,  70],
        "hr":    [63.0, 63.5, 64.0, 64.0, 63.5, 64.0, 64.5],
        "steps": [7000, 6800, 7200, 7100, 6900, 7300, 7100],
    },
    # review_soon: 3 concurrent warnings
    #   1. last-day sleep efficiency ~83% (< 85%)
    #   2. HR trend +1.36 bpm/day (> 0.5 and > 1.0)
    #   3. load ratio ~2.5x (> 1.5)
    # Also triggers the hr_trend > 1.0 AND load_ratio > 1.5 review_soon rule.
    "demo-3": {
        "sleep": [290, 310, 280, 300, 270, 295, 285],
        "deep":  [55,  60,  50,  60,  45,  55,  50],
        "rem":   [65,  70,  60,  70,  55,  65,  60],
        "awake": [55,  50,  60,  50,  65,  55,  60],
        "hr":    [60.0, 61.0, 63.0, 64.0, 65.0, 67.0, 68.0],
        "steps": [3000, 4000, 3500, 5000, 9000, 10000, 11000],
    },
}

_DEFAULT_FIXTURE = "demo-1"


class StubHealthDataProvider:
    """Returns deterministic demo data without hitting VytalLink.

    Pass patient_id to select the scenario fixture. Unknown IDs fall back to demo-1.
    """

    def __init__(self, patient_id: str = "demo-1") -> None:
        self._fixture = _FIXTURES.get(patient_id, _FIXTURES[_DEFAULT_FIXTURE])

    def fetch_window(self, *, end_date: date, days: int) -> HealthData:
        window = [end_date - timedelta(days=offset) for offset in range(days - 1, -1, -1)]

        f = self._fixture
        sleep_map, hr_map, activity_map = {}, {}, {}

        for i, day in enumerate(window):
            key = day.isoformat()
            idx = i % 7
            total = f["sleep"][idx]
            deep = f["deep"][idx]
            rem = f["rem"][idx]
            awake = f["awake"][idx]
            sleep_map[key] = SleepRecord(
                date=day,
                total_minutes=total,
                deep_minutes=deep,
                rem_minutes=rem,
                light_minutes=total - deep - rem - awake,
                awake_minutes=awake,
            )
            hr_map[key] = HRRecord(date=day, resting_bpm=f["hr"][idx])
            steps = f["steps"][idx]
            activity_map[key] = ActivityRecord(
                date=day,
                steps=steps,
                active_calories=steps // 20,
                exercise_minutes=30 + (i * 5) % 25,
            )

        return HealthData(days=window, sleep=sleep_map, heart_rate=hr_map, activity=activity_map)
