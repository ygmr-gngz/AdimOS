"""Instagram DM gönderme, alma ve akış yönetimi."""
import logging
import requests
from app.core.config import settings
from app.db.supabase import get_supabase_client
from app.db.repositories.leads_repo import create_lead
from app.config.instagram_dm_flows import WELCOME_MESSAGE, FALLBACK_MESSAGE, FLOWS

logger = logging.getLogger(__name__)

_GRAPH = "https://graph.facebook.com/v21.0"


# ── Mesaj Gönder ──────────────────────────────────────────────

def send_instagram_message(recipient_id: str, text: str) -> bool:
    """Graph API üzerinden Instagram DM gönder."""
    if not settings.INSTAGRAM_DM_ENABLED:
        logger.info("[instagram] DM otomasyonu devre dışı; gönderim atlandı")
        return False

    account_id = settings.INSTAGRAM_BUSINESS_ACCOUNT_ID
    token = settings.META_ACCESS_TOKEN

    try:
        resp = requests.post(
            f"{_GRAPH}/{account_id}/messages",
            json={
                "recipient": {"id": recipient_id},
                "message": {"text": text},
            },
            params={"access_token": token},
            timeout=10,
        )
        data = resp.json()
        if "error" in data:
            logger.error(f"[instagram] mesaj gönderilemedi sender={recipient_id}: {data['error'].get('message')}")
            return False
        logger.info(f"[instagram] mesaj gönderildi → {recipient_id}")
        return True
    except Exception as e:
        logger.error(f"[instagram] send hatası: {e}")
        return False


# ── Veritabanı İşlemleri ──────────────────────────────────────

def is_duplicate_message(message_id: str) -> bool:
    """Aynı message_id daha önce işlendi mi?"""
    try:
        supabase = get_supabase_client()
        resp = supabase.table("instagram_messages").select("id").eq("message_id", message_id).execute()
        return len(resp.data) > 0
    except Exception:
        return False


def save_message(message_id: str, sender_id: str, recipient_id: str,
                 message_text: str, direction: str, raw_payload: dict) -> None:
    try:
        supabase = get_supabase_client()
        supabase.table("instagram_messages").insert({
            "message_id": message_id,
            "sender_id": sender_id,
            "recipient_id": recipient_id,
            "message_text": message_text,
            "direction": direction,
            "raw_payload": raw_payload,
        }).execute()
    except Exception as e:
        logger.warning(f"[instagram] mesaj kaydedilemedi: {e}")


def get_or_create_conversation(instagram_user_id: str) -> dict:
    """Konuşma kaydını getir veya oluştur."""
    try:
        supabase = get_supabase_client()
        resp = supabase.table("instagram_conversations").select("*").eq("instagram_user_id", instagram_user_id).execute()
        if resp.data:
            return resp.data[0]
        # Yeni konuşma
        new_resp = supabase.table("instagram_conversations").insert({
            "instagram_user_id": instagram_user_id,
            "current_step": "init",
            "source": "instagram_dm",
        }).execute()
        return new_resp.data[0] if new_resp.data else {"current_step": "init"}
    except Exception as e:
        logger.warning(f"[instagram] konuşma alınamadı: {e}")
        return {"current_step": "init"}


def update_conversation(instagram_user_id: str, updates: dict) -> None:
    try:
        supabase = get_supabase_client()
        supabase.table("instagram_conversations").update(updates).eq("instagram_user_id", instagram_user_id).execute()
    except Exception as e:
        logger.warning(f"[instagram] konuşma güncellenemedi: {e}")


# ── CRM Lead Oluştur ──────────────────────────────────────────

def create_instagram_lead(sender_id: str, crm_status: str, crm_interest: str, message_text: str) -> str | None:
    try:
        lead = create_lead(
            name=f"Instagram DM",
            email="",
            phone=None,
            status=crm_status,
            source="instagram_dm",
            notes=f"İlgi: {crm_interest}\nInstagram ID: {sender_id}\nMesaj: {message_text}",
        )
        lead_id = lead["id"] if lead else None
        if lead_id:
            logger.info(f"[instagram] CRM lead oluşturuldu id={lead_id} interest={crm_interest}")
        return lead_id
    except Exception as e:
        logger.warning(f"[instagram] CRM lead oluşturulamadı: {e}")
        return None


# ── Akış Eşleştirme ──────────────────────────────────────────

def match_flow(text: str) -> dict | None:
    """Mesaj metnini flow kurallarıyla eşleştir."""
    normalized = text.strip().lower()
    for flow in FLOWS:
        for keyword in flow["keywords"]:
            if normalized == keyword or keyword in normalized:
                return flow
    return None


# ── Ana Gelen Mesaj İşleyici ──────────────────────────────────

def process_incoming_dm(
    sender_id: str,
    recipient_id: str,
    message_text: str,
    message_id: str,
    timestamp: int,
    raw_payload: dict,
) -> None:
    """Gelen Instagram DM'i işle, cevap ver, DB'ye kaydet."""
    own_id = settings.INSTAGRAM_BUSINESS_ACCOUNT_ID

    # Bot kendi mesajına cevap vermesin
    if sender_id == own_id:
        logger.debug("[instagram] bot kendi mesajı, atlandı")
        return

    # Idempotency: aynı message_id tekrar gelirse işleme
    if is_duplicate_message(message_id):
        logger.info(f"[instagram] duplicate message_id={message_id}, atlandı")
        return

    logger.info(f"[instagram] DM alındı sender={sender_id} text='{message_text[:50]}'")

    # Mesajı kaydet (inbound)
    save_message(message_id, sender_id, recipient_id, message_text, "inbound", raw_payload)

    # Konuşma durumunu al
    conv = get_or_create_conversation(sender_id)
    current_step = conv.get("current_step", "init")

    # Cevap belirle
    reply_text = None
    crm_status = None
    crm_interest = None

    if current_step == "init":
        # İlk mesaj → karşılama menüsü gönder
        reply_text = WELCOME_MESSAGE
        update_conversation(sender_id, {"current_step": "menu", "last_message_at": "now()"})
    else:
        # Menüde veya devamında → flow eşleştir
        flow = match_flow(message_text)
        if flow:
            reply_text = flow["response"]
            crm_status = flow.get("crm_status")
            crm_interest = flow.get("crm_interest")
            update_conversation(sender_id, {
                "current_step": f"flow_{crm_interest or 'link'}",
                "interest": crm_interest,
                "last_message_at": "now()",
            })
        else:
            reply_text = FALLBACK_MESSAGE

    # Cevap gönder
    if reply_text:
        ok = send_instagram_message(sender_id, reply_text)
        if ok:
            # Gönderilen mesajı da kaydet (outbound)
            save_message(
                message_id=f"out_{message_id}",
                sender_id=own_id,
                recipient_id=sender_id,
                message_text=reply_text,
                direction="outbound",
                raw_payload={},
            )

    # CRM lead oluştur
    if crm_status and crm_interest:
        lead_id = create_instagram_lead(sender_id, crm_status, crm_interest, message_text)
        if lead_id:
            update_conversation(sender_id, {"crm_lead_id": lead_id})
            logger.info(f"[instagram] CRM lead created lead_id={lead_id}")
