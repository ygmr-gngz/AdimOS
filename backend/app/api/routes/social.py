"""Sosyal medya bağlantı durumu ve test endpoint'leri."""
import logging
import requests
from fastapi import APIRouter
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

_GRAPH = "https://graph.facebook.com/v21.0"


def _mask(value: str) -> str:
    if not value or len(value) < 10:
        return "***"
    return value[:6] + "..." + value[-4:]


@router.get("/instagram/status")
def instagram_status():
    """Instagram bağlantı durumunu döndür ve token'ı test et."""
    token = settings.META_ACCESS_TOKEN
    account_id = settings.INSTAGRAM_BUSINESS_ACCOUNT_ID

    token_ok = bool(token and len(token) > 10)
    account_ok = bool(account_id and len(account_id) > 4)

    result = {
        "token_configured": token_ok,
        "account_configured": account_ok,
        "token_preview": _mask(token),
        "account_id": account_id or None,
        "connected": False,
        "account_name": None,
        "followers": None,
        "error": None,
    }

    if not token_ok or not account_ok:
        result["error"] = "Token veya Account ID eksik. Railway → Variables'dan ekleyin."
        return result

    try:
        resp = requests.get(
            f"{_GRAPH}/{account_id}",
            params={
                "fields": "name,username,followers_count",
                "access_token": token,
            },
            timeout=8,
        )
        data = resp.json()

        if "error" in data:
            result["error"] = data["error"].get("message", "API hatası")
        else:
            result["connected"] = True
            result["account_name"] = data.get("name") or data.get("username")
            result["followers"] = data.get("followers_count")
    except Exception as e:
        result["error"] = f"Bağlantı kurulamadı: {e}"

    return result


@router.get("/youtube/status")
def youtube_status():
    """YouTube bağlantı durumu — env var veya Supabase token."""
    from app.db.supabase import get_supabase_client
    has_env = bool(settings.YOUTUBE_REFRESH_TOKEN and len(settings.YOUTUBE_REFRESH_TOKEN) > 10)
    has_db = False
    try:
        sb = get_supabase_client()
        row = sb.table("platform_tokens").select("refresh_token").eq("platform", "youtube").execute()
        has_db = bool(row.data and row.data[0].get("refresh_token"))
    except Exception:
        pass
    connected = has_env or has_db
    return {
        "connected": connected,
        "source": "env" if has_env else ("supabase" if has_db else None),
        "client_id_configured": bool(settings.YOUTUBE_CLIENT_ID),
        "error": None if connected else "YouTube henüz bağlanmamış.",
    }


@router.get("/youtube/auth-url")
def youtube_auth_url():
    """Google OAuth URL'si oluştur — kullanıcı bu linki tarayıcıda açar."""
    if not settings.YOUTUBE_CLIENT_ID or not settings.YOUTUBE_CLIENT_SECRET:
        from fastapi import HTTPException
        raise HTTPException(400, "YOUTUBE_CLIENT_ID ve YOUTUBE_CLIENT_SECRET Railway'e eklenmeli.")
    from google_auth_oauthlib.flow import Flow
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": settings.YOUTUBE_CLIENT_ID,
                "client_secret": settings.YOUTUBE_CLIENT_SECRET,
                "redirect_uris": [settings.YOUTUBE_REDIRECT_URI],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=[
            "https://www.googleapis.com/auth/youtube.upload",
            "https://www.googleapis.com/auth/youtube",
        ],
        redirect_uri=settings.YOUTUBE_REDIRECT_URI,
    )
    auth_url, _ = flow.authorization_url(access_type="offline", prompt="consent")
    return {"auth_url": auth_url, "redirect_uri": settings.YOUTUBE_REDIRECT_URI}
