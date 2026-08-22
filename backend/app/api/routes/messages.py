from uuid import UUID
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.db.supabase import get_supabase_client

router = APIRouter()


class ManualMessage(BaseModel):
    content: str


class ModeChange(BaseModel):
    manual: bool


@router.get("/sessions")
def sessions():
    return get_supabase_client().table("chat_sessions").select("*").order("last_message_at", desc=True).limit(100).execute().data or []


@router.get("/sessions/{session_id}")
def session_messages(session_id: UUID):
    return get_supabase_client().table("chat_messages").select("id,role,content,created_at").eq("session_id", str(session_id)).order("created_at").execute().data or []


@router.post("/sessions/{session_id}/reply")
def manual_reply(session_id: UUID, body: ManualMessage):
    text = body.content.strip()
    if not text:
        raise HTTPException(422, "Mesaj boş olamaz")
    sb = get_supabase_client()
    session = sb.table("chat_sessions").select("*").eq("id", str(session_id)).single().execute().data
    if not session:
        raise HTTPException(404, "Oturum bulunamadı")
    if session["source"] == "instagram":
        from app.modules.instagram.dm_service import send_instagram_message
        if not send_instagram_message(session["external_id"], text):
            raise HTTPException(409, "Instagram 24 saat penceresi kapalı veya gönderim başarısız")
    result = sb.table("chat_messages").insert({"session_id": str(session_id), "role": "assistant", "content": text}).execute()
    return result.data[0]


@router.post("/sessions/{session_id}/mode")
def change_mode(session_id: UUID, body: ModeChange):
    status = "manual" if body.manual else "active"
    result = get_supabase_client().table("chat_sessions").update({"status": status, "bot_enabled": not body.manual}).eq("id", str(session_id)).execute()
    if not result.data:
        raise HTTPException(404, "Oturum bulunamadı")
    return result.data[0]
