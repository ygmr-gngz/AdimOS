from datetime import datetime, timezone

from app.modules.publishing.service import next_slot


def test_next_slot_uses_trt_publish_hours() -> None:
    now = datetime(2026, 8, 22, 5, 30, tzinfo=timezone.utc)  # TRT 08:30
    assert next_slot(now, []) == datetime(2026, 8, 22, 6, 0, tzinfo=timezone.utc)


def test_next_slot_respects_four_hour_gap() -> None:
    now = datetime(2026, 8, 22, 5, 30, tzinfo=timezone.utc)
    rows = [{"scheduled_at": "2026-08-22T06:00:00+00:00", "published_at": None}]
    assert next_slot(now, rows) == datetime(2026, 8, 22, 10, 0, tzinfo=timezone.utc)


def test_next_slot_moves_after_daily_limit() -> None:
    now = datetime(2026, 8, 22, 5, 30, tzinfo=timezone.utc)
    rows = [
        {"scheduled_at": f"2026-08-22T{hour:02d}:00:00+00:00", "published_at": None}
        for hour in (6, 10, 16)
    ]
    assert next_slot(now, rows) == datetime(2026, 8, 23, 6, 0, tzinfo=timezone.utc)
