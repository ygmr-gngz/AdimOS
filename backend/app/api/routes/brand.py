"""Marka varlıkları — logo yükleme (ayarlar otomatik)."""
import io
import logging
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from app.db.repositories.brand_repo import get_brand_settings, update_brand_settings, _logo_cache, _logo_cache_url
from app.db.supabase import get_supabase_client

logger = logging.getLogger(__name__)
router = APIRouter()

BUCKET = "brand-assets"
ALLOWED_TYPES = {"image/png", "image/jpeg", "image/jpg", "image/webp"}


def _ensure_bucket() -> None:
    """Bucket yoksa oluşturur."""
    supabase = get_supabase_client()
    try:
        buckets = supabase.storage.list_buckets()
        names = [b.name if hasattr(b, "name") else b.get("name", "") for b in buckets]
        if BUCKET not in names:
            supabase.storage.create_bucket(BUCKET, options={"public": True})
            logger.info(f"[brand] '{BUCKET}' bucket oluşturuldu")
    except Exception as e:
        logger.warning(f"[brand] bucket kontrol hatası: {e}")


def _to_png_bytes(raw: bytes, content_type: str) -> tuple[bytes, str]:
    """PNG değilse PNG'ye dönüştür (PIL üzerinden)."""
    if content_type == "image/png":
        return raw, "adim_logo.png"
    from PIL import Image
    img = Image.open(io.BytesIO(raw)).convert("RGBA")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue(), "adim_logo.png"


@router.get("/settings")
def get_settings():
    return get_brand_settings()


@router.put("/settings")
def toggle_watermark(body: dict):
    """Sadece watermark_enabled toggle'ı — geri kalan ayarlar otomatik."""
    enabled = body.get("watermark_enabled")
    if enabled is None:
        raise HTTPException(400, "watermark_enabled gerekli")
    return update_brand_settings({"watermark_enabled": bool(enabled)})


@router.post("/logo")
async def upload_logo(file: UploadFile = File(...)):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(415, "Sadece PNG, JPG veya WebP yüklenebilir")
    raw = await file.read()
    if len(raw) > 5 * 1024 * 1024:
        raise HTTPException(413, "Logo dosyası 5 MB'tan büyük olamaz")

    _ensure_bucket()

    png_bytes, filename = _to_png_bytes(raw, file.content_type or "image/png")
    path = f"logos/{filename}"

    supabase = get_supabase_client()
    # Varsa üstüne yaz
    try:
        supabase.storage.from_(BUCKET).remove([path])
    except Exception:
        pass
    supabase.storage.from_(BUCKET).upload(path, png_bytes, {"content-type": "image/png", "upsert": "true"})

    public_url = supabase.storage.from_(BUCKET).get_public_url(path)
    update_brand_settings({"logo_url": public_url, "watermark_enabled": True})

    # Önbelleği temizle
    import app.db.repositories.brand_repo as _br
    _br._logo_cache = None
    _br._logo_cache_url = None

    logger.info(f"[brand] logo yüklendi: {public_url}")
    return {"logo_url": public_url, "message": "Logo yüklendi, tüm videolara otomatik eklenecek"}


@router.delete("/logo")
def delete_logo():
    import app.db.repositories.brand_repo as _br
    _br._logo_cache = None
    _br._logo_cache_url = None
    update_brand_settings({"logo_url": None, "watermark_enabled": False})
    return {"message": "Logo kaldırıldı"}
