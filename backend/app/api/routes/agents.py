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
    db_ok, db_msg   = _ping_supabase()
    api_ok          = bool(settings.OPENAI_API_KEY)
    storage_ok, _   = _ping_storage()

    # Gerçek sayımlar
    failed_docs     = _count_table("documents",         {"status": "failed"})
    processing_docs = _count_table("documents",         {"status": "processing"})
    generating_cnt  = _count_table("generated_contents",{"status": "generating"})
    new_leads       = _count_table("leads",             {"status": "new"})

    def _s(ready: bool, busy: bool, err: bool, busy_label: str, err_label: str) -> tuple[str, str, str]:
        if err:   return "error",   err_label,  "red"
        if busy:  return "running", busy_label, "yellow"
        return "ready", "Hazır", "green"

    # Knowledge
    k_err  = not db_ok or not api_ok
    k_busy = processing_docs > 0
    k_s, k_l, k_c = _s(
        True, k_busy, k_err,
        f"{processing_docs} doküman işleniyor",
        "Supabase/OpenAI bağlantı hatası" if not db_ok else "OpenAI API eksik",
    )
    if db_ok and api_ok and failed_docs > 0:
        k_s, k_l, k_c = "warning", f"{failed_docs} hatalı doküman", "yellow"

    # Voice
    v_s, v_l, v_c = ("ready", "API aktif", "green") if api_ok else ("error", "OpenAI API eksik", "red")

    # Automation
    a_err  = not storage_ok or not api_ok
    a_busy = generating_cnt > 0
    a_s, a_l, a_c = _s(
        True, a_busy, a_err,
        f"{generating_cnt} içerik üretiliyor",
        "Storage/OpenAI hatası",
    )

    # CRM
    c_s, c_l, c_c = _s(
        True, new_leads > 0, not db_ok,
        f"{new_leads} yeni lead bekliyor",
        "Veritabanı bağlantı hatası",
    )
    if db_ok and new_leads > 0:
        c_s, c_l, c_c = "running", f"{new_leads} yeni lead", "yellow"

    # CEO & Follow-up — scheduler her sabah çalışıyor
    ceo_s, ceo_l, ceo_c = ("running", "Planlandı — sabah 08:00", "yellow") if db_ok else ("error", "DB hatası", "red")
    fu_s,  fu_l,  fu_c  = ("running", "Planlandı — sabah 09:00", "yellow") if db_ok else ("error", "DB hatası", "red")

    # Learning
    lrn_s, lrn_l, lrn_c = ("ready", "Hazır", "green") if (db_ok and api_ok) else ("error", "Bağlantı hatası", "red")

    return [
        {
            "id": "knowledge_agent",
            "name": "Knowledge Agent",
            "description": "Doküman işleme, embedding ve RAG bilgi arama",
            "status": k_s, "label": k_l, "color": k_c,
            "icon": "brain", "run_count": 0,
            "detail": db_msg if not db_ok else f"{failed_docs} hatalı, {processing_docs} işleniyor",
        },
        {
            "id": "voice_agent",
            "name": "Voice Agent",
            "description": "Sesli komut, STT ve TTS servisleri",
            "status": v_s, "label": v_l, "color": v_c,
            "icon": "mic", "run_count": 0,
            "detail": "OpenAI Whisper + TTS-1 aktif" if api_ok else "API key eksik",
        },
        {
            "id": "ceo_agent",
            "name": "CEO Agent",
            "description": "Günlük yönetici özeti — her sabah 08:00",
            "status": ceo_s, "label": ceo_l, "color": ceo_c,
            "icon": "briefcase", "run_count": 0,
            "detail": "APScheduler aktif" if db_ok else db_msg,
        },
        {
            "id": "crm_agent",
            "name": "CRM Agent",
            "description": "Lead yönetimi ve müşteri takibi",
            "status": c_s, "label": c_l, "color": c_c,
            "icon": "users", "run_count": 0,
            "detail": f"Toplam {_count_table('leads')} lead" if db_ok else db_msg,
        },
        {
            "id": "followup_agent",
            "name": "Follow-up Agent",
            "description": "Lead takip hatırlatmaları — her sabah 09:00",
            "status": fu_s, "label": fu_l, "color": fu_c,
            "icon": "usercheck", "run_count": 0,
            "detail": "APScheduler aktif" if db_ok else db_msg,
        },
        {
            "id": "learning_agent",
            "name": "Learning Agent",
            "description": "SGS Academy öğrenci analizi ve öğrenme planları",
            "status": lrn_s, "label": lrn_l, "color": lrn_c,
            "icon": "bookopen", "run_count": 0,
            "detail": "Sistem hazır" if (db_ok and api_ok) else "Bağlantı eksik",
        },
        {
            "id": "automation_agent",
            "name": "Automation Agent",
            "description": "YouTube/Instagram içerik üretimi ve yayın",
            "status": a_s, "label": a_l, "color": a_c,
            "icon": "video", "run_count": 0,
            "detail": f"{generating_cnt} içerik üretiliyor" if a_busy else "Hazır — içerik üret butonuna bas",
        },
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
