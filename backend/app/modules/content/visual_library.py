"""
Görsel kütüphane seçici — ADIM 5 (ÖNCELİK HATTI v3 §6.2–6.4).

Depolama: Supabase Postgres tablosu `visual_assets` + Supabase Storage bucket
`visual-library`. Repo kökündeki local dosya sistemi KULLANILMAZ — render
Remotion Lambda üzerinde çalışır ve backend'in local diskine hiçbir zaman
erişemez (gerçek HTTP URL şart), ayrıca Railway'de backend'in Docker build
context'i backend/ (Root Directory) — repo kökü runtime'da yok
(content_constants.py postmortem'i ile aynı hata sınıfı).

Tema kataloğu / stil sözleşmesi: app.core.visual_manifest (backend/ içinde
git'e commitli, sabit — serbest metin tema/prompt yok).

Spec §6.3 seçim algoritması:
  1. Sahne anahtar kelimeleri → tag eşleşmesi → aday havuzu
  2. Son 10 videoda kullanılanları çıkar
  3. Aynı video içinde tekrarı çıkar
  4. has_face=true: en fazla 3 adet
  5. Deterministik seçim: sha256(job_id + theme + index) % len(candidates)

Lisans zorunluluğu: license alanı boş olan görsel render'a giremez (asset_license_missing).
"""
from __future__ import annotations

import hashlib
import logging
from typing import Optional

from app.core.visual_manifest import STYLE_CONTRACT, THEMES
from app.db.supabase import get_supabase_client

logger = logging.getLogger(__name__)

VISUAL_ASSETS_TABLE = "visual_assets"


def cache_key(theme: str, model: str, quality: str, variant_index: int) -> str:
    """§6.5.6 — Önbellek anahtarı. Stil değişirse (aynı tema için) yeni üretim tetiklenir."""
    raw = f"{theme}|{STYLE_CONTRACT['positive']}|{model}|{quality}|{variant_index}"
    return hashlib.sha256(raw.encode()).hexdigest()


def _deterministic_pick(candidates: list[dict], job_id: str, theme: str, idx: int = 0) -> dict:
    """§6.3 — Aynı job/theme için her zaman aynı görseli seçer."""
    raw = f"{job_id}|{theme}|{idx}"
    h = int(hashlib.sha256(raw.encode()).hexdigest(), 16)
    return candidates[h % len(candidates)]


def register_asset(asset: dict) -> None:
    """
    Üretilmiş görseli visual_assets tablosuna ekler.
    Gerekli alanlar: asset_id, theme, cache_key, license, model, quality,
                     storage_path, public_url, sha256
    """
    required = {"asset_id", "theme", "cache_key", "storage_path", "public_url", "sha256"}
    missing = required - set(asset.keys())
    if missing:
        raise ValueError(f"register_asset eksik alanlar: {sorted(missing)}")

    supabase = get_supabase_client()
    try:
        existing = (
            supabase.table(VISUAL_ASSETS_TABLE)
            .select("asset_id")
            .eq("asset_id", asset["asset_id"])
            .limit(1)
            .execute()
        )
        if existing.data:
            logger.debug(f"[visual_library] Zaten kayıtlı: {asset['asset_id']}")
            return
        supabase.table(VISUAL_ASSETS_TABLE).insert(asset).execute()
        logger.info(f"[visual_library] Kaydedildi: {asset['asset_id']} (tema: {asset.get('theme')})")
    except Exception as exc:
        logger.error(f"[visual_library] DB kayıt hatası: {exc}")
        raise


