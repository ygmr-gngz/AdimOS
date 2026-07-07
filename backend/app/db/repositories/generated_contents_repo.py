from app.db.supabase import get_supabase_client

_TABLE = "generated_contents"

# Liste endpoint'i için ince sütun seti — audio_base64 hariç, yalnızca mevcut kolonlar
_LIST_FIELDS = (
    "id,title,caption,type,status,topic,"
    "video_url,image_url,audio_url,"
    "script,error_detail,approval_notes,"
    "created_at"
)


def create_content(topic: str, content_type: str) -> dict:
    supabase = get_supabase_client()
    r = supabase.table(_TABLE).insert({
        "topic": topic,
        "type": content_type,
        "status": "generating",
    }).execute()
    return r.data[0] if r.data else {}


def update_content(content_id: str, updates: dict) -> dict:
    supabase = get_supabase_client()
    r = supabase.table(_TABLE).update(updates).eq("id", content_id).execute()
    return r.data[0] if r.data else {}


def get_content(content_id: str) -> dict | None:
    supabase = get_supabase_client()
    r = supabase.table(_TABLE).select("*").eq("id", content_id).execute()
    return r.data[0] if r.data else None


def list_contents(page: int = 0, limit: int = 50) -> list[dict]:
    supabase = get_supabase_client()
    offset = page * limit
    r = (
        supabase.table(_TABLE)
        .select(_LIST_FIELDS)
        .order("created_at", desc=True)
        .range(offset, offset + limit - 1)
        .execute()
    )
    return r.data if r.data else []


def delete_content(content_id: str) -> None:
    supabase = get_supabase_client()
    supabase.table(_TABLE).delete().eq("id", content_id).execute()


def delete_orphan_contents() -> int:
    """video_url ve image_url'si olmayan error/failed/generating kartları sil."""
    supabase = get_supabase_client()
    r = (
        supabase.table(_TABLE)
        .delete()
        .is_("video_url", "null")
        .is_("image_url", "null")
        .in_("status", ["error", "failed", "generating"])
        .execute()
    )
    return len(r.data) if r.data else 0
