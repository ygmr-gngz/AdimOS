from fastapi import APIRouter, HTTPException
from app.schemas.crm import LeadCreate, LeadUpdate
from app.modules.crm.service import add_lead, list_leads, fetch_lead, modify_lead, remove_lead, get_lead_score
from app.modules.crm.followup import get_leads_needing_followup

router = APIRouter()


@router.post("")
def create_lead(data: LeadCreate):
    lead = add_lead(data)
    try:
        from app.api.routes.notifications import push_notification
        push_notification("crm", f"Yeni lead: {data.name}", f"Kaynak: {data.source or '—'} | Durum: {data.status.value}")
    except Exception:
        pass
    return lead


@router.get("")
def get_leads():
    return list_leads()


@router.get("/followup")
def followup_leads():
    return get_leads_needing_followup()


@router.get("/{lead_id}")
def get_lead(lead_id: str):
    lead = fetch_lead(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead bulunamadı")
    return lead


@router.patch("/{lead_id}")
def update_lead(lead_id: str, data: LeadUpdate):
    updated = modify_lead(lead_id, data)
    if not updated:
        raise HTTPException(status_code=404, detail="Lead bulunamadı")
    return updated


@router.delete("/{lead_id}")
def delete_lead(lead_id: str):
    remove_lead(lead_id)
    return {"message": "Lead silindi"}


@router.get("/{lead_id}/score")
def lead_score(lead_id: str):
    return get_lead_score(lead_id)
