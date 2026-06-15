from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from app.modules.automation.tasks import task_daily_brief, task_followup_check

_scheduler = BackgroundScheduler()


def start_scheduler():
    _scheduler.add_job(task_daily_brief, CronTrigger(hour=8, minute=0), id="daily_brief", replace_existing=True)
    _scheduler.add_job(task_followup_check, CronTrigger(hour=9, minute=0), id="followup_check", replace_existing=True)
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
