import logging
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from app.core.config import settings

logger = logging.getLogger(__name__)


def _get_refresh_token() -> str:
    """Önce Supabase platform_tokens'a bak, sonra env var'a dön."""
    try:
        from app.db.supabase import get_supabase_client
        sb = get_supabase_client()
        row = sb.table("platform_tokens").select("refresh_token").eq("platform", "youtube").execute()
        if row.data and row.data[0].get("refresh_token"):
            logger.debug("[youtube] token Supabase'den alındı")
            return row.data[0]["refresh_token"]
    except Exception as e:
        logger.debug(f"[youtube] Supabase token okunamadı: {e}")
    if settings.YOUTUBE_REFRESH_TOKEN:
        logger.debug("[youtube] token env var'dan alındı")
        return settings.YOUTUBE_REFRESH_TOKEN
    raise RuntimeError("YouTube refresh token bulunamadı. /settings/integrations sayfasından bağlayın.")


def _get_client():
    creds = Credentials(
        token=None,
        refresh_token=_get_refresh_token(),
        client_id=settings.YOUTUBE_CLIENT_ID,
        client_secret=settings.YOUTUBE_CLIENT_SECRET,
        token_uri="https://oauth2.googleapis.com/token",
    )
    return build("youtube", "v3", credentials=creds)


def upload_to_youtube(
    video_path: str,
    title: str,
    description: str,
    tags: list[str],
    privacy: str = "private",
) -> dict:
    youtube = _get_client()

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": "27",  # Eğitim
            "defaultLanguage": "tr",
        },
        "status": {"privacyStatus": privacy},
    }

    media = MediaFileUpload(video_path, chunksize=-1, resumable=True, mimetype="video/mp4")
    request = youtube.videos().insert(part=",".join(body.keys()), body=body, media_body=media)
    response = request.execute()
    video_id = response["id"]

    return {
        "video_id": video_id,
        "url": f"https://www.youtube.com/watch?v={video_id}",
        "status": privacy,
    }


def make_public(video_id: str) -> dict:
    youtube = _get_client()
    youtube.videos().update(
        part="status",
        body={"id": video_id, "status": {"privacyStatus": "public"}},
    ).execute()
    return {"video_id": video_id, "status": "public"}
