from app.db.supabase import get_supabase_client
import logging

logger = logging.getLogger(__name__)


def log_action(
    user_id: str,
    user_email: str,
    action: str,
    resource: str = None,
    details: dict = None,
    ip_address: str = None,
):
    try:
        supabase = get_supabase_client()
        supabase.table("audit_logs").insert({
            "user_id": user_id,
            "user_email": user_email,
            "action": action,
            "resource": resource,
            "details": details or {},
            "ip_address": ip_address,
        }).execute()
    except Exception as e:
        logger.error(f"[audit] kayıt yazılamadı: {e}")


def get_audit_logs(limit: int = 100) -> list[dict]:
    try:
        supabase = get_supabase_client()
        resp = supabase.table("audit_logs").select("*").order("created_at", desc=True).limit(limit).execute()
        return resp.data or []
    except Exception as e:
        logger.error(f"[audit] kayıtlar alınamadı: {e}")
        return []
