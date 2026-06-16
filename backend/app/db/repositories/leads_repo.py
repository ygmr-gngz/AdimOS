from app.db.supabase import get_supabase_client


def create_lead(name: str, email: str, phone: str | None, status: str, source: str | None = None, notes: str | None = None) -> dict | None:
    supabase = get_supabase_client()
    row = {"name": name, "email": email, "phone": phone, "status": status}
    if source: row["source"] = source
    if notes: row["notes"] = notes
    response = supabase.table("leads").insert(row).execute()
    return response.data[0] if response.data else None


def get_leads() -> list[dict]:
    supabase = get_supabase_client()
    response = (
        supabase.table("leads")
        .select("*")
        .order("created_at", desc=True)
        .execute()
    )
    return response.data if response.data else []


def get_lead(lead_id: str) -> dict | None:
    supabase = get_supabase_client()
    response = supabase.table("leads").select("*").eq("id", lead_id).execute()
    return response.data[0] if response.data else None


def update_lead(lead_id: str, updates: dict) -> dict | None:
    supabase = get_supabase_client()
    response = supabase.table("leads").update(updates).eq("id", lead_id).execute()
    return response.data[0] if response.data else None


def delete_lead(lead_id: str) -> list[dict]:
    supabase = get_supabase_client()
    response = supabase.table("leads").delete().eq("id", lead_id).execute()
    return response.data if response.data else []
