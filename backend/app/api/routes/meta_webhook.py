"""Meta / Instagram webhook endpoint'leri.

GET  /meta/webhook  — Meta doğrulama challenge
POST /meta/webhook  — Instagram DM eventleri
POST /meta/test-dm-flow — Gerçek Instagram'a göndermeden test
GET  /meta/conversations — Panel için konuşma listesi
GET  /meta/messages/{instagram_user_id} — Konuşma mesajları
POST /meta/send — Manuel mesaj gönder
"""
import logging
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from app.core.config import settings
from app.modules.instagram.dm_service import (
    process_incoming_dm, send_instagram_message, match_flow,
)
from app.db.supabase import get_supabase_client
from app.config.instagram_dm_flows import WELCOME_MESSAGE, FALLBACK_MESSAGE

logger = logging.getLogger(__name__)
router = APIRouter()           # Public — Meta'nın çağırdığı endpoint'ler
protected_router = APIRouter() # Protected — panel endpoint'leri


# ── GET /meta/webhook — Meta doğrulama ───────────────────────

@router.get("/webhook")
async def meta_verify(request: Request):
    """Meta Developers → Webhook → Callback URL doğrulaması."""
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    logger.info(
        f"[meta] webhook doğrulama isteği — "
        f"mode={mode} "
        f"verify_token={token} "
        f"env_token={settings.META_VERIFY_TOKEN!r}"
    )

    if mode == "subscribe" and token == settings.META_VERIFY_TOKEN:
        logger.info("[meta] webhook doğrulandı ✓")
        return PlainTextResponse(challenge)

    logger.warning(
        f"[meta] webhook doğrulama BAŞARISIZ — "
        f"token eşleşmiyor: gelen={token!r} beklenen={settings.META_VERIFY_TOKEN!r}"
    )
    raise HTTPException(status_code=403, detail="Verify token hatalı")


# ── POST /meta/webhook — Instagram eventleri ─────────────────

@router.post("/webhook")
async def meta_webhook(request: Request):
    """Instagram DM, comment vb. eventleri işle."""
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="JSON parse hatası")

    if body.get("object") not in ("instagram", "page"):
        return {"status": "ignored", "reason": "object not instagram/page"}

    for entry in body.get("entry", []):
        for messaging in entry.get("messaging", []):
            sender_id = messaging.get("sender", {}).get("id")
            recipient_id = messaging.get("recipient", {}).get("id")
            timestamp = messaging.get("timestamp", 0)
            message = messaging.get("message", {})
            message_id = message.get("mid", "")
            message_text = message.get("text", "")

            if not sender_id or not message_text or not message_id:
                continue

            # Arka planda işle (webhook hızlı 200 dönmeli)
            try:
                process_incoming_dm(
                    sender_id=sender_id,
                    recipient_id=recipient_id,
                    message_text=message_text,
                    message_id=message_id,
                    timestamp=timestamp,
                    raw_payload=messaging,
                )
            except Exception as e:
                logger.error(f"[meta] DM işlenemedi: {e}", exc_info=True)

    return {"status": "ok"}


# ── POST /meta/test-dm-flow — Test (Protected) ───────────────

class TestDmRequest(BaseModel):
    sender_id: str = "test_user_001"
    message_text: str


@protected_router.post("/test-dm-flow")
def test_dm_flow(req: TestDmRequest):
    """Gerçek Instagram'a göndermeden hangi cevabın üretileceğini test et."""
    flow = match_flow(req.message_text)
    if flow:
        reply = flow["response"]
        crm_status = flow.get("crm_status")
        crm_interest = flow.get("crm_interest")
    else:
        # İlk mesaj gibi davran
        from app.db.supabase import get_supabase_client
        try:
            sb = get_supabase_client()
            conv = sb.table("instagram_conversations").select("current_step").eq("instagram_user_id", req.sender_id).execute()
            step = conv.data[0]["current_step"] if conv.data else "init"
        except Exception:
            step = "init"

        if step == "init":
            reply = WELCOME_MESSAGE
            crm_status = None
            crm_interest = None
        else:
            reply = FALLBACK_MESSAGE
            crm_status = None
            crm_interest = None

    return {
        "sender_id": req.sender_id,
        "message_text": req.message_text,
        "matched_flow": flow["keywords"][0] if flow else None,
        "reply": reply,
        "crm_status": crm_status,
        "crm_interest": crm_interest,
        "would_create_crm_lead": bool(crm_status),
    }


# ── GET /meta/conversations — Panel konuşma listesi ──────────

@protected_router.get("/conversations")
def list_conversations():
    try:
        supabase = get_supabase_client()
        resp = (
            supabase.table("instagram_conversations")
            .select("*")
            .order("last_message_at", desc=True)
            .execute()
        )
        return resp.data if resp.data else []
    except Exception as e:
        logger.warning(f"[meta] konuşmalar alınamadı: {e}")
        return []


# ── GET /meta/messages/{id} — Konuşma mesajları ──────────────

@protected_router.get("/messages/{instagram_user_id}")
def get_conversation_messages(instagram_user_id: str):
    try:
        supabase = get_supabase_client()
        resp = (
            supabase.table("instagram_messages")
            .select("*")
            .or_(f"sender_id.eq.{instagram_user_id},recipient_id.eq.{instagram_user_id}")
            .order("created_at")
            .execute()
        )
        return resp.data if resp.data else []
    except Exception as e:
        logger.warning(f"[meta] mesajlar alınamadı: {e}")
        return []


# ── POST /meta/send — Manuel mesaj gönder ────────────────────

class SendMessageRequest(BaseModel):
    instagram_user_id: str
    text: str


@protected_router.post("/send")
def send_manual_message(req: SendMessageRequest):
    ok = send_instagram_message(req.instagram_user_id, req.text)
    if not ok:
        raise HTTPException(status_code=502, detail="Mesaj gönderilemedi")
    return {"status": "sent"}
