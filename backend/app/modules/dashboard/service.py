import logging
from app.db.repositories.leads_repo import get_leads
from app.db.repositories.students_repo import get_students
from app.db.repositories.documents_repo import get_documents
from app.db.repositories.generated_contents_repo import list_contents
from app.modules.dashboard.brief_generator import generate_daily_brief

logger = logging.getLogger(__name__)


def _safe(fn):
    try:
        return fn()
    except Exception as e:
        logger.warning(f"[dashboard] veri alınamadı: {e}")
        return []


def get_dashboard_data() -> dict:
    leads = _safe(get_leads)
    students = _safe(get_students)
    documents = _safe(get_documents)
    contents = _safe(list_contents)

    indexed = [d for d in documents if d.get("status") == "indexed"]
    published = [c for c in contents if c.get("status") == "published"]

    recent_docs = sorted(documents, key=lambda d: d.get("created_at", ""), reverse=True)[:5]

    return {
        "stats": {
            "total_documents": len(documents),
            "indexed_documents": len(indexed),
            "total_agent_runs": 0,
            "total_leads": len(leads),
            "total_students": len(students),
            "published_content": len(published),
        },
        "daily_brief": None,
        "recent_documents": [
            {
                "id": d.get("id", ""),
                "file_name": d.get("file_name", ""),
                "status": d.get("status", ""),
                "created_at": d.get("created_at", ""),
            }
            for d in recent_docs
        ],
        "agent_statuses": [
            {"agent_type": "knowledge", "status": "idle"},
            {"agent_type": "voice", "status": "idle"},
            {"agent_type": "automation", "status": "idle"},
        ],
    }


def get_recent_briefs() -> list[dict]:
    from app.db.repositories.briefs_repo import get_briefs
    return _safe(get_briefs)


def create_brief() -> dict:
    return generate_daily_brief()
