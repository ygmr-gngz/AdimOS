from fastapi import APIRouter

from app.db.supabase import get_supabase_client

router = APIRouter()


@router.get("/queue")
def list_queue(status: str | None = None):
    query = get_supabase_client().table("publishing_queue").select("*").order("created_at", desc=True).limit(100)
    if status:
        query = query.eq("status", status)
    return query.execute().data or []
