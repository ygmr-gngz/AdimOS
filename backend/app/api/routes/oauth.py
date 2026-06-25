"""OAuth callback endpoint'leri — PUBLIC, JWT gerektirmez."""
import logging
from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse
from app.core.config import settings
from app.db.supabase import get_supabase_client

logger = logging.getLogger(__name__)
router = APIRouter()

_YT_SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
]

_SUCCESS_HTML = """<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="UTF-8">
  <title>YouTube Bağlandı</title>
  <style>
    body { font-family: system-ui, sans-serif; background: #0e0d0c; color: #f8f8f8;
           display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }
    .card { background: #1e1c19; border: 1px solid #3c3830; border-radius: 16px;
            padding: 40px; text-align: center; max-width: 380px; }
    h1 { color: #f97316; margin: 0 0 12px; font-size: 22px; }
    p { color: #9ca3af; margin: 0; }
    .icon { font-size: 48px; margin-bottom: 16px; }
  </style>
</head>
<body>
  <div class="card">
    <div class="icon">✅</div>
    <h1>YouTube Bağlandı!</h1>
    <p>Bu sekmeyi kapatabilirsiniz. AdimOS paneline dönün.</p>
  </div>
</body>
</html>"""

_ERROR_HTML = """<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="UTF-8">
  <title>Hata</title>
  <style>
    body {{ font-family: system-ui, sans-serif; background: #0e0d0c; color: #f8f8f8;
            display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }}
    .card {{ background: #1e0a0a; border: 1px solid #7f1d1d; border-radius: 16px;
              padding: 40px; text-align: center; max-width: 420px; }}
    h1 {{ color: #ef4444; margin: 0 0 12px; font-size: 22px; }}
    p {{ color: #9ca3af; margin: 0; font-size: 14px; }}
  </style>
</head>
<body>
  <div class="card">
    <h1>Bağlantı başarısız</h1>
    <p>{error}</p>
  </div>
</body>
</html>"""


def _flow():
    from google_auth_oauthlib.flow import Flow
    return Flow.from_client_config(
        {
            "web": {
                "client_id": settings.YOUTUBE_CLIENT_ID,
                "client_secret": settings.YOUTUBE_CLIENT_SECRET,
                "redirect_uris": [settings.YOUTUBE_REDIRECT_URI],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=_YT_SCOPES,
        redirect_uri=settings.YOUTUBE_REDIRECT_URI,
    )


@router.get("/youtube/callback")
def youtube_callback(code: str = Query(...), error: str = Query(None)):
    """Google OAuth callback — refresh token'ı Supabase'e kaydeder."""
    if error:
        logger.warning(f"[oauth/youtube] Google hatası: {error}")
        return HTMLResponse(_ERROR_HTML.format(error=f"Google hatası: {error}"), status_code=400)

    try:
        flow = _flow()
        flow.fetch_token(code=code)
        creds = flow.credentials
        refresh_token = creds.refresh_token

        if not refresh_token:
            return HTMLResponse(_ERROR_HTML.format(
                error="Refresh token alınamadı. Google Console'da uygulamanızın onay tipini 'External' yapın ve prompt=consent ekleyin."
            ), status_code=400)

        supabase = get_supabase_client()
        supabase.table("platform_tokens").upsert({
            "platform": "youtube",
            "refresh_token": refresh_token,
        }).execute()

        logger.info("[oauth/youtube] YouTube bağlantısı başarılı, token kaydedildi")
        return HTMLResponse(_SUCCESS_HTML)

    except Exception as e:
        logger.error(f"[oauth/youtube] token alınamadı: {e}", exc_info=True)
        return HTMLResponse(_ERROR_HTML.format(error=str(e)[:200]), status_code=500)
