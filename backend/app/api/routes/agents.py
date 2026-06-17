import logging
from fastapi import APIRouter
from app.core.config import settings
from app.db.supabase import get_supabase_client

router = APIRouter()
logger = logging.getLogger(__name__)


def _ping_supabase() -> tuple[bool, str]:
    try:
        supabase = get_supabase_client()
        supabase.table("documents").select("id").limit(1).execute()
        return True, "OK"
    except Exception as e:
        return False, str(e)[:80]


def _ping_storage() -> tuple[bool, str]:
    try:
        supabase = get_supabase_client()
        supabase.storage.from_("content-videos").list(path="", options={"limit": 1})
        return True, "OK"
    except Exception as e:
        return False, str(e)[:80]


def _count_table(table: str, filters: dict | None = None) -> int:
    try:
        supabase = get_supabase_client()
        q = supabase.table(table).select("id", count="exact")
        if filters:
            for k, v in filters.items():
                q = q.eq(k, v)
        r = q.execute()
        return r.count or 0
    except Exception:
        return 0


def _agent_statuses() -> list[dict]:
    db_ok, db_msg = _ping_supabase()
    api_ok        = bool(settings.OPENAI_API_KEY)
    storage_ok, _ = _ping_storage()

    # Gerçek sayımlar — tek seferde
    failed_docs     = _count_table("documents",          {"status": "failed"})
    processing_docs = _count_table("documents",          {"status": "processing"})
    indexed_docs    = _count_table("documents",          {"status": "indexed"})
    total_docs      = failed_docs + processing_docs + indexed_docs
    generating_cnt  = _count_table("generated_contents", {"status": "generating"})
    error_cnt       = _count_table("generated_contents", {"status": "error"})
    new_leads       = _count_table("leads",              {"status": "new"})
    followup_leads  = _count_table("leads",              {"status": "contacted"})
    total_leads     = _count_table("leads")

    # ── Knowledge Agent
    if not db_ok:
        k_s, k_l, k_c = "error",   "Supabase bağlantı hatası", "red"
        k_detail = db_msg
    elif not api_ok:
        k_s, k_l, k_c = "error",   "OpenAI API key eksik", "red"
        k_detail = "OPENAI_API_KEY env değişkeni tanımlı değil"
    elif processing_docs > 0:
        k_s, k_l, k_c = "running", f"{processing_docs} doküman işleniyor", "yellow"
        k_detail = f"{indexed_docs}/{total_docs} belge hazır, {processing_docs} sırada"
    elif failed_docs > 0:
        k_s, k_l, k_c = "warning", f"{failed_docs} hatalı doküman", "yellow"
        k_detail = f"{indexed_docs} hazır · {failed_docs} yeniden işlenmeyi bekliyor"
    else:
        k_s, k_l, k_c = "ready",   f"{indexed_docs} belge hazır", "green"
        k_detail = f"Toplam {total_docs} belge indekslenmiş, RAG aktif"

    # ── Voice Agent
    if api_ok:
        v_s, v_l, v_c = "ready", "Whisper + TTS-1 aktif", "green"
        v_detail = "OpenAI Whisper (STT) ve TTS-1 nova sesi hazır"
    else:
        v_s, v_l, v_c = "error", "OpenAI API key eksik", "red"
        v_detail = "Ses özellikleri devre dışı"

    # ── Automation Agent
    if not storage_ok or not api_ok:
        a_s, a_l, a_c = "error",   "Storage/OpenAI bağlantı hatası", "red"
        a_detail = "İçerik üretimi devre dışı"
    elif generating_cnt > 0:
        a_s, a_l, a_c = "running", f"{generating_cnt} içerik üretiliyor", "yellow"
        a_detail = f"{generating_cnt} üretiliyor · {error_cnt} hata"
    elif error_cnt > 0:
        a_s, a_l, a_c = "warning", f"{error_cnt} hatalı içerik", "yellow"
        a_detail = f"{error_cnt} içerik hata aldı, panelden silinebilir"
    else:
        a_s, a_l, a_c = "ready",   "İçerik üretimine hazır", "green"
        a_detail = "Video, Shorts, Soru Çözüm, Konu Anlatım üretilebilir"

    # ── CRM Agent
    if not db_ok:
        c_s, c_l, c_c = "error",   "Veritabanı bağlantı hatası", "red"
        c_detail = db_msg
    elif new_leads > 0:
        c_s, c_l, c_c = "running", f"{new_leads} yeni lead bekliyor", "yellow"
        c_detail = f"Toplam {total_leads} lead · {new_leads} yeni · {followup_leads} takipte"
    else:
        c_s, c_l, c_c = "ready",   "Lead takibi güncel", "green"
        c_detail = f"Toplam {total_leads} lead · {followup_leads} takipte"

    # ── CEO Agent (scheduler sabah 08:00)
    if not db_ok:
        ceo_s, ceo_l, ceo_c = "error",   "DB hatası — özet üretilemez", "red"
        ceo_detail = db_msg
    elif not api_ok:
        ceo_s, ceo_l, ceo_c = "warning", "OpenAI eksik — ham özet", "yellow"
        ceo_detail = "GPT-4o-mini yoksa ham veri özeti üretilir"
    else:
        ceo_s, ceo_l, ceo_c = "running", "Planlandı — sabah 08:00", "green"
        ceo_detail = "APScheduler aktif, GPT-4o-mini özeti her gün 08:00"

    # ── Follow-up Agent (scheduler sabah 09:00)
    fu_s  = "running" if db_ok else "error"
    fu_l  = "Planlandı — sabah 09:00" if db_ok else "DB hatası"
    fu_c  = "green" if db_ok else "red"
    fu_detail = f"APScheduler aktif · {followup_leads} takipte lead" if db_ok else db_msg

    # ── Learning Agent
    lrn_s = "ready" if (db_ok and api_ok) else "error"
    lrn_l = "Hazır" if (db_ok and api_ok) else "Bağlantı eksik"
    lrn_c = "green" if (db_ok and api_ok) else "red"
    lrn_detail = "SGS Academy öğrenci analizi hazır" if (db_ok and api_ok) else "OpenAI veya DB bağlantısı eksik"

    return [
        {"id": "knowledge_agent",  "name": "Knowledge Agent",
         "description": "Doküman işleme, embedding ve RAG bilgi arama",
         "status": k_s, "label": k_l, "color": k_c, "icon": "brain",   "detail": k_detail},
        {"id": "voice_agent",      "name": "Voice Agent",
         "description": "Sesli komut, STT ve TTS servisleri",
         "status": v_s, "label": v_l, "color": v_c, "icon": "mic",     "detail": v_detail},
        {"id": "ceo_agent",        "name": "CEO Agent",
         "description": "Günlük yönetici özeti — her sabah 08:00",
         "status": ceo_s, "label": ceo_l, "color": ceo_c, "icon": "briefcase", "detail": ceo_detail},
        {"id": "crm_agent",        "name": "CRM Agent",
         "description": "Lead yönetimi ve müşteri takibi",
         "status": c_s, "label": c_l, "color": c_c, "icon": "users",   "detail": c_detail},
        {"id": "followup_agent",   "name": "Follow-up Agent",
         "description": "Lead takip hatırlatmaları — her sabah 09:00",
         "status": fu_s, "label": fu_l, "color": fu_c, "icon": "usercheck", "detail": fu_detail},
        {"id": "learning_agent",   "name": "Learning Agent",
         "description": "SGS Academy öğrenci analizi ve öğrenme planları",
         "status": lrn_s, "label": lrn_l, "color": lrn_c, "icon": "bookopen", "detail": lrn_detail},
        {"id": "automation_agent", "name": "Automation Agent",
         "description": "YouTube/Instagram içerik üretimi ve yayın",
         "status": a_s, "label": a_l, "color": a_c, "icon": "video",   "detail": a_detail},
    ]


@router.get("")
def list_agents():
    return _agent_statuses()


@router.get("/status")
def agent_status():
    agents = _agent_statuses()
    return {
        "agents": [
            {
                "name": a["name"],
                "status": a["status"],
                "label": a["label"],
                "color": a["color"],
            }
            for a in agents
        ]
    }


@router.get("/runs")
def list_runs(limit: int = 10):
    return {"runs": []}
