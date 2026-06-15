from app.db.repositories.leads_repo import get_leads
from app.db.repositories.students_repo import get_students
from app.db.repositories.documents_repo import get_documents
from app.db.repositories.briefs_repo import get_briefs
from app.modules.dashboard.brief_generator import generate_daily_brief


def get_dashboard_data() -> dict:
    leads = get_leads()
    students = get_students()
    documents = get_documents()

    return {
        "leads": {
            "total": len(leads),
            "new": len([l for l in leads if l.get("status") == "new"]),
            "qualified": len([l for l in leads if l.get("status") == "qualified"]),
        },
        "students": {
            "total": len(students),
            "active": len([s for s in students if s.get("status") == "active"]),
        },
        "documents": {
            "total": len(documents),
            "indexed": len([d for d in documents if d.get("status") == "indexed"]),
        },
    }


def get_recent_briefs() -> list[dict]:
    return get_briefs()


def create_brief() -> dict:
    return generate_daily_brief()
