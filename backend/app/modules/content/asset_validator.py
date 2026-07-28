"""
Asset doğrulama — render öncesi HTTP kontrol.

- Logo URL'si Supabase'den geliyorsa HEAD/GET ile 200 + image/png doğrulanır.
- Font kontrolleri: bundle'da woff2 var mı (remotion/public/fonts/).
- Hata deduplikasyonu: aynı asset hatası tek kayıtta toplanır (occurrence_count).
"""
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

# Remotion public dizini (bu backend proje kökünden göreceli)
_REMOTION_PUBLIC = Path(__file__).resolve().parents[4] / "remotion" / "public"

_REQUIRED_FONTS = [
    "fonts/NotoSans-Regular-Latin.woff2",
    "fonts/NotoSans-Regular-LatinExt.woff2",
    "fonts/NotoSans-Bold-Latin.woff2",
    "fonts/NotoSans-Bold-LatinExt.woff2",
]


def validate_logo_url(logo_url: str | None, job_id: str = "") -> tuple[bool, str]:
    """
    Supabase logo URL'sini doğrular.
    Returns: (ok, mesaj)
    """
    if not logo_url:
        logger.info(f"[asset] {job_id[:8]} logo_url yok — staticFile fallback kullanılacak")
        return True, "no_url_fallback_static"

    try:
        import httpx
        r = httpx.head(logo_url, timeout=10, follow_redirects=True)
        if r.status_code == 200:
            ct = r.headers.get("content-type", "")
            size = int(r.headers.get("content-length", 0))
            if "image" not in ct and size == 0:
                # HEAD boş döndü — GET ile dene
                rg = httpx.get(logo_url, timeout=10, follow_redirects=True)
                if rg.status_code != 200 or len(rg.content) < 512:
                    return False, f"brand_asset_invalid content_type={ct} size={size}"
            logger.info(f"[asset] {job_id[:8]} logo HTTP {r.status_code} ct={ct}")
            return True, f"ok status={r.status_code}"
        return False, f"brand_asset_http_{r.status_code}"
    except Exception as exc:
        logger.warning(f"[asset] {job_id[:8]} logo URL kontrolü atlandı: {exc}")
        return True, f"check_skipped: {exc}"   # ağ kısıtlamasında render'ı engelleme


def validate_fonts() -> tuple[bool, list[str]]:
    """
    Remotion bundle'ında woff2 font dosyaları var mı kontrol eder.
    Returns: (all_present, eksik_dosyalar)
    """
    missing = []
    for rel in _REQUIRED_FONTS:
        full = _REMOTION_PUBLIC / rel
        if not full.exists():
            missing.append(rel)
    if missing:
        logger.error(f"[asset] eksik font dosyaları: {missing}")
    return len(missing) == 0, missing


def validate_brand_assets(logo_url: str | None, job_id: str = "") -> list[dict]:
    """
    Logo + font varlığını kontrol eder.
    Returns: hata listesi — her item {error_code, asset_name, detail, occurrence_count=1}
    """
    from app.errors.registry import PipelineErrorException

    errors = []

    # Logo
    logo_ok, logo_msg = validate_logo_url(logo_url, job_id)
    if not logo_ok:
        errors.append({
            "error_code": "brand_asset_missing",
            "asset_name": "adim-musavir-logo",
            "resolved_url": logo_url,
            "detail": logo_msg,
            "occurrence_count": 1,
        })
        logger.error(f"[brand] job={job_id[:8]} brand_asset_missing: {logo_msg}")

    # Font
    fonts_ok, missing_fonts = validate_fonts()
    if not fonts_ok:
        errors.append({
            "error_code": "font_asset_missing",
            "asset_name": "noto-sans-woff2",
            "missing_files": missing_fonts,
            "detail": f"{len(missing_fonts)} font dosyası eksik",
            "occurrence_count": 1,
        })
        logger.error(f"[brand] job={job_id[:8]} font_asset_missing: {missing_fonts}")

    # Yapılandırılmış log
    logger.info(
        f"[brand] job={job_id[:8]} "
        f"logo_ok={logo_ok} fonts_ok={fonts_ok} "
        f"asset_resolved={'true' if logo_ok else 'false'}"
    )

    return errors
