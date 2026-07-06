import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from app.modules.automation.tasks import task_daily_brief, task_followup_check

logger = logging.getLogger(__name__)
_scheduler = BackgroundScheduler()


def _task_video_cleanup():
    """Video pipeline haftalık temizlik — takılı ve eski başarısız işleri arşivle."""
    try:
        from app.db.supabase import get_supabase_client
        from datetime import datetime, timezone, timedelta
        sb = get_supabase_client()
        now = datetime.now(timezone.utc)
        stale_threshold = (now - timedelta(hours=4)).isoformat()
        old_threshold = (now - timedelta(days=7)).isoformat()

        stuck = (
            sb.table("video_jobs")
            .select("id, status, updated_at")
            .in_("status", ["scripting", "tts_generating", "warmup_pinging", "rendering", "pending"])
            .lt("updated_at", stale_threshold)
            .execute().data or []
        )
        old_failed = (
            sb.table("video_jobs")
            .select("id, status, updated_at")
            .eq("status", "failed")
            .lt("updated_at", old_threshold)
            .execute().data or []
        )
        archived_at = now.isoformat()
        all_ids = [j["id"] for j in stuck] + [j["id"] for j in old_failed]
        if all_ids:
            sb.table("video_jobs").update({
                "status": "archived",
                "archived_at": archived_at,
            }).in_("id", all_ids).execute()
            logger.info(f"[scheduler] video_cleanup: {len(all_ids)} iş arşivlendi (takılı={len(stuck)}, eski_hata={len(old_failed)})")
        else:
            logger.info("[scheduler] video_cleanup: temizlenecek iş yok")
    except Exception as e:
        logger.error(f"[scheduler] video_cleanup hatası: {e}", exc_info=True)


def _task_video_watchdog():
    """30 dakikayı aşan işleri failed'a taşı — her 15 dakikada bir."""
    try:
        from app.api.routes.video import _watchdog_sweep
        _watchdog_sweep()
    except Exception as e:
        logger.error(f"[scheduler] video_watchdog hatası: {e}")


def start_scheduler():
    _scheduler.add_job(task_daily_brief, CronTrigger(hour=8, minute=0), id="daily_brief", replace_existing=True)
    _scheduler.add_job(task_followup_check, CronTrigger(hour=9, minute=0), id="followup_check", replace_existing=True)
    # Haftalık video pipeline temizliği — Pazartesi 03:00
    _scheduler.add_job(
        _task_video_cleanup,
        CronTrigger(day_of_week="mon", hour=3, minute=0),
        id="video_cleanup_weekly",
        replace_existing=True,
    )
    # Video watchdog — her 15 dakikada bir (list_jobs'tan kaldırıldı)
    _scheduler.add_job(
        _task_video_watchdog,
        "interval",
        minutes=15,
        id="video_watchdog",
        replace_existing=True,
    )
    if not _scheduler.running:
        _scheduler.start()


def stop_scheduler():
    if _scheduler.running:
        _scheduler.shutdown()


def get_jobs() -> list[dict]:
    return [
        {"id": job.id, "next_run": str(job.next_run_time)}
        for job in _scheduler.get_jobs()
    ]
