import logging
import os
import uuid
from app.db.supabase import get_supabase_client

logger = logging.getLogger(__name__)

VIDEO_BUCKET = "content-videos"
IMAGE_BUCKET = "content-videos"
VISUAL_LIBRARY_BUCKET = "visual-library"


def ensure_bucket(bucket: str, public: bool = True) -> None:
    """Bucket yoksa oluşturur — idempotent (bkz. api/routes/brand.py _ensure_bucket)."""
    supabase = get_supabase_client()
    try:
        buckets = supabase.storage.list_buckets()
        names = [b.name if hasattr(b, "name") else b.get("name", "") for b in buckets]
        if bucket not in names:
            supabase.storage.create_bucket(bucket, options={"public": public})
            logger.info(f"[storage] '{bucket}' bucket oluşturuldu")
    except Exception as e:
        logger.warning(f"[storage] bucket kontrol hatası ({bucket}): {e}")


def upload_bytes(data: bytes, bucket: str, remote_path: str, content_type: str) -> str:
    """Bellekteki bytes'ı doğrudan Supabase Storage'a yükler (local dosya gerekmez)."""
    ensure_bucket(bucket)
    supabase = get_supabase_client()
    supabase.storage.from_(bucket).upload(
        remote_path, data, {"content-type": content_type}
    )
    return supabase.storage.from_(bucket).get_public_url(remote_path)


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
