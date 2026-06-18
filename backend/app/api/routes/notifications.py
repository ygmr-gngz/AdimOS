"""Bildirim sistemi — CRUD endpoint'leri."""
import logging
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.db.supabase import get_supabase_client
from app.core.auth import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)
_TABLE = "notifications"


class NotificationCreate(BaseModel):
    type: str
    title: str
    body: str = ""


def push_notification(type: str, title: str, body: str = "") -> dict | None:
    """Herhangi bir yerden bildirim oluşturmak için yardımcı fonksiyon."""
    try:
        sb = get_supabase_client()
        resp = sb.table(_TABLE).insert({
            "type": type,
            "title": title,
            "body": body,
            "is_read": False,
        }).execute()
        return resp.data[0] if resp.data else None
    except Exception as e:
        logger.warning(f"[notifications] push hatası: {e}")
        return None


@router.get("")
def list_notifications(user=Depends(get_current_user)):
    try:
        sb = get_supabase_client()
        resp = (
            sb.table(_TABLE)
            .select("*")
            .order("created_at", desc=True)
            .limit(50)
            .execute()
        )
        unread = sum(1 for n in (resp.data or []) if not n.get("is_read"))
        return {"notifications": resp.data or [], "unread_count": unread}
    except Exception as e:
        logger.error(f"[notifications] list hatası: {e}")
        return {"notifications": [], "unread_count": 0}


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


@router.delete("")
def clear_all(user=Depends(get_current_user)):
    try:
        sb = get_supabase_client()
        sb.table(_TABLE).delete().eq("is_read", True).execute()
    except Exception as e:
        logger.warning(f"[notifications] clear hatası: {e}")
    return {"ok": True}