def select_asset(
    theme: str,
    job_id: str,
    content_track: str = "ogrenci",
    used_in_video: Optional[list[str]] = None,
    recently_used: Optional[list[str]] = None,
    face_count: int = 0,
) -> dict:
    """
    §6.3 algoritmasına göre görsel seçer.

    Args:
        theme:          Görsel teması (THEMES anahtarı)
        job_id:         Deterministik seçim için iş kimliği
        content_track:  'ogrenci' | 'danisan'
        used_in_video:  Bu video içinde kullanılmış asset_id'ler
        recently_used:  Son 10 videoda kullanılmış asset_id'ler
        face_count:     Bu videoda has_face=true olan görsel sayısı

    Returns:
        Seçilen asset kaydı

    Raises:
        PipelineErrorException: Geçerli aday bulunamazsa
    """
    from app.errors.registry import PipelineErrorException

    used_in_video = used_in_video or []
    recently_used = recently_used or []

    theme_cfg = THEMES.get(theme)
    if not theme_cfg:
        raise PipelineErrorException(
            "asset_license_missing",
            admin_detail={"reason": "unknown_theme", "theme": theme},
            stage="visual",
        )

    allowed_tracks = theme_cfg.get("content_tracks", ["ogrenci"])
    if content_track not in allowed_tracks:
        raise PipelineErrorException(
            "asset_license_missing",
            admin_detail={
                "reason": "theme_not_for_track",
                "theme": theme,
                "content_track": content_track,
                "allowed": allowed_tracks,
            },
            stage="visual",
        )

    supabase = get_supabase_client()
    try:
        resp = (
            supabase.table(VISUAL_ASSETS_TABLE)
            .select("*")
            .eq("theme", theme)
            .execute()
        )
        registry_rows = resp.data or []
    except Exception as exc:
        logger.error(f"[visual_library] DB okuma hatası: {exc}")
        raise PipelineErrorException(
            "asset_license_missing",
            admin_detail={"reason": "db_read_failed", "theme": theme, "error": str(exc)},
            stage="visual",
        )

    # Lisans kontrolü: license alanı boş olan çıkar
    candidates = [a for a in registry_rows if a.get("license")]

    # Son 10 videoda kullanılanları çıkar
    candidates = [a for a in candidates if a.get("asset_id") not in recently_used]

    # Aynı video içinde tekrarı çıkar
    candidates = [a for a in candidates if a.get("asset_id") not in used_in_video]

    # has_face=true kotası: videoda en fazla 3 adet
    if face_count >= 3:
        candidates = [a for a in candidates if not a.get("has_face", False)]

    if not candidates:
        raise PipelineErrorException(
            "asset_license_missing",
            admin_detail={
                "reason": "no_valid_candidate",
                "theme": theme,
                "total_in_theme": len(registry_rows),
                "after_filters": 0,
            },
            stage="visual",
        )

    return _deterministic_pick(candidates, job_id, theme)


def theme_for_scene(scene: dict, content_track: str = "ogrenci") -> Optional[str]:
    """
    Sahne bileşeni ve içeriğine göre uygun temayı belirler.
    LLM'den gelen 'visual_theme' alanı varsa onu kullanır (güvenli allowlist ile).

    Returns:
        THEMES anahtarı ya da None
    """
    all_themes = set(THEMES.keys())

    # LLM visual_theme alanına güven — sadece THEMES'te varsa
    if scene.get("visual_theme") in all_themes:
        return scene["visual_theme"]

    component = scene.get("component", "")
    segment_type = scene.get("segment_type", "")

    # text_only sahneler görsel gerektirmez
    visual_source = scene.get("visual_source", "")
    if visual_source == "text_only":
        return None

    # Motivasyon sahneleri fotoğraf tabanlı
    if "Motivation" in component:
        if content_track == "danisan":
            return "ofis_muhasebe"
        _motivation_map = {
            "hook":    "yeniden_baslama",
            "problem": "mola",
            "empathy": "sabah_isik",
            "turn":    "ilerleme",
            "step":    "calisma_masasi",
            "proof":   "kitap_defter",
            "focus":   "takvim_plan",
            "outro":   "ogrenci_calisir",
        }
        return _motivation_map.get(segment_type, "calisma_masasi")

    # Kart/tablo sahneleri görsel gerektirmez (card/table/journal visual_source)
    if visual_source in ("card", "table", "journal", "board"):
        return None

    if content_track == "danisan":
        return "ofis_muhasebe"
    return "calisma_masasi"


MIN_VARIANTS_READY = 5


def motivation_library_ready() -> tuple[bool, dict]:
    """
    Motivasyon üretimi açılmadan önce her temanın en az MIN_VARIANTS_READY
    lisanslı varyantı olmalı — boş/yarım kütüphaneyle iş başlatılmaz
    (asset_license_missing ile sessizce yarım video üretmek yerine, iş hiç
    kuyruğa girmez; bkz. app/api/routes/video.py /create motivasyon kapısı).

    Returns: (ready, status) — status = library_status() çıktısı
    """
    status = library_status()
    ready = all(v["current"] >= MIN_VARIANTS_READY for v in status.values())
    return ready, status


def library_status() -> dict:
    """
    Kütüphane doluluk durumunu raporlar — toplu üretim kararı için.
    Returns: {theme: {target, current, pct, needs_generation: bool}}
    """
    supabase = get_supabase_client()
    try:
        resp = supabase.table(VISUAL_ASSETS_TABLE).select("theme, license").execute()
        rows = resp.data or []
    except Exception as exc:
        logger.error(f"[visual_library] library_status DB hatası: {exc}")
        rows = []

    result = {}
    for theme_key, cfg in THEMES.items():
        target = cfg.get("target_variants", 15)
        current = sum(1 for a in rows if a.get("theme") == theme_key and a.get("license"))
        result[theme_key] = {
            "label": cfg.get("label", theme_key),
            "target": target,
            "current": current,
            "pct": round(current / target * 100) if target else 0,
            "needs_generation": current < target,
        }
    return result
