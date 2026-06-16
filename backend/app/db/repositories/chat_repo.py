import logging
from app.db.supabase import get_supabase_client

logger = logging.getLogger(__name__)


def create_conversation(user_id: str, title: str = "Yeni Sohbet") -> dict | None:
    supabase = get_supabase_client()
    try:
        resp = supabase.table("chat_conversations").insert({
            "user_id": user_id,
            "title": title[:80],
        }).execute()
        return resp.data[0] if resp.data else None
    except Exception as e:
        logger.error(f"[chat_repo] conversation oluşturulamadı: {e}")
        return None


def get_conversations(user_id: str, limit: int = 30) -> list[dict]:
    supabase = get_supabase_client()
    try:
        resp = (
            supabase.table("chat_conversations")
            .select("id, title, created_at, updated_at")
            .eq("user_id", user_id)
            .order("updated_at", desc=True)
            .limit(limit)
            .execute()
        )
        return resp.data or []
    except Exception as e:
        logger.error(f"[chat_repo] conversations alınamadı: {e}")
        return []


def touch_conversation(conversation_id: str):
    supabase = get_supabase_client()
    try:
        from datetime import datetime, timezone
        supabase.table("chat_conversations").update({
            "updated_at": datetime.now(timezone.utc).isoformat()
        }).eq("id", conversation_id).execute()
    except Exception as e:
        logger.warning(f"[chat_repo] conversation timestamp güncellenemedi: {e}")


def create_message(
    conversation_id: str,
    user_id: str,
    role: str,
    content: str,
    sources: list | None = None,
    used_rag: bool = False,
) -> dict | None:
    supabase = get_supabase_client()
    try:
        resp = supabase.table("chat_messages").insert({
            "conversation_id": conversation_id,
            "user_id": user_id,
            "role": role,
            "content": content,
            "sources": sources or [],
            "used_rag": used_rag,
        }).execute()
        return resp.data[0] if resp.data else None
    except Exception as e:
        logger.error(f"[chat_repo] mesaj kaydedilemedi: {e}")
        return None


def get_messages(conversation_id: str, limit: int = 60) -> list[dict]:
    supabase = get_supabase_client()
    try:
        resp = (
            supabase.table("chat_messages")
            .select("id, role, content, sources, used_rag, created_at")
            .eq("conversation_id", conversation_id)
            .order("created_at", desc=False)
            .limit(limit)
            .execute()
        )
        return resp.data or []
    except Exception as e:
        logger.error(f"[chat_repo] mesajlar alınamadı: {e}")
        return []


def delete_conversation(conversation_id: str):
    supabase = get_supabase_client()
    try:
        supabase.table("chat_messages").delete().eq("conversation_id", conversation_id).execute()
        supabase.table("chat_conversations").delete().eq("id", conversation_id).execute()
    except Exception as e:
        logger.error(f"[chat_repo] sohbet silinemedi: {e}")
