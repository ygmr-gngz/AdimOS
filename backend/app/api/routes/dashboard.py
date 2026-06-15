from fastapi import APIRouter
from app.modules.dashboard.service import get_dashboard_data, get_recent_briefs, create_brief

router = APIRouter()


@router.get("")
def dashboard():
    return get_dashboard_data()


@router.get("/briefs")
def list_briefs():
    return get_recent_briefs()


@router.post("/briefs/generate")
def generate_brief():
    return create_brief()
