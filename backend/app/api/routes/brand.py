"""Marka varlıkları — logo yükleme (ayarlar otomatik)."""
import io
import logging
from pathlib import Path
from fastapi import APIRouter, HTTPException, UploadFile, File
from app.db.repositories.brand_repo import get_brand_settings, update_brand_settings
from app.db.supabase import get_supabase_client

logger = logging.getLogger(__name__)
router = APIRouter()

BUCKET = "brand-assets"

ALLOWED_MIME: set[str] = {"image/png", "image/jpeg", "image/webp"}
EXTENSION_MIME: dict[str, str] = {
    ".png":  "image/png",
    ".jpg":  "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
}
MAX_BYTES = 5 * 1024 * 1024  # 5 MB


def _resolve_mime(file: UploadFile) -> str | None:
    """content_type önce, yoksa uzantıdan çöz."""
    ct = (file.content_type or "").strip().lower().split(";")[0]
    if ct in ALLOWED_MIME:
        return ct
    if file.filename:
        ext = Path(file.filename).suffix.lower()
        return EXTENSION_MIME.get(ext)
    return ct or None


def _ensure_bucket() -> None:
    supabase = get_supabase_client()
    try:
        buckets = supabase.storage.list_buckets()
        names = [b.name if hasattr(b, "name") else b.get("name", "") for b in buckets]
        if BUCKET not in names:
            supabase.storage.create_bucket(BUCKET, options={"public": True})
            logger.info(f"[brand] '{BUCKET}' bucket oluşturuldu")
    except Exception as e:
        logger.warning(f"[brand] bucket kontrol hatası: {e}")


def _to_png_bytes(raw: bytes, mime: str) -> bytes:
    if mime == "image/png":
        return raw
    from PIL import Image
    img = Image.open(io.BytesIO(raw)).convert("RGBA")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


# Alfa min üst sınırı: 250 (255 değil) — hafif JPEG/webp sıkıştırma artefaktları
# kenarlarda alfa'yı 250-254 gibi değerlere kaydırabilir, gerçek şeffaflık yine
# de tespit edilebilsin diye küçük tolerans bırakıldı.
_OPAQUE_ALPHA_THRESHOLD = 250


def _validate_transparency(png_bytes: bytes) -> None:
    """
    Marka logosu şeffaf arka planlı olmalı — opak bir dosya her render'da köşede
    beyaz/renkli bir kutu olarak görünür ve fark edilmesi zor (canlı ortamda
    haftalarca sessizce üretime giden bir kopya bu şekilde bulundu — 2026-08-04
    postmortem: JPEG kaynaklı bir logo .convert('RGBA') ile PNG'ye çevrilmiş,
    RGBA mode kazanmış ama alfa kanalı uçtan uca 255'te kalmış).
    Raises ValueError — çağıran HTTPException'a çevirir.
    """
    from PIL import Image
    import numpy as np
    img = Image.open(io.BytesIO(png_bytes)).convert("RGBA")
    alpha = np.array(img)[:, :, 3]
    if alpha.min() >= _OPAQUE_ALPHA_THRESHOLD:
        raise ValueError("Logo şeffaf arka planlı PNG olmalı.")


def _log_asset(file_name: str, file_path: str, public_url: str, mime: str, size: int) -> None:
    try:
        sb = get_supabase_client()
        sb.table("brand_assets").insert({
            "asset_type": "logo",
            "file_name": file_name,
            "file_path": file_path,
            "public_url": public_url,
            "mime_type": mime,
            "size_bytes": size,
        }).execute()
    except Exception as e:
        logger.debug(f"[brand] brand_assets kaydı atlandı: {e}")


@router.get("/settings")
def get_settings():
    return get_brand_settings()


@router.put("/settings")
def toggle_watermark(body: dict):
    enabled = body.get("watermark_enabled")
    if enabled is None:
        raise HTTPException(400, "watermark_enabled gerekli")
    return update_brand_settings({"watermark_enabled": bool(enabled)})


