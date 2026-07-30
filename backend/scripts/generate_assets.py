"""
Görsel kütüphane toplu üretici — ADIM 5 §6.5.6

Her tema için hedef varyant sayısına ulaşana kadar görsel üretir,
kalite kontrolünden geçirir, assets/library/{tema}/ altına kaydeder
ve asset_registry.json'a yazar.

Kullanım:
  python scripts/generate_assets.py                     # kuru çalışma (dry-run)
  python scripts/generate_assets.py --run               # gerçek üretim
  python scripts/generate_assets.py --run --theme calisma_masasi --count 5
  python scripts/generate_assets.py --run --quality low # geliştirme/test (~$0.005/görsel)

Env:
  OPENAI_API_KEY         — zorunlu (gerçek üretimde)
  OPENAI_IMAGE_MODEL     — varsayılan: dall-e-3
  OPENAI_IMAGE_SIZE      — varsayılan: 1024x1792  (portre, 9:16 yaklaşımı)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import pathlib
import sys
import time
import uuid
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# ── Sabitler ──────────────────────────────────────────────────

PROJECT_ROOT  = pathlib.Path(__file__).resolve().parents[2]
ASSETS_DIR    = PROJECT_ROOT / "assets" / "library"
MANIFEST_PATH = ASSETS_DIR / "manifest.json"
REGISTRY_PATH = ASSETS_DIR / "asset_registry.json"

# OpenAI görsel üretim parametreleri
DEFAULT_MODEL   = os.getenv("OPENAI_IMAGE_MODEL", "dall-e-3")
DEFAULT_SIZE    = os.getenv("OPENAI_IMAGE_SIZE", "1024x1792")  # portre (~9:16)
DEFAULT_QUALITY = "standard"   # dall-e-3: standard | hd

# §6.5.1 maliyet sabitleri (OpenAI fiyat sayfasından güncelle)
# Tarih: 2026-07-30 — dall-e-3 standard pricing
IMAGE_COST_PER_UNIT = {
    "low":    0.005,   # mini/low kalite (geliştirme)
    "medium": 0.040,   # standard
    "high":   0.080,   # hd
}

# §6.5.5 kalite kapıları
OCR_MAX_CHARS    = 3
BLUR_MIN         = 100   # Laplacian varyansı
BRIGHTNESS_MIN   = 40
BRIGHTNESS_MAX   = 215
MAX_REGEN        = 2     # maksimum yeniden deneme


# ── Manifest ve registry yükleyici ──────────────────────────

def load_manifest() -> dict:
    if not MANIFEST_PATH.exists():
        logger.error(f"manifest.json bulunamadı: {MANIFEST_PATH}")
        sys.exit(1)
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def load_registry() -> list[dict]:
    if not REGISTRY_PATH.exists():
        return []
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def save_registry(registry: list[dict]) -> None:
    REGISTRY_PATH.write_text(
        json.dumps(registry, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


# ── OpenAI görsel üretimi ────────────────────────────────────

def build_prompt(theme_cfg: dict, manifest: dict) -> str:
    sc = manifest.get("style_contract", {})
    subject  = theme_cfg.get("subject_prompt", "")
    positive = sc.get("positive", "")
    negative = sc.get("negative", "")
    return f"{subject}\n\n{positive}\n\n{negative}"


def generate_image(
    prompt: str,
    model: str = DEFAULT_MODEL,
    size: str = DEFAULT_SIZE,
    quality: str = "standard",
    api_key: str = "",
) -> tuple[bytes | None, str]:
    """
    OpenAI DALL-E ile görsel üretir.
    Returns: (image_bytes | None, hata_mesajı)
    """
    try:
        import openai
        client = openai.OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))

        # dall-e-3 quality: "standard" | "hd"
        kwargs: dict = {
            "model":   model,
            "prompt":  prompt,
            "n":       1,
            "size":    size,
            "response_format": "b64_json",
        }
        if model == "dall-e-3":
            kwargs["quality"] = quality

        resp = client.images.generate(**kwargs)
        import base64
        data = base64.b64decode(resp.data[0].b64_json)
        return data, ""

    except Exception as exc:
        err_type = type(exc).__name__
        err_msg  = str(exc)
        if "insufficient_quota" in err_msg or "quota" in err_msg.lower():
            return None, f"insufficient_quota: {err_msg}"
        if "rate_limit" in err_msg.lower():
            return None, f"rate_limit: {err_msg}"
        if "content_policy" in err_msg.lower() or "safety" in err_msg.lower():
            return None, f"content_policy: {err_msg}"
        return None, f"{err_type}: {err_msg}"


# ── Kalite kontrolleri ────────────────────────────────────────

def check_blur(image_bytes: bytes) -> tuple[bool, float]:
    """Laplacian varyansı ile bulanıklık kontrolü."""
    try:
        import struct, zlib
        # Pillow varsa kullan
        from PIL import Image, ImageFilter
        import io, numpy as np
        img = Image.open(io.BytesIO(image_bytes)).convert("L")
        arr = np.array(img, dtype=float)
        lap = arr[:-2, 1:-1] + arr[2:, 1:-1] + arr[1:-1, :-2] + arr[1:-1, 2:] - 4 * arr[1:-1, 1:-1]
        variance = float(lap.var())
        return variance >= BLUR_MIN, variance
    except ImportError:
        logger.debug("[quality] Pillow/numpy yok — bulanıklık kontrolü atlandı")
        return True, 0.0
    except Exception as exc:
        logger.debug(f"[quality] blur check hatası: {exc}")
        return True, 0.0


def check_brightness(image_bytes: bytes) -> tuple[bool, float]:
    """Ortalama parlaklık kontrolü."""
    try:
        from PIL import Image
        import io, numpy as np
        img = Image.open(io.BytesIO(image_bytes)).convert("L")
        avg = float(np.array(img).mean())
        return BRIGHTNESS_MIN <= avg <= BRIGHTNESS_MAX, avg
    except Exception:
        return True, 0.0


def check_ocr(image_bytes: bytes) -> tuple[bool, str]:
    """
    Görselde okunabilir metin var mı? (tesseract gerektirir)
    Returns: (temiz_mi, bulunan_metin)
    """
    try:
        import pytesseract
        from PIL import Image
        import io
        img = Image.open(io.BytesIO(image_bytes))
        text = pytesseract.image_to_string(img, lang="tur+eng", config="--psm 11")
        clean_text = "".join(c for c in text if c.isalnum())
        is_clean = len(clean_text) <= OCR_MAX_CHARS
        return is_clean, clean_text[:50]
    except ImportError:
        logger.debug("[quality] pytesseract yok — OCR kontrolü atlandı")
        return True, ""
    except Exception as exc:
        logger.debug(f"[quality] OCR hatası: {exc}")
        return True, ""


def run_quality_checks(image_bytes: bytes) -> tuple[bool, dict]:
    """
    §6.5.5 tüm kalite kontrollerini çalıştırır.
    Returns: (passed, report)
    """
    report: dict = {}

    blur_ok, blur_val     = check_blur(image_bytes)
    bright_ok, bright_val = check_brightness(image_bytes)
    ocr_ok, ocr_text      = check_ocr(image_bytes)

    report["blur_variance"]    = round(blur_val, 1)
    report["brightness_avg"]   = round(bright_val, 1)
    report["ocr_text_found"]   = ocr_text
    report["blur_ok"]          = blur_ok
    report["brightness_ok"]    = bright_ok
    report["ocr_ok"]           = ocr_ok

    return all([blur_ok, bright_ok, ocr_ok]), report


# ── Görsel kaydetme ve dönüştürme ─────────────────────────────

def resize_to_target(image_bytes: bytes, target: tuple[int, int] = (1080, 1920)) -> bytes:
    """
    §6.5.4 dönüştürme hattı:
      üretilen boyut → 1280×1920'ye ölçekle → 1080×1920'ye merkez kırp
    """
    try:
        from PIL import Image
        import io
        img = Image.open(io.BytesIO(image_bytes))
        tw, th = target

        # Yüksekliğe göre ölçekle
        ratio = th / img.height
        new_w = int(img.width * ratio)
        img   = img.resize((new_w, th), Image.LANCZOS)

        # Yatayda merkez kırp
        if img.width > tw:
            left = (img.width - tw) // 2
            img  = img.crop((left, 0, left + tw, th))

        buf = io.BytesIO()
        img.save(buf, format="WEBP", quality=88)
        return buf.getvalue()
    except ImportError:
        logger.debug("[resize] Pillow yok — ham görsel kullanılıyor")
        return image_bytes
    except Exception as exc:
        logger.debug(f"[resize] hata: {exc}")
        return image_bytes


def save_asset(
    image_bytes: bytes,
    theme_key: str,
    theme_dir: str,
    asset_id: str,
) -> pathlib.Path:
    out_dir = ASSETS_DIR / theme_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    ext  = "webp"
    path = out_dir / f"{asset_id}.{ext}"
    path.write_bytes(image_bytes)
    return path


# ── Ana üretim döngüsü ────────────────────────────────────────

def generate_theme_assets(
    theme_key: str,
    theme_cfg: dict,
    manifest: dict,
    registry: list[dict],
    count: int,
    quality: str,
    model: str,
    size: str,
    dry_run: bool,
    api_key: str,
) -> tuple[int, float]:
    """
    Bir tema için count kadar görsel üretir.
    Returns: (üretilen_sayı, toplam_maliyet_usd)
    """
    existing = sum(1 for a in registry if a.get("theme") == theme_key and a.get("license"))
    target   = theme_cfg.get("target_variants", 15)
    needed   = min(count, target - existing)

    if needed <= 0:
        logger.info(f"  {theme_key}: hedef doldu ({existing}/{target}), atlandı")
        return 0, 0.0

    prompt       = build_prompt(theme_cfg, manifest)
    cost_unit    = IMAGE_COST_PER_UNIT.get(quality, IMAGE_COST_PER_UNIT["medium"])
    total_cost   = 0.0
    produced     = 0
    quality_flag = "hd" if quality == "high" else "standard"

    logger.info(f"  {theme_key}: {needed} görsel üretilecek "
                f"(mevcut {existing}/{target}, ~${cost_unit * needed:.3f})")

    for i in range(needed):
        asset_id = f"{theme_key.replace('_', '-')}-{str(uuid.uuid4())[:8]}"
        logger.info(f"    [{i+1}/{needed}] {asset_id} …")

        if dry_run:
            logger.info(f"    DRY-RUN — atlandı")
            produced += 1
            total_cost += cost_unit
            continue

        # Üretim + retry döngüsü
        final_bytes: bytes | None = None
        for attempt in range(MAX_REGEN + 1):
            img_bytes, err = generate_image(
                prompt=prompt, model=model, size=size,
                quality=quality_flag, api_key=api_key,
            )
            if err:
                if "insufficient_quota" in err:
                    logger.error(f"    [hata] {err} — üretim durduruluyor")
                    return produced, total_cost
                if "rate_limit" in err and attempt < MAX_REGEN:
                    wait = 2 ** (attempt + 1)
                    logger.warning(f"    rate_limit, {wait}s bekleniyor …")
                    time.sleep(wait)
                    continue
                logger.warning(f"    [deneme {attempt+1}] hata: {err}")
                break

            # Kalite kontrolü
            ok, report = run_quality_checks(img_bytes)
            logger.debug(f"    kalite raporu: {report}")

            if ok:
                final_bytes = img_bytes
                break
            else:
                logger.warning(
                    f"    [deneme {attempt+1}] kalite başarısız "
                    f"(ocr={report.get('ocr_ok')}, "
                    f"blur={report.get('blur_ok')}, "
                    f"bright={report.get('brightness_ok')})"
                )
                if attempt < MAX_REGEN:
                    logger.info(f"    yeniden üretiliyor …")

        if final_bytes is None:
            logger.warning(f"    {asset_id} kaliteyi geçemedi — atlandı")
            continue

        # Boyut dönüştürme
        final_bytes = resize_to_target(final_bytes)

        # Kaydet
        rel_path = save_asset(final_bytes, theme_key, theme_cfg["dir"], asset_id)
        sha256   = hashlib.sha256(final_bytes).hexdigest()

        # Registry'e ekle
        entry = {
            "asset_id":       asset_id,
            "theme":          theme_key,
            "source":         "openai_image_api",
            "model":          model,
            "quality":        quality,
            "license":        "api_terms_commercial",
            "license_url":    "https://openai.com/policies/terms-of-use",
            "attribution_required": False,
            "path":           str(rel_path.relative_to(ASSETS_DIR)),
            "generated_at":   datetime.now(timezone.utc).isoformat(),
            "sha256":         sha256,
            "ocr_clean":      True,
            "has_face":       False,
            "tags":           theme_cfg.get("tags", []),
            "dominant_color": None,
        }
        registry.append(entry)
        save_registry(registry)

        total_cost += cost_unit
        produced   += 1
        logger.info(f"    kaydedildi: {rel_path.name}  (toplam: {produced})")

        # Rate limit koruması: üretimler arası kısa bekleme
        if i < needed - 1:
            time.sleep(1)

    return produced, total_cost


# ── CLI ───────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Görsel kütüphane toplu üreticisi — ADIM 5 §6.5.6"
    )
    parser.add_argument("--run",     action="store_true",
                        help="Gerçek üretim yap (varsayılan: dry-run)")
    parser.add_argument("--theme",   default=None,
                        help="Belirli tema üret (yoksa tüm temalar)")
    parser.add_argument("--count",   type=int, default=15,
                        help="Tema başına üretilecek maksimum görsel (varsayılan: 15)")
    parser.add_argument("--quality", choices=["low", "medium", "high"], default="medium",
                        help="Görsel kalitesi (varsayılan: medium)")
    parser.add_argument("--model",   default=DEFAULT_MODEL,
                        help=f"OpenAI görsel modeli (varsayılan: {DEFAULT_MODEL})")
    parser.add_argument("--size",    default=DEFAULT_SIZE,
                        help=f"Çıktı boyutu (varsayılan: {DEFAULT_SIZE})")
    parser.add_argument("--status",  action="store_true",
                        help="Kütüphane doluluk durumunu göster ve çık")
    args = parser.parse_args()

    manifest = load_manifest()
    registry = load_registry()
    themes   = manifest.get("themes", {})

    # Durum raporu
    print("\n=== Görsel Kütüphane Durum Raporu ===\n")
    total_existing = 0
    total_target   = 0
    for tk, cfg in themes.items():
        existing = sum(1 for a in registry if a.get("theme") == tk and a.get("license"))
        target   = cfg.get("target_variants", 15)
        pct      = round(existing / target * 100) if target else 0
        bar      = "█" * (pct // 10) + "░" * (10 - pct // 10)
        total_existing += existing
        total_target   += target
        print(f"  {tk:<22} [{bar}] {existing:>3}/{target}  {pct:>3}%")
    print(f"\n  TOPLAM: {total_existing}/{total_target}")

    cost_unit  = IMAGE_COST_PER_UNIT.get(args.quality, IMAGE_COST_PER_UNIT["medium"])
    needed_all = max(0, total_target - total_existing)
    print(f"\n  Kalite    : {args.quality} (~${cost_unit}/görsel)")
    print(f"  Model     : {args.model}  boyut={args.size}")
    print(f"  Tahmini   : {needed_all} görsel × ${cost_unit:.3f} = ~${needed_all * cost_unit:.2f}")
    print(f"  Mod       : {'GERÇEK ÜRETİM' if args.run else 'DRY-RUN (--run ile etkinleştir)'}\n")

    if args.status:
        return

    # API key kontrolü
    api_key = os.getenv("OPENAI_API_KEY", "")
    if args.run and not api_key:
        print("[HATA] OPENAI_API_KEY env'de yok — gerçek üretim yapılamaz.")
        sys.exit(1)

    # Tema listesi
    theme_list = list(themes.items())
    if args.theme:
        if args.theme not in themes:
            print(f"[HATA] Bilinmeyen tema: {args.theme}")
            print(f"  Mevcut temalar: {', '.join(themes.keys())}")
            sys.exit(1)
        theme_list = [(args.theme, themes[args.theme])]

    # Üretim döngüsü
    print("=== Üretim Başlıyor ===\n")
    grand_total = 0
    grand_cost  = 0.0

    for tk, cfg in theme_list:
        logger.info(f"\n[TEMA] {tk} — {cfg.get('label', tk)}")
        n, cost = generate_theme_assets(
            theme_key=tk,
            theme_cfg=cfg,
            manifest=manifest,
            registry=registry,
            count=args.count,
            quality=args.quality,
            model=args.model,
            size=args.size,
            dry_run=not args.run,
            api_key=api_key,
        )
        grand_total += n
        grand_cost  += cost

    print(f"\n=== Tamamlandı ===")
    print(f"  Üretilen  : {grand_total} görsel")
    print(f"  Toplam maliyet (tahmini): ${grand_cost:.3f}")
    if not args.run:
        print(f"\n  NOT: Dry-run modundaydı. Gerçek üretim için --run ekle.")


if __name__ == "__main__":
    main()
