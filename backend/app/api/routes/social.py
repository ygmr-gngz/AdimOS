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
    """YouTube OAuth durumunu döndür."""
    has_token = bool(settings.YOUTUBE_REFRESH_TOKEN and len(settings.YOUTUBE_REFRESH_TOKEN) > 10)
    return {
        "configured": has_token,
        "client_id_preview": _mask(settings.YOUTUBE_CLIENT_ID),
        "refresh_token_configured": has_token,
        "error": None if has_token else "YOUTUBE_REFRESH_TOKEN eksik. Google Cloud Console'dan alın.",
    }
