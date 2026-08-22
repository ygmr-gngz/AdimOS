import re
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Header, HTTPException
from openai import OpenAI
from pydantic import BaseModel

from app.core.config import settings
from app.db.supabase import get_supabase_client
from app.modules.content.quality_gates import FORBIDDEN_MARKETING_PHRASES

router = APIRouter()

SYSTEM = """Sen Adım Müşavir yapay zekâ asistanısın. Yalnızca SGS sınavı,
muhasebe temel kavramları ve staja giriş süreci hakkında bilgilendirici, net,
2-4 cümlelik Türkçe cevap ver. Kesin hukuki veya mali danışmanlık, kişiye özel
vergi hesabı, ücret/fiyat, en iyi/en ucuz karşılaştırması ve iş talebi verme.
Hizmet isteyen kullanıcıya yalnızca 'Detaylı bilgi için iletişim formunu
doldurabilirsiniz.' de. Emin olmadığın güncel mevzuatı kesinmiş gibi sunma."""


class SessionCreate(BaseModel):
    source: str = "website"


class MessageCreate(BaseModel):
    session_id: UUID
    message: str
    visitor_name: str | None = None
    visitor_email: str | None = None


def _auth(key: str | None) -> None:
    if not settings.ADIMOS_WIDGET_PUBLIC_KEY or key != settings.ADIMOS_WIDGET_PUBLIC_KEY:
        raise HTTPException(401, "Geçersiz widget anahtarı")


def _filter_answer(answer: str) -> str:
    lowered = answer.casefold()
    hits = [phrase for phrase in FORBIDDEN_MARKETING_PHRASES if phrase.casefold() in lowered]
    if hits:
        return "Bu konuda yalnızca genel bilgilendirme yapabilirim. Detaylı bilgi için iletişim formunu doldurabilirsiniz."
    return answer.strip()


@router.post("/session")
def create_session(body: SessionCreate, x_adimos_key: str | None = Header(default=None)):
    _auth(x_adimos_key)
    if body.source != "website":
        raise HTTPException(422, "Widget oturum kaynağı website olmalı")
    result = get_supabase_client().table("chat_sessions").insert({"source": body.source}).execute()
    return {"session_id": result.data[0]["id"]}


@router.post("/message")
def send_message(body: MessageCreate, x_adimos_key: str | None = Header(default=None)):
    _auth(x_adimos_key)
    text = body.message.strip()
    if not text or len(text) > 2000:
        raise HTTPException(422, "Mesaj 1-2000 karakter olmalı")
    sb = get_supabase_client()
    session = sb.table("chat_sessions").select("*").eq("id", str(body.session_id)).single().execute().data
    if not session or session.get("status") in ("closed", "manual") or not session.get("bot_enabled", True):
        raise HTTPException(409, "Bu oturum manuel modda veya kapalı")
    history = sb.table("chat_messages").select("role,content").eq("session_id", str(body.session_id)).order("created_at").limit(12).execute().data or []
    sb.table("chat_messages").insert({"session_id": str(body.session_id), "role": "user", "content": text}).execute()
    messages = [{"role": "system", "content": SYSTEM}] + history + [{"role": "user", "content": text}]
    response = OpenAI(api_key=settings.OPENAI_API_KEY).chat.completions.create(
        model="gpt-4o-mini", messages=messages, max_tokens=220, temperature=0.2,
    )
    answer = _filter_answer(response.choices[0].message.content or "")
    sb.table("chat_messages").insert({"session_id": str(body.session_id), "role": "assistant", "content": answer}).execute()
    updates: dict = {"last_message_at": datetime.now(timezone.utc).isoformat()}
    if body.visitor_name:
        updates["visitor_name"] = body.visitor_name[:100]
    if body.visitor_email:
        if not re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", body.visitor_email):
            raise HTTPException(422, "Geçerli bir e-posta adresi girin")
        updates["visitor_email"] = body.visitor_email
        updates["status"] = "converted"
    sb.table("chat_sessions").update(updates).eq("id", str(body.session_id)).execute()
    user_count = sum(1 for message in history if message.get("role") == "user") + 1
    lead_prompt = user_count >= 3 and not session.get("visitor_email")
    return {"answer": answer, "request_contact": lead_prompt}


@router.get("/history/{session_id}")
def history(session_id: UUID, x_adimos_key: str | None = Header(default=None)):
    _auth(x_adimos_key)
    messages = get_supabase_client().table("chat_messages").select("id,role,content,created_at").eq("session_id", str(session_id)).order("created_at").execute().data or []
    return {"messages": messages}
