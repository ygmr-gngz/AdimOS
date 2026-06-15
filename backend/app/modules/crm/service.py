from app.db.repositories.leads_repo import create_lead, get_leads, get_lead, update_lead, delete_lead
from app.modules.crm.lead_scoring import score_lead
from app.schemas.crm import LeadCreate, LeadUpdate


def add_lead(data: LeadCreate) -> dict:
    return create_lead(data.name, data.email, data.phone, data.status.value)


def list_leads() -> list[dict]:
    return get_leads()


def fetch_lead(lead_id: str) -> dict | None:
    return get_lead(lead_id)


def modify_lead(lead_id: str, data: LeadUpdate) -> dict | None:
    updates = data.model_dump(exclude_none=True)
    if "status" in updates:
        updates["status"] = updates["status"].value
    return update_lead(lead_id, updates)


def remove_lead(lead_id: str) -> list[dict]:
    return delete_lead(lead_id)


def get_lead_score(lead_id: str) -> dict:
    lead = get_lead(lead_id)
    if not lead:
        return {"score": 0, "reason": "Lead bulunamadı"}
    return score_lead(lead)
