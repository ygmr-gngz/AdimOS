"""Marka ayarları (logo, filigran) Supabase repo."""
import logging
from app.db.supabase import get_supabase_client

logger = logging.getLogger(__name__)
_SETTINGS_ID = "default"

_defaults = {
    "logo_url": None,
    "watermark_enabled": True,
    "watermark_opacity": 0.07,
    "watermark_position": "center",
    "watermark_size": 0.30,
    "logo_corner_position": "top-right",
}


def get_brand_settings() -> dict:
    try:
        supabase = get_supabase_client()
        resp = supabase.table("brand_settings").select("*").eq("id", _SETTINGS_ID).execute()
        return resp.data[0] if resp.data else _defaults
    except Exception as e:
        logger.warning(f"[brand] ayarlar alınamadı: {e}")
        return _defaults


def update_brand_settings(updates: dict) -> dict:
    supabase = get_supabase_client()
    resp = supabase.table("brand_settings").update(updates).eq("id", _SETTINGS_ID).execute()
    return resp.data[0] if resp.data else {}


def get_logo_bytes() -> bytes | None:
    """Logo URL'sini Supabase storage'dan indir, baytları döndür."""
    settings = get_brand_settings()
    logo_url = settings.get("logo_url")
    if not logo_url:
        return None
    try:
        from app.db.supabase import get_supabase_client as _sc
        sb = _sc()
        path = logo_url.split("/brand-assets/")[-1] if "/brand-assets/" in logo_url else None
        if not path:
            return None
        return sb.storage.from_("brand-assets").download(path)
    except Exception as e:
        logger.warning(f"[brand] logo indirilemedi: {e}")
        return None
