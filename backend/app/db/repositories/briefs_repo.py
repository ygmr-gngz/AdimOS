from app.db.supabase import get_supabase_client


def create_brief(title: str, content: str, brief_type: str) -> dict | None:
    supabase = get_supabase_client()
    response = supabase.table("briefs").insert({
        "title": title,
        "content": content,
        "type": brief_type,
    }).execute()
    return response.data[0] if response.data else None


def get_briefs() -> list[dict]:
    supabase = get_supabase_client()
    response = (
        supabase.table("briefs")
        .select("*")
        .order("created_at", desc=True)
        .execute()
    )
    return response.data if response.data else []


def get_brief(brief_id: str) -> dict | None:
    supabase = get_supabase_client()
    response = supabase.table("briefs").select("*").eq("id", brief_id).execute()
    return response.data[0] if response.data else None


def delete_brief(brief_id: str) -> list[dict]:
    supabase = get_supabase_client()
    response = supabase.table("briefs").delete().eq("id", brief_id).execute()
    return response.data if response.data else []
