import logging
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from app.core.config import settings
from app.modules.crm.service import add_lead
from app.schemas.crm import LeadCreate, LeadStatus

router = APIRouter()
logger = logging.getLogger(__name__)


class AdimMusavirLead(BaseModel):
    name: str
    email: str
    phone: str | None = None
    message: str | None = None
    form_type: str | None = None


@router.post("/adim-musavir-lead")
async def receive_adim_musavir_lead(
    lead: AdimMusavirLead,
    x_webhook_secret: str | None = Header(default=None),
):
    """adimmusavir.com iletişim formundan gelen lead'i CRM'e kaydet."""
    secret = getattr(settings, "WEBHOOK_SECRET", "")
    if secret:
        if x_webhook_secret != secret:
            logger.warning("[webhook] geçersiz secret, istek reddedildi")
            raise HTTPException(status_code=401, detail="Geçersiz webhook secret")

    notes = lead.message or ""
    if lead.form_type:
        notes = f"Form: {lead.form_type}\n{notes}".strip()

    data = LeadCreate(
        name=lead.name,
        email=lead.email,
        phone=lead.phone,
        status=LeadStatus.NEW,
        source="website",
        notes=notes or None,
    )
    try:
        result = add_lead(data)
        logger.info(f"[webhook] yeni lead kaydedildi email={lead.email}")
        return {"ok": True, "lead_id": result["id"] if result else None}
    except Exception as e:
        logger.error(f"[webhook] lead kayıt hatası: {e}")
        raise HTTPException(status_code=500, detail="Lead kaydedilemedi")
