import logging
from app.db.repositories.leads_repo import get_leads
from app.db.repositories.students_repo import get_students
from app.db.repositories.documents_repo import get_documents
from app.db.repositories.generated_contents_repo import list_contents

logger = logging.getLogger(__name__)


def _safe(fn, default=None):
    try:
        return fn()
    except Exception as e:
        logger.warning(f"[dashboard] veri alınamadı: {e}")
        return default if default is not None else []


def _get_agent_statuses() -> list[dict]:
    """Merkezi agent durumunu /agents route ile aynı kaynaktan çek."""
    try:
        from app.api.routes.agents import _agent_statuses
        agents = _agent_statuses()
        return [
            {
                "agent_type": a["id"].replace("_agent", ""),
                "status": a["status"],
                "label": a["label"],
                "color": a["color"],
            }
            for a in agents
        ]
    except Exception as e:
        logger.warning(f"[dashboard] agent status alınamadı: {e}")
        return []


def get_dashboard_data() -> dict:
    leads     = _safe(get_leads)
    students  = _safe(get_students)
    documents = _safe(get_documents)
    contents  = _safe(list_contents)

    indexed        = [d for d in documents if d.get("status") == "indexed"]
    failed_docs    = [d for d in documents if d.get("status") == "failed"]
    processing     = [d for d in documents if d.get("status") == "processing"]
    published      = [c for c in contents if c.get("status") == "published"]
    pending        = [c for c in contents if c.get("status") == "pending_approval"]
    generating     = [c for c in contents if c.get("status") == "generating"]
    failed_content = [c for c in contents if c.get("status") == "failed"]
    new_leads      = [l for l in leads if l.get("status") == "new"]
    followup       = [l for l in leads if l.get("status") == "follow_up"]

    recent_docs = sorted(documents, key=lambda d: d.get("created_at", ""), reverse=True)[:5]
    recent_contents = sorted(contents, key=lambda c: c.get("created_at", ""), reverse=True)[:5]

    # En güncel CEO brifini yükle
    brief_content = None
    brief_generated_at = None
    brief_title = None
    try:
        from app.db.repositories.briefs_repo import get_briefs
        briefs = _safe(get_briefs)
        if briefs:
            brief_content      = briefs[0].get("content", "")
            brief_generated_at = briefs[0].get("created_at", "")
            brief_title        = briefs[0].get("title", "Günlük CEO Özeti")
    except Exception:
        pass

    return {
        "stats": {
            "total_documents": len(documents),
            "indexed_documents": len(indexed),
            "failed_documents": len(failed_docs),
            "processing_documents": len(processing),
            "total_leads": len(leads),
            "new_leads": len(new_leads),
            "followup_leads": len(followup),
            "pending_content": len(pending),
            "generating_content": len(generating),
            "failed_content": len(failed_content),
            "total_students": len(students),
            "published_content": len(published),
            "total_content": len(contents),
        },
        "daily_brief": brief_content,
        "brief_generated_at": brief_generated_at,
        "brief_title": brief_title,
        "recent_documents": [
            {
                "id": d.get("id", ""),
                "file_name": d.get("file_name", ""),
                "status": d.get("status", ""),
                "created_at": d.get("created_at", ""),
            }
            for d in recent_docs
        ],
        "recent_contents": [
            {
                "id": c.get("id", ""),
                "title": c.get("title", ""),
                "content_type": c.get("content_type", ""),
                "status": c.get("status", ""),
                "created_at": c.get("created_at", ""),
            }
            for c in recent_contents
        ],
        "agent_statuses": _get_agent_statuses(),
    }


def get_recent_briefs() -> list[dict]:
    from app.db.repositories.briefs_repo import get_briefs
    return _safe(get_briefs)


def create_brief() -> dict:
    from app.modules.dashboard.brief_generator import generate_daily_brief
    return generate_daily_brief()
