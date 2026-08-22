from datetime import datetime, timedelta, timezone


def within_reply_window(last_user_message_at: datetime, now: datetime | None = None) -> bool:
    now = now or datetime.now(timezone.utc)
    if last_user_message_at.tzinfo is None:
        last_user_message_at = last_user_message_at.replace(tzinfo=timezone.utc)
    return timedelta(0) <= now - last_user_message_at <= timedelta(hours=24)
