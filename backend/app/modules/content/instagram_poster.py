import requests
import uuid
from app.core.config import settings
from app.db.storage import upload_file
from app.db.supabase import get_supabase_client

_GRAPH = "https://graph.facebook.com/v21.0"
_BUCKET = "content"


def _get_public_url(file_path: str) -> str:
    with open(file_path, "rb") as f:
        file_bytes = f.read()

    ext = file_path.split(".")[-1]
    file_name = f"{uuid.uuid4()}.{ext}"
    upload_file(_BUCKET, file_name, file_bytes)

    supabase = get_supabase_client()
    return supabase.storage.from_(_BUCKET).get_public_url(file_name)


def post_image_to_instagram(image_path: str, caption: str) -> dict:
    public_url = _get_public_url(image_path)
    account_id = settings.INSTAGRAM_BUSINESS_ACCOUNT_ID
    token = settings.META_ACCESS_TOKEN

    container = requests.post(
        f"{_GRAPH}/{account_id}/media",
        data={"image_url": public_url, "caption": caption, "access_token": token},
    ).json()

    creation_id = container.get("id")
    if not creation_id:
        return {"error": container}

    publish = requests.post(
        f"{_GRAPH}/{account_id}/media_publish",
        data={"creation_id": creation_id, "access_token": token},
    ).json()

    return {"media_id": publish.get("id"), "status": "published"}


def post_reel_to_instagram(video_path: str, caption: str) -> dict:
    public_url = _get_public_url(video_path)
    account_id = settings.INSTAGRAM_BUSINESS_ACCOUNT_ID
    token = settings.META_ACCESS_TOKEN

    container = requests.post(
        f"{_GRAPH}/{account_id}/media",
        data={
            "video_url": public_url,
            "caption": caption,
            "media_type": "REELS",
            "access_token": token,
        },
    ).json()

    creation_id = container.get("id")
    if not creation_id:
        return {"error": container}

    publish = requests.post(
        f"{_GRAPH}/{account_id}/media_publish",
        data={"creation_id": creation_id, "access_token": token},
    ).json()

    return {"media_id": publish.get("id"), "status": "published"}