@router.post("/logo")
async def upload_logo(file: UploadFile = File(...)):
    # 1. MIME tipi tespiti (content_type + uzantı fallback)
    mime = _resolve_mime(file)
    if not mime:
        logger.warning(f"[brand] tanımsız dosya tipi — content_type={file.content_type!r} filename={file.filename!r}")
        raise HTTPException(
            415,
            detail={
                "error": "format",
                "message": f"Dosya formatı tanınamadı. PNG, JPG veya WebP yükleyin. (Alınan: {file.content_type!r})",
            },
        )

    # 2. Dosya içeriği
    try:
        raw = await file.read()
    except Exception as e:
        logger.error(f"[brand] dosya okunamadı: {e}")
        raise HTTPException(400, detail={"error": "read", "message": "Dosya okunamadı. Tekrar deneyin."})

    # 3. Boyut kontrolü
    if len(raw) > MAX_BYTES:
        raise HTTPException(
            413,
            detail={
                "error": "size",
                "message": f"Dosya çok büyük ({len(raw) // 1024 // 1024:.1f} MB). Maks 5 MB yüklenebilir.",
            },
        )

    # 4. Bucket garantisi
    _ensure_bucket()

    # 5. PNG'ye dönüştür + yükle
    path = "logos/adim_logo.png"
    try:
        png_bytes = _to_png_bytes(raw, mime)
    except Exception as e:
        logger.error(f"[brand] görsel dönüştürülemedi: {e}")
        raise HTTPException(422, detail={"error": "convert", "message": "Görsel işlenemedi. Farklı bir dosya deneyin."})

    # 5b. Şeffaflık kapısı — opak bir logo her render'ı sessizce bozar (köşede
    # beyaz/renkli kutu). JPEG kaynaklı dosyalar burada HER ZAMAN reddedilir
    # (JPEG yapısal olarak alfa taşıyamaz) — bu doğru davranış, format hatası değil.
    try:
        _validate_transparency(png_bytes)
    except ValueError as e:
        logger.warning(f"[brand] opak logo reddedildi: filename={file.filename!r} mime={mime}")
        raise HTTPException(422, detail={"error": "opaque", "message": str(e)})

    supabase = get_supabase_client()
    try:
        supabase.storage.from_(BUCKET).remove([path])
    except Exception:
        pass

    try:
        supabase.storage.from_(BUCKET).upload(
            path, png_bytes, {"content-type": "image/png", "upsert": "true"}
        )
    except Exception as e:
        logger.error(f"[brand] Supabase yükleme hatası: {e}")
        raise HTTPException(
            502,
            detail={"error": "storage", "message": f"Storage yükleme hatası: {e}"},
        )

    # 6. Public URL al
    try:
        public_url = supabase.storage.from_(BUCKET).get_public_url(path)
    except Exception as e:
        raise HTTPException(502, detail={"error": "url", "message": f"URL alınamadı: {e}"})

    # 7. Ayarları güncelle
    try:
        update_brand_settings({"logo_url": public_url, "watermark_enabled": True})
    except Exception as e:
        logger.error(f"[brand] brand_settings güncellenemedi: {e}")
        raise HTTPException(500, detail={"error": "db", "message": "Logo URL veritabanına kaydedilemedi."})

    # 8. Önbelleği temizle
    import app.db.repositories.brand_repo as _br
    _br._logo_cache = None
    _br._logo_cache_url = None

    # 9. brand_assets kaydı (tablo yoksa atla)
    _log_asset(file.filename or "adim_logo", path, public_url, "image/png", len(png_bytes))

    logger.info(f"[brand] logo yüklendi: {public_url} ({len(png_bytes)//1024} KB)")
    return {
        "success": True,
        "logo_url": public_url,
        "message": "Logo başarıyla yüklendi",
    }


@router.delete("/logo")
def delete_logo():
    import app.db.repositories.brand_repo as _br
    _br._logo_cache = None
    _br._logo_cache_url = None
    update_brand_settings({"logo_url": None, "watermark_enabled": False})
    return {"message": "Logo kaldırıldı"}
