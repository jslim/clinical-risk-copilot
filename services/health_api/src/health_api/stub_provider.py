"""Stub health data provider — lives in clinical-risk-copilot, not in vytallink-health-kit."""

from __future__ import annotations

from datetime import date, timedelta

from vytallink_health_kit.domain.entities import (
    ActivityRecord,
    HealthData,
    HRRecord,
    SleepRecord,
)


class StubHealthDataProvider:
    """Returns realistic demo data without hitting VytalLink."""

    def fetch_window(self, *, end_date: date, days: int) -> HealthData:
        window = [end_date - timedelta(days=offset) for offset in range(days - 1, -1, -1)]

        sleep_data = [440, 395, 460, 420, 380, 410, 445]
        deep_data = [85, 70, 95, 80, 60, 75, 90]
        rem_data = [90, 80, 100, 85, 70, 88, 95]
        awake_data = [20, 30, 15, 25, 35, 22, 18]
        hr_data = [54.0, 56.0, 53.0, 55.0, 58.0, 54.0, 52.0]
        steps_data = [8200, 6500, 9800, 7100, 4200, 8800, 10200]

        sleep_map, hr_map, activity_map = {}, {}, {}

        for i, day in enumerate(window):
            key = day.isoformat()
            total = sleep_data[i % len(sleep_data)]
            deep = deep_data[i % len(deep_data)]
            rem = rem_data[i % len(rem_data)]
            awake = awake_data[i % len(awake_data)]
            sleep_map[key] = SleepRecord(
                date=day,
                total_minutes=total,
                deep_minutes=deep,
                rem_minutes=rem,
                light_minutes=total - deep - rem - awake,
                awake_minutes=awake,
            )
            hr_map[key] = HRRecord(date=day, resting_bpm=hr_data[i % len(hr_data)])
            activity_map[key] = ActivityRecord(
                date=day,
                steps=steps_data[i % len(steps_data)],
                active_calories=steps_data[i % len(steps_data)] // 20,
                exercise_minutes=30 + (i * 5) % 25,
            )

        return HealthData(days=window, sleep=sleep_map, heart_rate=hr_map, activity=activity_map)
