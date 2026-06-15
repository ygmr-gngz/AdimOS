from app.modules.dashboard.brief_generator import generate_daily_brief
from app.modules.crm.followup import get_leads_needing_followup


def task_daily_brief() -> dict:
    return generate_daily_brief()


def task_followup_check() -> dict:
    leads = get_leads_needing_followup()
    return {"leads_needing_followup": len(leads), "leads": leads}
