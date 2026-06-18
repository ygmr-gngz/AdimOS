from fastapi import APIRouter
from app.modules.dashboard.service import get_dashboard_data, get_recent_briefs, create_brief

router = APIRouter()


@router.get("")
def dashboard():
    return get_dashboard_data()


@router.get("/briefs")
def list_briefs():
    return get_recent_briefs()


@router.get("/brief")
def get_latest_brief():
    """En güncel CEO brifingini {brief, generated_at, title} formatında döndürür."""
    briefs = get_recent_briefs()
    if not briefs:
        return {"brief": None, "generated_at": None, "title": None}
    b = briefs[0]
    return {
        "brief": b.get("content", ""),
        "generated_at": b.get("created_at", ""),
        "title": b.get("title", "Günlük CEO Özeti"),
    }


@router.post("/brief/generate")
def generate_brief_new():
    """CEO brifingini anında üret ve döndür."""
    result = create_brief()
    if not result:
        return {"brief": None, "generated_at": None}
    return {
        "brief": result.get("content", ""),
        "generated_at": result.get("created_at", ""),
        "title": result.get("title", "Günlük CEO Özeti"),
    }


@router.post("/briefs/generate")
def generate_brief():
    return create_brief()
