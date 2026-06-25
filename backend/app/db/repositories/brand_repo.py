"""Marka ayarları (logo, filigran) Supabase repo."""
import logging
from app.db.supabase import get_supabase_client

logger = logging.getLogger(__name__)
_SETTINGS_ID = "default"

_defaults: dict = {
    "logo_url": None,
    "watermark_enabled": True,
    "updated_at": None,
}

# Video türüne göre otomatik filigran ayarları
# SGS eğitim: silik merkez filigran (logo okunmayı engellemez)
# Motivasyon / kısa içerik: köşede görünür küçük logo
_VIDEO_TYPE_WATERMARK: dict[str, dict] = {
    "sgs_topic_video":    {"position": "center",       "opacity": 0.07, "size": 0.28},
    "sgs_question_video": {"position": "center",       "opacity": 0.07, "size": 0.28},
    "question_solution":  {"position": "center",       "opacity": 0.07, "size": 0.28},
    "topic_explanation":  {"position": "center",       "opacity": 0.06, "size": 0.25},
    "motivation_video":   {"position": "top-right",    "opacity": 0.90, "size": 0.11},
    "short":              {"position": "bottom-right", "opacity": 0.85, "size": 0.10},
    "reel":               {"position": "bottom-right", "opacity": 0.85, "size": 0.10},
    "video":              {"position": "center",       "opacity": 0.06, "size": 0.25},
    "post":               {"position": "bottom-right", "opacity": 0.90, "size": 0.11},
}

# Bellekte logo önbelleği (process yaşam süresi boyunca)
_logo_cache: bytes | None = None
_logo_cache_url: str | None = None


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
    """Logo baytlarını döndürür. Process içinde önbellekler."""
    global _logo_cache, _logo_cache_url
    settings = get_brand_settings()
    logo_url: str | None = settings.get("logo_url")
    if not logo_url:
        return None
    if _logo_cache and _logo_cache_url == logo_url:
        return _logo_cache
    try:
        sb = get_supabase_client()
        # URL'den path çıkar: .../object/public/brand-assets/logos/... → logos/...
        marker = "/brand-assets/"
        path = logo_url.split(marker)[-1] if marker in logo_url else None
        if not path:
            return None
        data = sb.storage.from_("brand-assets").download(path)
        _logo_cache = data
        _logo_cache_url = logo_url
        return data
    except Exception as e:
        logger.warning(f"[brand] logo indirilemedi: {e}")
        return None


def configure_video_watermark(video_type: str = "video") -> None:
    """Video üretiminden önce çağrılır. Tür bazlı otomatik filigran konfigürasyonu."""
    from app.modules.content.scene_engine import configure_watermark
    settings = get_brand_settings()
    if not settings.get("watermark_enabled", True):
        configure_watermark(None, enabled=False)
        return
    logo = get_logo_bytes()
    if not logo:
        configure_watermark(None, enabled=False)
        return
    cfg = _VIDEO_TYPE_WATERMARK.get(video_type, _VIDEO_TYPE_WATERMARK["video"])
    configure_watermark(
        logo,
        opacity=cfg["opacity"],
        position=cfg["position"],
        size=cfg["size"],
        enabled=True,
    )
    logger.info(f"[brand] filigran ayarlandı: tür={video_type} konum={cfg['position']} opaklık={cfg['opacity']}")
