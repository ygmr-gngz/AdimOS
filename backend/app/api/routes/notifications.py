"""Bildirim sistemi — Aktivite Merkezi."""
import logging
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.db.supabase import get_supabase_client
from app.core.auth import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)
_TABLE = "notifications"


def push_notification(
    type: str,
    title: str,
    body: str = "",            # geriye dönük uyum
    *,
    message: str | None = None,
    status: str = "info",      # info | success | warning | error
    priority: str = "normal",  # low | normal | high | critical
    details: dict | None = None,
    related_entity_type: str | None = None,
    related_entity_id: str | None = None,
    action_url: str | None = None,
) -> dict | None:
    """Herhangi bir yerden bildirim oluşturmak için yardımcı fonksiyon."""
    msg = message or body
    try:
        sb = get_supabase_client()
        row = {
            "type": type,
            "title": title,
            "body": msg,
            "message": msg,
            "is_read": False,
            "status": status,
            "priority": priority,
        }
        if details:
            row["details"] = details
        if related_entity_type:
            row["related_entity_type"] = related_entity_type
        if related_entity_id:
            row["related_entity_id"] = related_entity_id
        if action_url:
            row["action_url"] = action_url
        resp = sb.table(_TABLE).insert(row).execute()
        return resp.data[0] if resp.data else None
    except Exception as e:
        logger.warning(f"[notifications] push hatası: {e}")
        return None


# ── Listele ───────────────────────────────────────────────────

@router.get("")
def list_notifications(
    limit: int = 80,
    user=Depends(get_current_user),
):
    try:
        sb = get_supabase_client()
        resp = (
            sb.table(_TABLE)
            .select("*")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        rows = resp.data or []
        unread = sum(1 for n in rows if not n.get("is_read"))
        return {"notifications": rows, "unread_count": unread}
    except Exception as e:
        logger.error(f"[notifications] list hatası: {e}")
        return {"notifications": [], "unread_count": 0}


@router.get("/unread-count")
def unread_count(user=Depends(get_current_user)):
    try:
        sb = get_supabase_client()
        resp = sb.table(_TABLE).select("id", count="exact").eq("is_read", False).execute()
        return {"unread_count": resp.count or 0}
    except Exception:
        return {"unread_count": 0}


@router.get("/{notification_id}")
def get_notification(notification_id: str, user=Depends(get_current_user)):
    try:
        sb = get_supabase_client()
        resp = sb.table(_TABLE).select("*").eq("id", notification_id).execute()
        if not resp.data:
            from fastapi import HTTPException
            raise HTTPException(404, "Bildirim bulunamadı")
        return resp.data[0]
    except Exception as e:
        logger.error(f"[notifications] get hatası: {e}")
        return {}


# ── Okundu ────────────────────────────────────────────────────

@router.patch("/{notification_id}/read")
def mark_read(notification_id: str, user=Depends(get_current_user)):
    try:
        sb = get_supabase_client()
        sb.table(_TABLE).update({"is_read": True}).eq("id", notification_id).execute()
    except Exception as e:
        logger.warning(f"[notifications] read hatası: {e}")
    return {"ok": True}


@router.patch("/read-all")
def mark_all_read(user=Depends(get_current_user)):
    try:
        sb = get_supabase_client()
        sb.table(_TABLE).update({"is_read": True}).eq("is_read", False).execute()
    except Exception as e:
        logger.warning(f"[notifications] read-all hatası: {e}")
    return {"ok": True}


# ── Sil ──────────────────────────────────────────────────────

@router.delete("/clear-read")
def clear_read(user=Depends(get_current_user)):
    try:
        sb = get_supabase_client()
        sb.table(_TABLE).delete().eq("is_read", True).execute()
    except Exception as e:
        logger.warning(f"[notifications] clear-read hatası: {e}")
    return {"ok": True}


@router.delete("/{notification_id}")
def delete_notification(notification_id: str, user=Depends(get_current_user)):
    try:
        sb = get_supabase_client()
        sb.table(_TABLE).delete().eq("id", notification_id).execute()
    except Exception as e:
        logger.warning(f"[notifications] delete hatası: {e}")
    return {"ok": True}


@router.delete("")
def clear_all(user=Depends(get_current_user)):
    try:
        sb = get_supabase_client()
        sb.table(_TABLE).delete().eq("is_read", True).execute()
    except Exception as e:
        logger.warning(f"[notifications] clear hatası: {e}")
    return {"ok": True}
