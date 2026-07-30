"""
Görsel kütüphane seçici — ADIM 5 (ÖNCELİK HATTI v3 §6.2–6.4).

Manifest: assets/library/manifest.json
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
import json
import logging
import pathlib
from typing import Optional

logger = logging.getLogger(__name__)

_MANIFEST_PATH = pathlib.Path(__file__).resolve().parents[4] / "assets" / "library" / "manifest.json"
_ASSET_REGISTRY_PATH = pathlib.Path(__file__).resolve().parents[4] / "assets" / "library" / "asset_registry.json"

# Önbellek: modül yüklendiğinde manifest okunur
_manifest_cache: Optional[dict] = None


def _load_manifest() -> dict:
    global _manifest_cache
    if _manifest_cache is not None:
        return _manifest_cache
    if not _MANIFEST_PATH.exists():
        logger.error(f"[visual_library] manifest bulunamadı: {_MANIFEST_PATH}")
        return {}
    try:
        _manifest_cache = json.loads(_MANIFEST_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.error(f"[visual_library] manifest parse hatası: {exc}")
        return {}
    return _manifest_cache


def _cache_key(theme: str, model: str, quality: str, variant_index: int) -> str:
    """§6.5.6 — Önbellek anahtarı."""
    manifest = _load_manifest()
    style = manifest.get("style_contract", {}).get("positive", "")
    raw = f"{theme}|{style}|{model}|{quality}|{variant_index}"
    return hashlib.sha256(raw.encode()).hexdigest()


def _deterministic_pick(candidates: list[dict], job_id: str, theme: str, idx: int = 0) -> dict:
    """§6.3 — Aynı job/theme için her zaman aynı görseli seçer."""
    raw = f"{job_id}|{theme}|{idx}"
    h = int(hashlib.sha256(raw.encode()).hexdigest(), 16)
    return candidates[h % len(candidates)]


def _load_asset_registry() -> list[dict]:
    """Üretilmiş görsellerin kayıt defteri."""
    if not _ASSET_REGISTRY_PATH.exists():
        return []
    try:
        return json.loads(_ASSET_REGISTRY_PATH.read_text(encoding="utf-8"))
    except Exception:
        return []


def _save_asset_registry(registry: list[dict]) -> None:
    _ASSET_REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    _ASSET_REGISTRY_PATH.write_text(
        json.dumps(registry, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def register_asset(asset: dict) -> None:
    """
    Üretilmiş görseli kayıt defterine ekler.
    Gerekli alanlar: asset_id, theme, source, license, model, quality,
                     prompt_hash, path, generated_at, sha256, ocr_clean, has_face
    """
    required = {"asset_id", "theme", "license", "path"}
    missing = required - set(asset.keys())
    if missing:
        raise ValueError(f"register_asset eksik alanlar: {sorted(missing)}")

    registry = _load_asset_registry()
    # Çift kayıt engeli
    if any(a.get("asset_id") == asset["asset_id"] for a in registry):
        logger.debug(f"[visual_library] Zaten kayıtlı: {asset['asset_id']}")
        return
    registry.append(asset)
    _save_asset_registry(registry)
    logger.info(f"[visual_library] Kaydedildi: {asset['asset_id']} (tema: {asset.get('theme')})")


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
        theme:          Görsel teması (manifest anahtarı)
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

    manifest = _load_manifest()
    theme_cfg = manifest.get("themes", {}).get(theme)
    if not theme_cfg:
        raise PipelineErrorException(
            "asset_license_missing",
            admin_detail={"reason": "unknown_theme", "theme": theme},
            stage="visual",
        )

    # Tema bu content_track için geçerli mi?
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

    # Kayıt defterinden bu temaya ait adaylar
    registry = _load_asset_registry()
    candidates = [a for a in registry if a.get("theme") == theme]

    # Lisans kontrolü: license alanı boş olan çıkar
    candidates = [a for a in candidates if a.get("license")]

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
                "total_in_theme": len([a for a in registry if a.get("theme") == theme]),
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
        Manifest'teki tema anahtarı ya da None
    """
    manifest = _load_manifest()
    all_themes = set(manifest.get("themes", {}).keys())

    # LLM visual_theme alanına güven — sadece manifest'te varsa
    if scene.get("visual_theme") in all_themes:
        return scene["visual_theme"]

    # Component bazlı varsayılan tema
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
        # Segment tipine göre öneri
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

    # Varsayılan
    if content_track == "danisan":
        return "ofis_muhasebe"
    return "calisma_masasi"


def library_status() -> dict:
    """
    Kütüphane doluluk durumunu raporlar — toplu üretim kararı için.
    Returns: {theme: {target, current, pct, needs_generation: bool}}
    """
    manifest = _load_manifest()
    registry = _load_asset_registry()

    result = {}
    for theme_key, cfg in manifest.get("themes", {}).items():
        target = cfg.get("target_variants", 15)
        current = sum(
            1 for a in registry
            if a.get("theme") == theme_key and a.get("license")
        )
        result[theme_key] = {
            "label": cfg.get("label", theme_key),
            "target": target,
            "current": current,
            "pct": round(current / target * 100) if target else 0,
            "needs_generation": current < target,
        }
    return result
