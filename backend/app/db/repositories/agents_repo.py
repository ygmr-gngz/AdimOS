from app.db.supabase import get_supabase_client


def create_conversation(user_id: str, agent_type: str) -> dict | None:
    supabase = get_supabase_client()
    response = supabase.table("conversations").insert({
        "user_id": user_id,
        "agent_type": agent_type,
    }).execute()
    return response.data[0] if response.data else None


def get_conversations(user_id: str) -> list[dict]:
    supabase = get_supabase_client()
    response = (
        supabase.table("conversations")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )
    return response.data if response.data else []


def create_message(conversation_id: str, role: str, content: str) -> dict | None:
    supabase = get_supabase_client()
    response = supabase.table("messages").insert({
        "conversation_id": conversation_id,
        "role": role,
        "content": content,
    }).execute()
    return response.data[0] if response.data else None


def get_messages(conversation_id: str) -> list[dict]:
    supabase = get_supabase_client()
    response = (
        supabase.table("messages")
        .select("*")
        .eq("conversation_id", conversation_id)
        .order("created_at", desc=False)
        .execute()
    )
    return response.data if response.data else []


def delete_conversation(conversation_id: str) -> list[dict]:
    supabase = get_supabase_client()
    supabase.table("messages").delete().eq("conversation_id", conversation_id).execute()
    response = supabase.table("conversations").delete().eq("id", conversation_id).execute()
    return response.data if response.data else []
