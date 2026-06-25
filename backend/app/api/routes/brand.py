"""Marka varlıkları — logo yükleme ve filigran ayarları."""
import logging
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from app.db.repositories.brand_repo import get_brand_settings, update_brand_settings
from app.db.storage import upload_file
from app.db.supabase import get_supabase_client

logger = logging.getLogger(__name__)
router = APIRouter()

ALLOWED_IMG_TYPES = {"image/png", "image/jpeg", "image/jpg", "image/svg+xml", "image/webp"}
VALID_POSITIONS = {"center", "top-right", "top-left", "bottom-right", "bottom-left"}


class BrandSettingsUpdate(BaseModel):
    watermark_enabled: bool | None = None
    watermark_opacity: float | None = None
    watermark_position: str | None = None
    watermark_size: float | None = None
    logo_corner_position: str | None = None


@router.get("/settings")
def get_settings():
    return get_brand_settings()


@router.put("/settings")
def update_settings(body: BrandSettingsUpdate):
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="Güncellenecek alan yok")
    if "watermark_position" in updates and updates["watermark_position"] not in VALID_POSITIONS:
        raise HTTPException(400, f"Geçersiz konum. Seçenekler: {VALID_POSITIONS}")
    if "watermark_opacity" in updates:
        updates["watermark_opacity"] = max(0.0, min(float(updates["watermark_opacity"]), 1.0))
    if "watermark_size" in updates:
        updates["watermark_size"] = max(0.05, min(float(updates["watermark_size"]), 0.8))
    return update_brand_settings(updates)


@router.post("/logo")
async def upload_logo(file: UploadFile = File(...)):
    if file.content_type not in ALLOWED_IMG_TYPES:
        raise HTTPException(415, "Sadece PNG, JPG, SVG veya WebP yüklenebilir")
    data = await file.read()
    if len(data) > 5 * 1024 * 1024:
        raise HTTPException(413, "Logo dosyası 5 MB'tan büyük olamaz")

    path = f"logos/adim_logo{_ext(file.filename)}"
    upload_file("brand-assets", path, data)

    supabase = get_supabase_client()
    public_url = supabase.storage.from_("brand-assets").get_public_url(path)
    updated = update_brand_settings({"logo_url": public_url})
    logger.info(f"[brand] logo yüklendi: {public_url}")
    return {"logo_url": public_url, "settings": updated}


@router.delete("/logo")
def delete_logo():
    update_brand_settings({"logo_url": None})
    return {"message": "Logo kaldırıldı"}


def _ext(filename: str | None) -> str:
    if not filename or "." not in filename:
        return ".png"
    return "." + filename.rsplit(".", 1)[-1].lower()
