from app.db.repositories.leads_repo import get_leads, update_lead


def get_leads_needing_followup() -> list[dict]:
    leads = get_leads()
    return [l for l in leads if l.get("status") in ("new", "contacted")]


def mark_as_contacted(lead_id: str) -> dict | None:
    return update_lead(lead_id, {"status": "contacted"})
