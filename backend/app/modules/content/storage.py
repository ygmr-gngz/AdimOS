import os
import uuid
from app.db.supabase import get_supabase_client

VIDEO_BUCKET = "content-videos"
IMAGE_BUCKET = "content-videos"


def upload_video(local_path: str) -> str:
    if not os.path.exists(local_path):
        raise FileNotFoundError(f"Video dosyası bulunamadı: {local_path}")
    supabase = get_supabase_client()
    ext = os.path.splitext(local_path)[1] or ".mp4"
    remote_path = f"videos/{uuid.uuid4()}{ext}"
    with open(local_path, "rb") as f:
        supabase.storage.from_(VIDEO_BUCKET).upload(
            remote_path, f, {"content-type": "video/mp4"}
        )
    return supabase.storage.from_(VIDEO_BUCKET).get_public_url(remote_path)


def upload_image(local_path: str) -> str:
    if not os.path.exists(local_path):
        raise FileNotFoundError(f"Görsel dosyası bulunamadı: {local_path}")
    supabase = get_supabase_client()
    ext = os.path.splitext(local_path)[1] or ".png"
    remote_path = f"images/{uuid.uuid4()}{ext}"
    with open(local_path, "rb") as f:
        supabase.storage.from_(IMAGE_BUCKET).upload(
            remote_path, f, {"content-type": "image/png"}
        )
    return supabase.storage.from_(IMAGE_BUCKET).get_public_url(remote_path)
