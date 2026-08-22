from datetime import datetime, timezone
from app.db.supabase import get_supabase_client

UPLOAD_COST = 1600
DAILY_QUOTA = 10_000


def ensure_upload_quota() -> None:
    start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    rows = get_supabase_client().table("publishing_queue").select("id", count="exact").eq("platform", "youtube").eq("status", "published").gte("published_at", start).execute()
    used = int(rows.count or 0) * UPLOAD_COST
    if used + UPLOAD_COST > DAILY_QUOTA:
        raise RuntimeError(f"youtube_quota_exceeded: used={used} next={UPLOAD_COST} limit={DAILY_QUOTA}")
