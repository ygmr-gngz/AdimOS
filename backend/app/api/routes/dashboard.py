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
    """Tek brief döndürür — frontend /brief çağırıyorsa buraya düşer."""
    briefs = get_recent_briefs()
    return briefs[0] if briefs else {}


@router.post("/briefs/generate")
def generate_brief():
    return create_brief()
