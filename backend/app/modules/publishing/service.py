from __future__ import annotations

import logging
from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from app.db.supabase import get_supabase_client

logger = logging.getLogger(__name__)
TRT = ZoneInfo("Europe/Istanbul")
PUBLISH_HOURS = (9, 13, 19)
MAX_DAILY_PER_PLATFORM = 3
MIN_PLATFORM_GAP = timedelta(hours=4)


def _targets(job: dict, selections: dict[str, bool]) -> list[dict]:
    package = job.get("publish_package") or {}
    rows: list[dict] = []
    if selections.get("youtube_shorts") and job.get("video_url"):
        rows.append({"platform": "youtube", "content_type": "video", "asset_urls": [job["video_url"]]})
    if selections.get("instagram_reels") and job.get("video_url"):
        rows.append({"platform": "instagram_reels", "content_type": "video", "asset_urls": [job["video_url"]]})
    if selections.get("instagram_carousel") and package.get("card_stills"):
        rows.append({"platform": "instagram_post", "content_type": "carousel", "asset_urls": package["card_stills"]})
    if selections.get("instagram_single_image") and package.get("summary_post"):
        rows.append({"platform": "instagram_post", "content_type": "single_image", "asset_urls": [package["summary_post"]]})
    return rows


def enqueue_job(job: dict, selections: dict[str, bool]) -> list[dict]:
    rows = _targets(job, selections)
    if not rows:
        raise ValueError("Seçilen platformlar için yayınlanabilir varlık bulunamadı")
    sb = get_supabase_client()
    payload = [{
        **row,
        "job_id": job["id"],
        "publish_package": job.get("publish_package") or {},
        "status": "pending",
    } for row in rows]
    result = sb.table("publishing_queue").upsert(
        payload, on_conflict="job_id,platform,content_type"
    ).execute()
    return result.data or []


def next_slot(now: datetime, platform_rows: list[dict]) -> datetime:
    local_now = now.astimezone(TRT)
    published = [datetime.fromisoformat(r["published_at"].replace("Z", "+00:00")) for r in platform_rows if r.get("published_at")]
    scheduled = [datetime.fromisoformat(r["scheduled_at"].replace("Z", "+00:00")) for r in platform_rows if r.get("scheduled_at")]
    occupied = published + scheduled
    candidate_day = local_now.date()
    for day_offset in range(0, 30):
        day = candidate_day + timedelta(days=day_offset)
        used_today = [d for d in occupied if d.astimezone(TRT).date() == day]
        for hour in PUBLISH_HOURS:
            candidate = datetime.combine(day, time(hour=hour), tzinfo=TRT)
            if candidate < local_now:
                continue
            if len(used_today) >= MAX_DAILY_PER_PLATFORM:
                break
            if all(abs(candidate.astimezone(timezone.utc) - d.astimezone(timezone.utc)) >= MIN_PLATFORM_GAP for d in occupied):
                return candidate.astimezone(timezone.utc)
    raise RuntimeError("30 gün içinde uygun yayın slotu bulunamadı")


def schedule_pending(now: datetime | None = None) -> int:
    now = now or datetime.now(timezone.utc)
    sb = get_supabase_client()
    pending = sb.table("publishing_queue").select("*").eq("status", "pending").order("created_at").execute().data or []
    count = 0
    for row in pending:
        platform_rows = sb.table("publishing_queue").select("scheduled_at,published_at").eq("platform", row["platform"]).in_("status", ["scheduled", "published"]).execute().data or []
        slot = next_slot(now, platform_rows)
        sb.table("publishing_queue").update({"status": "scheduled", "scheduled_at": slot.isoformat()}).eq("id", row["id"]).eq("status", "pending").execute()
        count += 1
    logger.info("[publishing] %d kayıt zamanlandı", count)
    return count


def _publish(row: dict) -> str:
    if row["platform"] == "youtube":
        from app.integrations.youtube.publisher import publish_queue_item
    else:
        from app.integrations.instagram.publisher import publish_queue_item
    return publish_queue_item(row)


def process_due(now: datetime | None = None) -> int:
    now = now or datetime.now(timezone.utc)
    sb = get_supabase_client()
    due = (
        sb.table("publishing_queue").select("*")
        .eq("status", "scheduled").lte("scheduled_at", now.isoformat())
        .order("scheduled_at").limit(10).execute().data or []
    )
    processed = 0
    for row in due:
        claimed = sb.table("publishing_queue").update({"status": "publishing"}).eq("id", row["id"]).eq("status", "scheduled").execute().data or []
        if not claimed:
            continue
        try:
            external_id = _publish(row)
            sb.table("publishing_queue").update({
                "status": "published", "external_id": external_id,
                "published_at": now.isoformat(), "last_error": None,
            }).eq("id", row["id"]).execute()
        except Exception as exc:
            attempts = int(row.get("attempt_count") or 0) + 1
            status = "failed" if attempts >= 3 else "scheduled"
            sb.table("publishing_queue").update({
                "status": status,
                "attempt_count": attempts,
                "last_error": str(exc)[:1000],
                "scheduled_at": (now + timedelta(minutes=15)).isoformat(),
            }).eq("id", row["id"]).execute()
            logger.error("[publishing] id=%s deneme=%d/3 hata=%s", row["id"], attempts, exc)
        processed += 1
    return processed
