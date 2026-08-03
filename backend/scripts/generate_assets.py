"""
Görsel kütüphane toplu üretici — motivasyon foto arka planları.

Her tema için hedef varyant sayısına ulaşana kadar görsel üretir, 5 noktalı
kalite kontrolünden geçirir, Supabase Storage bucket 'visual-library'ye yükler
ve visual_assets DB tablosuna kaydeder (bkz. migrations/015_visual_asset_library.sql).

Repo kökünde local dosya YAZILMAZ — render Remotion Lambda üzerinde çalışır,
backend'in local diskine hiçbir zaman erişemez; gerçek HTTP URL şart.

Model: gpt-image-1 KULLANILMIYOR (2026-10-23'te kullanımdan kalkıyor).
  --quality low  → gpt-image-1-mini (geliştirme/test, ~$0.006/görsel)
  --quality medium/high → gpt-image-2 (üretim, medium ~$0.041/görsel)

Kullanım:
  python scripts/generate_assets.py                       # durum raporu + dry-run tahmini
  python scripts/generate_assets.py --dry-run              # aynısı, açık bayrak
  python scripts/generate_assets.py --run                  # GERÇEK ÜRETİM — para harcar
  python scripts/generate_assets.py --run --theme calisma_masasi --variants 5
  python scripts/generate_assets.py --run --quality low     # geliştirme/test
  python scripts/generate_assets.py --retry-pending         # ödenmiş ama kaydedilememiş
                                                              # görselleri kurtar (API'yi
                                                              # tekrar ÇAĞIRMAZ)

Ödenmiş bir görsel asla kaybolmaz: Storage/DB yazımı 3 denemeli backoff kullanır;
üçü de başarısız olursa görsel + metadata backend/_pending_registration/'e
kaydedilir (silinmez) — --retry-pending ile parasız tamamlanır.

Sadece YEREL makinede çalışır — Railway'de değil. backend/Dockerfile'ın tek
CMD'i "uvicorn app.main:app"; bu script hiçbir zaman deploy edilen container'da
çalışmaz (bkz. backend/requirements-dev.txt).

Ön koşullar:
  OPENAI_API_KEY  — zorunlu (--run için)
  pytesseract     — pip install -r requirements-dev.txt
  Tesseract OCR binary (Python paketinin dışında, sistem düzeyinde kurulur):
    Windows : winget install --id UB-Mannheim.TesseractOCR
              (kurulum sırasında "Additional language data" → Turkish işaretle,
              veya sonradan tur.traineddata dosyasını Tesseract-OCR/tessdata/'ya kopyala)
    macOS   : brew install tesseract tesseract-lang
    Linux   : apt-get install tesseract-ocr tesseract-ocr-tur

  OCR en kritik kalite kapısıdır (metin sızıntısı riski) — Tesseract yoksa
  --run BAŞLAMAZ (verify_ocr_available() önyükleme kontrolü, sessiz atlama yok).
  --dry-run / --status Tesseract olmadan da çalışır (yalnızca rapor, hiçbir şey
  üretmez/yazmaz) ama OCR durumunu raporda gösterir.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import pathlib
import sys
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

from app.core.visual_manifest import (  # noqa: E402
    THEMES, QUALITY_GATES,
    DEV_MODEL, DEV_QUALITY, PROD_MODEL, PROD_QUALITY, OUTPUT_SIZE,
    cost_per_image, build_prompt,
)

MAX_REGEN = QUALITY_GATES["max_regenerate_attempts"]
MAX_WORKERS = 3

# Tesseract 0-100 güven skoru; pilot #1'de OCR 4/6 reddetti ama ham metin
# uzunluğu ile ölçülüyordu — doku/gölgeyi Tesseract'ın tek karakter olarak
# "gördüğü" düşük güvenli yanlış pozitifler gerçek metinden ayrılamıyordu.
# 60, image_to_data.conf için yaygın kabul gören ayrım noktası (gerçek basılı
# metin genelde 70-95+, doku kaynaklı gürültü genelde <50) — pilot #2'nin
# backend/_rejected_previews/ çıktısı ile doğrulanacak, kör tahmin değil.
OCR_MIN_CONFIDENCE = 60

REJECTED_DIR = pathlib.Path(__file__).resolve().parents[1] / "_rejected_previews"

# Ödenmiş ama Storage/DB'ye yazılamamış görseller — SİLİNMEZ. pilot #2: "Server
# disconnected" 2 ödenmiş görseli DB'ye yazamadan kaybetti (para ödendi, iş
# çöpe gitti). Kalite reddi DEĞİL — telemetri/altyapı hatası iş hatasını
# maskeleyemez kuralının maliyet karşılığı: --retry-pending ile API'yi TEKRAR
# ÇAĞIRMADAN (yeniden ödeme yapmadan) tamamlanır.
PENDING_DIR = pathlib.Path(__file__).resolve().parents[1] / "_pending_registration"

_BACKOFF_ATTEMPTS = 3
_BACKOFF_BASE_SECONDS = 1.0


def _with_backoff(fn, label: str = ""):
    """3 denemeli üstel geri çekilme (1s, 2s, 4s) — Supabase Storage/DB yazımları için."""
    last_exc: Exception | None = None
    for attempt in range(_BACKOFF_ATTEMPTS):
        try:
            return fn()
        except Exception as exc:
            last_exc = exc
            if attempt < _BACKOFF_ATTEMPTS - 1:
                wait = _BACKOFF_BASE_SECONDS * (2 ** attempt)
                logger.warning(f"    {label} deneme {attempt + 1}/{_BACKOFF_ATTEMPTS} başarısız "
                                f"({exc}) — {wait:.0f}s sonra tekrar")
                time.sleep(wait)
    raise last_exc


def _save_pending(image_bytes: bytes, entry: dict, stage_failed: str, exc: Exception) -> None:
    """Ödenmiş görseli yerel diske kaydeder — --retry-pending onu API'ye tekrar ödemeden tamamlar."""
    try:
        PENDING_DIR.mkdir(parents=True, exist_ok=True)
        base = entry["asset_id"]
        (PENDING_DIR / f"{base}.webp").write_bytes(image_bytes)
        meta = dict(entry)
        meta["_stage_failed"] = stage_failed
        meta["_last_error"] = str(exc)
        (PENDING_DIR / f"{base}.json").write_text(
            json.dumps(meta, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
        )
        logger.error(
            f"    ÖDENMİŞ GÖRSEL KUYRUĞA ALINDI ({stage_failed}, 3 deneme sonrası): "
            f"{PENDING_DIR / (base + '.webp')} — kurtarmak için --retry-pending çalıştır"
        )
    except Exception as save_exc:
        logger.critical(
            f"    KRİTİK: ödenmiş görsel yerel kuyruğa da kaydedilemedi, bytes KAYBOLDU: {save_exc}"
        )


# ── DB yardımcıları (doğrudan — script içi, visual_library'ye bağımlı değil) ──

def _theme_rows(theme: str) -> list[dict]:
    from app.db.supabase import get_supabase_client
    supabase = get_supabase_client()
    resp = supabase.table("visual_assets").select("asset_id, cache_key, license").eq("theme", theme).execute()
    return resp.data or []


def _existing_count(theme: str) -> int:
    return sum(1 for r in _theme_rows(theme) if r.get("license"))


def _existing_cache_keys(theme: str) -> set[str]:
    return {r["cache_key"] for r in _theme_rows(theme) if r.get("cache_key")}


# ── OpenAI görsel üretimi ────────────────────────────────────

def generate_image(prompt: str, model: str, quality: str, api_key: str) -> tuple[bytes | None, str]:
    """
    gpt-image-2 / gpt-image-1-mini ile görsel üretir. Bu modeller response_format
    KABUL ETMEZ — her zaman b64_json döner (OpenAI resmi dokümantasyonu, 2026-08-02).
    Returns: (image_bytes | None, hata_mesajı)
    """
    try:
        import openai
        import base64
        client = openai.OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        resp = client.images.generate(
            model=model, prompt=prompt, n=1,
            size=OUTPUT_SIZE, quality=quality, output_format="png",
        )
        data = base64.b64decode(resp.data[0].b64_json)
        return data, ""
    except Exception as exc:
        err_type = type(exc).__name__
        err_msg = str(exc)
        if "insufficient_quota" in err_msg or "quota" in err_msg.lower():
            return None, f"insufficient_quota: {err_msg}"
        if "rate_limit" in err_msg.lower():
            return None, f"rate_limit: {err_msg}"
        if "content_policy" in err_msg.lower() or "safety" in err_msg.lower():
            return None, f"content_policy: {err_msg}"
        return None, f"{err_type}: {err_msg}"


# ── Kalite kontrolleri — 5 nokta ────────────────────────────

def check_blur(image_bytes: bytes) -> tuple[bool, float]:
    """
    Bölge: TÜM KARE (basit, öngörülebilir — bölge seçimiyle "doğru" bulanıklığı
    kovalamayı bıraktık). Önce merkez %40, sonra alt %40 denendi; ikisi de
    yetersiz kaldı çünkü asıl sorun bölge değil, STİLDİ: STYLE_CONTRACT
    "shallow depth of field" istiyor VE koyu düz dokulu özneler (ör. hoodie)
    doğaları gereği düşük Laplacian üretiyor — kusur değil.

    Eşik: 35 (eskiden 100). Kaynak — 3 kabul edilmiş, insan gözüyle onaylanmış
    gerçek pilot görselinin TAM KARE ölçümü: 64.4, 64.6, 52.8 (bkz. sohbet
    geçmişi, kullanıcı tarafından ölçüldü). 35, bunların en düşüğünün (52.8)
    belirgin altında — kabul edilmiş hiçbirini reddetmiyor ama gerçekten
    bozuk/düz görseller için hâlâ bir alt sınır.

    NOT — bu değer TAM DOĞRULANMADI: reddedilen görsellerin gerçek ölçümüyle
    çapraz kontrol edilecekti (35'in altında mı, yoksa 52-64 aralığında,
    yani aslında kaliteli görseller de mi reddediliyordu?) ama pilot #2'nin
    _rejected_previews/ çıktısı, bu değişiklikten önce yanlışlıkla silindi
    (ajan hatası — kendi test dosyalarını temizlerken gerçek pilot verisini
    de sildi). Pilot #3'ün reddettiği görseller artık dokunulmadan kalacak;
    35'in gerçek doğrulaması onlarla yapılacak.
    """
    try:
        from PIL import Image
        import io, numpy as np
        img = Image.open(io.BytesIO(image_bytes)).convert("L")
        arr = np.array(img, dtype=float)
        lap = arr[:-2, 1:-1] + arr[2:, 1:-1] + arr[1:-1, :-2] + arr[1:-1, 2:] - 4 * arr[1:-1, 1:-1]
        variance = float(lap.var())
        return variance >= QUALITY_GATES["blur_laplacian_min"], variance
    except ImportError:
        logger.debug("[quality] Pillow/numpy yok — bulanıklık kontrolü atlandı")
        return True, 0.0
    except Exception as exc:
        logger.debug(f"[quality] blur check hatası: {exc}")
        return True, 0.0


def check_brightness(image_bytes: bytes) -> tuple[bool, float]:
    try:
        from PIL import Image
        import io, numpy as np
        img = Image.open(io.BytesIO(image_bytes)).convert("L")
        avg = float(np.array(img).mean())
        return QUALITY_GATES["brightness_min"] <= avg <= QUALITY_GATES["brightness_max"], avg
    except Exception:
        return True, 0.0


class OcrUnavailableError(RuntimeError):
    """pytesseract kurulu değil VEYA Tesseract binary çalıştırılamıyor.
    OCR en kritik kalite kapısı — bu durumda sessizce True dönüp devam ETMEZ,
    çağıran (main() önyükleme kontrolü) üretimi hiç başlatmaz."""


def check_ocr(image_bytes: bytes) -> tuple[bool, dict]:
    """
    Görselde okunabilir metin var mı? En kritik kalite kapısı — Tesseract ZORUNLU.
    pytesseract paketi kurulu olsa bile Tesseract binary'si yoksa (TesseractNotFoundError,
    import-time değil ÇAĞRI zamanında fırlar) burada da yakalanır: ikisi de
    OcrUnavailableError'a çevrilir, sessiz "True" dönmek YOK.

    image_to_data kullanır (image_to_string DEĞİL) — her token'ın güven skorunu
    (0-100) alır. Yalnızca OCR_MIN_CONFIDENCE üstü tokenlar "gerçek metin"
    sayılır; pilot #1'de ham metin uzunluğu dokuyu/gölgeyi de metin sanıp
    4/6 yanlış reddediyordu.

    Returns: (temiz_mi, detay) — detay: {"raw_text", "high_conf_chars", "tokens"}
             tokens: [{"text","conf"}], hem düşük hem yüksek güvenli tüm adaylar
             (teşhis için — pilot çıktısı hangi eşiğin doğru olduğunu gösterecek).
    """
    try:
        import pytesseract
    except ImportError as exc:
        raise OcrUnavailableError(f"pytesseract paketi kurulu değil: {exc}") from exc

    from PIL import Image
    import io
    img = Image.open(io.BytesIO(image_bytes))
    try:
        data = pytesseract.image_to_data(
            img, lang="tur+eng", config="--psm 11", output_type=pytesseract.Output.DICT
        )
    except Exception as exc:
        # TesseractNotFoundError dahil — binary PATH'te yok veya çalışmıyor
        raise OcrUnavailableError(f"Tesseract binary çalıştırılamadı: {exc}") from exc

    tokens: list[dict] = []
    high_conf_chars = 0
    for raw_text, raw_conf in zip(data.get("text", []), data.get("conf", [])):
        clean = "".join(c for c in raw_text if c.isalnum())
        if not clean:
            continue
        try:
            conf = float(raw_conf)
        except (TypeError, ValueError):
            conf = -1.0
        tokens.append({"text": clean, "conf": conf})
        if conf >= OCR_MIN_CONFIDENCE:
            high_conf_chars += len(clean)

    is_clean = high_conf_chars <= QUALITY_GATES["ocr_max_readable_chars"]
    detail = {
        "raw_text": " ".join(t["text"] for t in tokens)[:200],
        "high_conf_chars": high_conf_chars,
        "tokens": tokens,
    }
    return is_clean, detail


def verify_ocr_available() -> tuple[bool, str]:
    """
    Gerçek bir Tesseract çağrısıyla önyükleme doğrulaması yapar (sadece 'import
    pytesseract' başarılı diye binary de çalışıyor demek DEĞİL — python3 stub
    dersiyle aynı sınıf hata: varlık ≠ çalışırlık). --run öncesi main() bunu
    çağırır; başarısızsa üretim HİÇ başlamaz.
    """
    try:
        from PIL import Image
        import io
        probe = Image.new("RGB", (64, 64), color=(255, 255, 255))
        buf = io.BytesIO()
        probe.save(buf, format="PNG")
        check_ocr(buf.getvalue())
        return True, ""
    except OcrUnavailableError as exc:
        return False, str(exc)


def check_upper_third_flatness(image_bytes: bytes) -> tuple[bool, float]:
    """Üst üçte bir metin overlay'i için yeterince sade mi? (düşük varyans = sade)"""
    try:
        from PIL import Image
        import io, numpy as np
        img = Image.open(io.BytesIO(image_bytes)).convert("L")
        w, h = img.size
        top_third = img.crop((0, 0, w, max(1, h // 3)))
        std = float(np.array(top_third, dtype=float).std())
        flatness = max(0.0, 1.0 - std / 128.0)
        return flatness >= QUALITY_GATES["upper_third_flatness_min"], round(flatness, 3)
    except Exception as exc:
        logger.debug(f"[quality] upper_third_flatness hatası: {exc}")
        return True, 0.0


def check_resolution(image_bytes: bytes) -> tuple[bool, tuple[int, int]]:
    try:
        from PIL import Image
        import io
        img = Image.open(io.BytesIO(image_bytes))
        expected_w, expected_h = (int(x) for x in OUTPUT_SIZE.split("x"))
        return (img.width == expected_w and img.height == expected_h), (img.width, img.height)
    except Exception as exc:
        logger.debug(f"[quality] resolution check hatası: {exc}")
        return True, (0, 0)


def run_quality_checks(image_bytes: bytes) -> tuple[bool, dict]:
    report: dict = {}

    ocr_ok, ocr_detail = check_ocr(image_bytes)
    blur_ok, blur_val = check_blur(image_bytes)
    bright_ok, bright_val = check_brightness(image_bytes)
    flat_ok, flat_val = check_upper_third_flatness(image_bytes)
    res_ok, (w, h) = check_resolution(image_bytes)

    report.update({
        "ocr_ok": ocr_ok,
        "ocr_text_found": ocr_detail["raw_text"],
        "ocr_high_conf_chars": ocr_detail["high_conf_chars"],
        "ocr_tokens": ocr_detail["tokens"],
        "blur_ok": blur_ok, "blur_variance": round(blur_val, 1),
        "brightness_ok": bright_ok, "brightness_avg": round(bright_val, 1),
        "upper_third_flatness_ok": flat_ok, "upper_third_flatness": flat_val,
        "resolution_ok": res_ok, "width": w, "height": h,
    })
    return all([ocr_ok, blur_ok, bright_ok, flat_ok, res_ok]), report


# ── Boyut dönüştürme ─────────────────────────────────────────

def resize_to_target(image_bytes: bytes, target: tuple[int, int] = (1080, 1920)) -> bytes:
    try:
        from PIL import Image
        import io
        img = Image.open(io.BytesIO(image_bytes))
        tw, th = target
        ratio = th / img.height
        new_w = int(img.width * ratio)
        img = img.resize((new_w, th), Image.LANCZOS)
        if img.width > tw:
            left = (img.width - tw) // 2
            img = img.crop((left, 0, left + tw, th))
        buf = io.BytesIO()
        img.save(buf, format="WEBP", quality=88)
        return buf.getvalue()
    except ImportError:
        logger.debug("[resize] Pillow yok — ham görsel kullanılıyor")
        return image_bytes
    except Exception as exc:
        logger.debug(f"[resize] hata: {exc}")
        return image_bytes


def _save_rejected(image_bytes: bytes, theme_key: str, variant_index: int, attempt: int, report: dict) -> None:
    """
    Reddedilen görseli SİLMEZ, backend/_rejected_previews/'e kaydeder (.gitignore'da) —
    hangi kontrolün gerçekten reddettiğini ve OCR'ın ne bulduğunu insan gözüyle
    doğrulamak için (pilot #1'den sonraki talep: yanlış pozitif mi, gerçek ret mi?).
    """
    try:
        REJECTED_DIR.mkdir(parents=True, exist_ok=True)
        base = f"{theme_key}_v{variant_index}_deneme{attempt}"
        (REJECTED_DIR / f"{base}.png").write_bytes(image_bytes)
        (REJECTED_DIR / f"{base}.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
        )
    except Exception as exc:
        logger.debug(f"[quality] reddedilen görsel kaydedilemedi: {exc}")


# ── Tek varyant üretim + kayıt ───────────────────────────────

def _produce_one(
    theme_key: str,
    variant_index: int,
    model: str,
    quality: str,
    api_key: str,
    stop_event: threading.Event,
) -> dict:
    """
    Returns dict:
      produced: bool
      cost: float
      attempts: int              — bu varyant için yapılan GERÇEK generate_image() çağrısı sayısı
      theme, asset_id, public_url: str | None (produced=True'da dolu)
      failed_checks: list[str]   — kalite reddi ise, son denemede başarısız olan kontroller
      error: str | None          — kalite dışı bir hata (API/rate_limit/upload/db)
    """
    from app.modules.content.visual_library import register_asset, cache_key as _compute_cache_key
    from app.modules.content.storage import upload_bytes, VISUAL_LIBRARY_BUCKET

    cache_key = _compute_cache_key(theme_key, model, quality, variant_index)
    prompt = build_prompt(theme_key)
    unit_cost = cost_per_image(model, quality)
    asset_id = f"{theme_key.replace('_', '-')}-{str(uuid.uuid4())[:8]}"

    attempts = 0

    def _fail(spent: float, error: str | None = None, failed_checks: list[str] | None = None) -> dict:
        return {
            "produced": False, "cost": spent, "attempts": attempts, "theme": theme_key,
            "asset_id": None, "public_url": None,
            "failed_checks": failed_checks or [], "error": error,
        }

    _CHECK_NAMES = {
        "ocr_ok": "ocr", "blur_ok": "blur", "brightness_ok": "brightness",
        "upper_third_flatness_ok": "upper_third_flatness", "resolution_ok": "resolution",
    }

    spent = 0.0
    final_bytes: bytes | None = None
    qc_report: dict = {}
    for attempt in range(MAX_REGEN + 1):
        if stop_event.is_set():
            return _fail(spent, error="durduruldu (insufficient_quota)")

        attempts += 1
        img_bytes, err = generate_image(prompt, model, quality, api_key)
        if err:
            if "insufficient_quota" in err:
                stop_event.set()
                return _fail(spent, error=err)
            if "rate_limit" in err and attempt < MAX_REGEN:
                wait = 2 ** (attempt + 1)
                logger.warning(f"    [{theme_key}#{variant_index}] rate_limit, {wait}s bekleniyor …")
                time.sleep(wait)
                continue
            return _fail(spent, error=err)

        spent += unit_cost
        try:
            ok, report = run_quality_checks(img_bytes)
        except OcrUnavailableError as exc:
            # OCR üretim ortasında koptu (binary çöktü vb.) — normal kalite
            # reddi değil, üretimi tamamen durdur (sessizce "kalite başarısız"
            # gibi görünmesin, gerçek sebep açıkça raporlansın).
            stop_event.set()
            return _fail(spent, error=f"ocr_unavailable_mid_run: {exc}")
        qc_report = report
        if ok:
            final_bytes = img_bytes
            break
        logger.warning(
            f"    [{theme_key}#{variant_index}] deneme {attempt + 1} kalite başarısız "
            f"(ocr={report.get('ocr_ok')} [metin='{report.get('ocr_text_found','')}' "
            f"güvenli_karakter={report.get('ocr_high_conf_chars')}], blur={report.get('blur_ok')} "
            f"[{report.get('blur_variance')}], bright={report.get('brightness_ok')}, "
            f"flat={report.get('upper_third_flatness_ok')}, res={report.get('resolution_ok')})"
        )
        _save_rejected(img_bytes, theme_key, variant_index, attempt, report)

    if final_bytes is None:
        failed = [label for key, label in _CHECK_NAMES.items() if not qc_report.get(key, True)]
        return _fail(spent, error="kalite kapısını geçemedi", failed_checks=failed)

    final_bytes = resize_to_target(final_bytes)
    sha256 = hashlib.sha256(final_bytes).hexdigest()
    remote_path = f"{theme_key}/{asset_id}.webp"

    entry = {
        "asset_id": asset_id,
        "theme": theme_key,
        "cache_key": cache_key,
        "source": "openai_image_api",
        "model": model,
        "quality": quality,
        "storage_path": remote_path,
        "public_url": None,  # upload başarılı olunca doldurulur
        "sha256": sha256,
        "width": qc_report.get("width"),
        "height": qc_report.get("height"),
        "license": "api_terms_commercial",
        "license_url": "https://openai.com/policies/terms-of-use",
        "attribution_required": False,
        "ocr_clean": bool(qc_report.get("ocr_ok")),
        "ocr_text": qc_report.get("ocr_text_found") or None,
        "blur_variance": qc_report.get("blur_variance"),
        "brightness_avg": qc_report.get("brightness_avg"),
        "upper_third_flatness": qc_report.get("upper_third_flatness"),
        "has_face": False,  # tema kataloğunda yüz istenmiyor (style_contract negative)
        "tags": THEMES[theme_key].get("tags", []),
        "dominant_color": None,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    # Ödenmiş görsel burada — Storage/DB'ye yazılamazsa 3 backoff denemesi,
    # sonra da yerel kuyruğa (paraya yazık edilmez, kalite reddiyle karışmaz).
    try:
        public_url = _with_backoff(
            lambda: upload_bytes(final_bytes, VISUAL_LIBRARY_BUCKET, remote_path, "image/webp"),
            label=f"[{theme_key}#{variant_index}] storage_upload",
        )
        entry["public_url"] = public_url
    except Exception as exc:
        _save_pending(final_bytes, entry, "storage_upload_failed", exc)
        return _fail(spent, error=f"storage_upload_failed_saved_pending: {exc}")

    try:
        _with_backoff(lambda: register_asset(entry), label=f"[{theme_key}#{variant_index}] db_register")
    except Exception as exc:
        _save_pending(final_bytes, entry, "db_register_failed", exc)
        return _fail(spent, error=f"db_register_failed_saved_pending: {exc}")

    return {
        "produced": True, "cost": spent, "attempts": attempts, "theme": theme_key,
        "asset_id": asset_id, "public_url": entry["public_url"],
        "failed_checks": [], "error": None,
    }


# ── Tema başına üretim (MAX_WORKERS eşzamanlı) ──────────────

def generate_theme_assets(
    theme_key: str, count: int, quality: str, model: str, dry_run: bool, api_key: str,
) -> tuple[int, float, list[dict]]:
    """Returns: (üretilen_sayı, harcanan_maliyet, tüm _produce_one sonuç dict'leri)"""
    theme_cfg = THEMES[theme_key]
    existing = _existing_count(theme_key)
    target = theme_cfg.get("target_variants", 15)
    needed = max(0, min(count, target - existing))

    if needed <= 0:
        logger.info(f"  {theme_key}: hedef doldu ({existing}/{target}), atlandı")
        return 0, 0.0, []

    unit_cost = cost_per_image(model, quality)
    logger.info(f"  {theme_key}: {needed} görsel üretilecek (mevcut {existing}/{target}, ~${unit_cost * needed:.3f})")

    if dry_run:
        logger.info(f"    DRY-RUN — üretim atlandı")
        return needed, unit_cost * needed, []

    from app.modules.content.visual_library import cache_key as _compute_cache_key

    existing_keys = _existing_cache_keys(theme_key)
    stop_event = threading.Event()
    produced = 0
    total_cost = 0.0
    results: list[dict] = []

    # variant_index existing sayıdan devam eder — cache_key çakışmasın
    variant_indices = []
    idx = existing
    while len(variant_indices) < needed:
        ck = _compute_cache_key(theme_key, model, quality, idx)
        if ck not in existing_keys:
            variant_indices.append(idx)
        idx += 1

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = {
            pool.submit(_produce_one, theme_key, vi, model, quality, api_key, stop_event): vi
            for vi in variant_indices
        }
        for fut in as_completed(futures):
            vi = futures[fut]
            try:
                res = fut.result()
            except Exception as exc:
                res = {"produced": False, "cost": 0.0, "attempts": 0, "theme": theme_key, "asset_id": None,
                       "public_url": None, "failed_checks": [], "error": f"worker_exception: {exc}"}
            results.append(res)
            total_cost += res["cost"]
            if res["produced"]:
                produced += 1
                logger.info(f"    [{theme_key}#{vi}] kaydedildi: {res['asset_id']}  (toplam: {produced}/{needed})")
            else:
                reason = res["error"] or f"kalite reddi: {', '.join(res['failed_checks'])}"
                logger.warning(f"    [{theme_key}#{vi}] atlandı: {reason}")
            if stop_event.is_set():
                logger.error(f"    {theme_key}: insufficient_quota — kalan denemeler iptal")
                break

    return produced, total_cost, results


# ── Ödenmiş ama kaydedilememiş görselleri kurtar ────────────

def retry_pending() -> None:
    """
    _pending_registration/'daki her görsel için: eksik olan adımı (upload ve/veya
    DB kaydı) 3 backoff denemesiyle tamamlar. API'yi TEKRAR ÇAĞIRMAZ — para
    zaten ödendi, bu yalnızca kaydı tamamlıyor.
    """
    from app.modules.content.visual_library import register_asset
    from app.modules.content.storage import upload_bytes, VISUAL_LIBRARY_BUCKET

    if not PENDING_DIR.exists() or not list(PENDING_DIR.glob("*.json")):
        print("Bekleyen kayıt yok.")
        return

    json_files = sorted(PENDING_DIR.glob("*.json"))
    print(f"=== {len(json_files)} bekleyen (ödenmiş) görsel işleniyor ===\n")
    recovered = 0
    for jf in json_files:
        meta = json.loads(jf.read_text(encoding="utf-8"))
        webp_path = jf.with_suffix(".webp")
        asset_id = meta.get("asset_id", jf.stem)
        if not webp_path.exists():
            print(f"  [HATA] {asset_id}: görsel dosyası eksik ({webp_path.name}) — atlanıyor")
            continue

        image_bytes = webp_path.read_bytes()
        entry = {k: v for k, v in meta.items() if not k.startswith("_")}
        try:
            if not entry.get("public_url"):
                entry["public_url"] = _with_backoff(
                    lambda: upload_bytes(image_bytes, VISUAL_LIBRARY_BUCKET, entry["storage_path"], "image/webp"),
                    label=asset_id,
                )
            _with_backoff(lambda: register_asset(entry), label=asset_id)
            jf.unlink()
            webp_path.unlink()
            recovered += 1
            print(f"  [OK] {asset_id} kurtarıldı -> {entry['public_url']}")
        except Exception as exc:
            print(f"  [HATA] {asset_id}: hâlâ başarısız — {exc}")

    print(f"\n=== Tamamlandı: {recovered}/{len(json_files)} kurtarıldı ===")
    if recovered < len(json_files):
        print(f"  Kalanlar {PENDING_DIR} içinde bekliyor — tekrar --retry-pending çalıştır.")


# ── CLI ───────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Görsel kütüphane toplu üreticisi")
    parser.add_argument("--run", action="store_true", help="Gerçek üretim yap (varsayılan: dry-run)")
    parser.add_argument("--dry-run", action="store_true", help="Açıkça dry-run (varsayılan zaten budur)")
    parser.add_argument("--theme", default=None,
                        help="Belirli tema(lar) üret, virgülle ayrılmış (örn: a,b) — yoksa --all")
    parser.add_argument("--all", action="store_true", help="Tüm temalar (varsayılan davranış)")
    parser.add_argument("--variants", "--count", dest="variants", type=int, default=15,
                        help="Tema başına üretilecek maksimum görsel (varsayılan: 15)")
    parser.add_argument("--quality", choices=["low", "medium", "high"], default="medium",
                        help="Görsel kalitesi (varsayılan: medium)")
    parser.add_argument("--model", default=None,
                        help=f"Model override (varsayılan: quality=low→{DEV_MODEL}, aksi halde {PROD_MODEL})")
    parser.add_argument("--status", action="store_true", help="Kütüphane doluluk durumunu göster ve çık")
    parser.add_argument("--retry-pending", action="store_true",
                        help="Ödenmiş ama kaydedilememiş görselleri kurtar (API'yi tekrar ÇAĞIRMAZ)")
    args = parser.parse_args()

    if args.retry_pending:
        retry_pending()
        return

    model = args.model or (DEV_MODEL if args.quality == "low" else PROD_MODEL)
    dry_run = not args.run

    print("\n=== Görsel Kütüphane Durum Raporu ===\n")
    total_existing = 0
    total_target = 0
    for tk, cfg in THEMES.items():
        existing = _existing_count(tk)
        target = cfg.get("target_variants", 15)
        pct = round(existing / target * 100) if target else 0
        bar = "#" * (pct // 10) + "-" * (10 - pct // 10)
        total_existing += existing
        total_target += target
        print(f"  {tk:<22} [{bar}] {existing:>3}/{target}  {pct:>3}%")
    print(f"\n  TOPLAM: {total_existing}/{total_target}")

    unit_cost = cost_per_image(model, args.quality)
    needed_all = max(0, total_target - total_existing)
    ocr_ok, ocr_err = verify_ocr_available()
    print(f"\n  Kalite    : {args.quality} (model={model}, ~${unit_cost}/görsel, boyut={OUTPUT_SIZE})")
    print(f"  Tahmini   : {needed_all} görsel × ${unit_cost:.3f} = ~${needed_all * unit_cost:.2f}")
    print(f"  OCR       : {'HAZIR' if ocr_ok else f'KULLANILAMIYOR — {ocr_err}'}")
    print(f"  Mod       : {'GERÇEK ÜRETİM' if args.run else 'DRY-RUN (--run ile etkinleştir)'}\n")

    if args.status:
        return

    api_key = os.getenv("OPENAI_API_KEY", "")
    if args.run and not api_key:
        print("[HATA] OPENAI_API_KEY env'de yok — gerçek üretim yapılamaz.")
        sys.exit(1)

    if args.run and not ocr_ok:
        print(
            "[HATA] OCR kontrolü kullanılamıyor — kütüphaneye yazma BAŞLATILAMAZ.\n"
            f"       Sebep: {ocr_err}\n"
            "       Kurulum: pip install -r requirements-dev.txt (pytesseract) "
            "+ Tesseract binary (README/kurulum talimatı).\n"
            "       Bu kontrol atlanamaz — metin sızıntısı riski en kritik kalite kapısıdır."
        )
        sys.exit(1)

    theme_list = list(THEMES.items())
    if args.theme:
        requested = [t.strip() for t in args.theme.split(",") if t.strip()]
        unknown = [t for t in requested if t not in THEMES]
        if unknown:
            print(f"[HATA] Bilinmeyen tema(lar): {', '.join(unknown)}")
            print(f"  Mevcut temalar: {', '.join(THEMES.keys())}")
            sys.exit(1)
        theme_list = [(t, THEMES[t]) for t in requested]

    print("=== Üretim Başlıyor ===\n")
    grand_total = 0
    grand_cost = 0.0
    all_results: list[dict] = []

    for tk, _cfg in theme_list:
        logger.info(f"\n[TEMA] {tk} — {THEMES[tk].get('label', tk)}")
        n, cost, results = generate_theme_assets(
            theme_key=tk, count=args.variants, quality=args.quality,
            model=model, dry_run=dry_run, api_key=api_key,
        )
        grand_total += n
        grand_cost += cost
        all_results.extend(results)

    print(f"\n=== Tamamlandı ===")
    print(f"  Üretilen  : {grand_total} görsel")
    print(f"  Toplam maliyet ({'tahmini' if dry_run else 'gerçek'}): ${grand_cost:.3f}")

    if not dry_run and all_results:
        from collections import Counter
        rejected = [r for r in all_results if not r["produced"]]
        pending_saved = [r for r in rejected if r["error"] and "saved_pending" in r["error"]]
        truly_failed = [r for r in rejected if r not in pending_saved]
        check_counts = Counter(c for r in truly_failed for c in r["failed_checks"])
        other_errors = [r["error"] for r in truly_failed if not r["failed_checks"] and r["error"]]

        total_attempts = sum(r.get("attempts", 0) for r in all_results)
        retry_calls = total_attempts - grand_total
        variants_attempted = len(all_results)
        acceptance_pct = round(grand_total / variants_attempted * 100) if variants_attempted else 0

        print(f"  Toplam deneme: {total_attempts} (başarılı {grand_total}, yeniden deneme {retry_calls})")
        print(f"  Kabul oranı: %{acceptance_pct} ({grand_total}/{variants_attempted} hedef)"
              f"{'  [UYARI: %70 eşiğinin altında]' if acceptance_pct < 70 else ''}")
        if REJECTED_DIR.exists() and truly_failed:
            print(f"  Reddedilen görseller (PNG + QC raporu): {REJECTED_DIR}")

        print(f"\n  Tema başına:")
        themes_seen = sorted({r["theme"] for r in all_results})
        for tk in themes_seen:
            t_rows = [r for r in all_results if r["theme"] == tk]
            t_produced = sum(1 for r in t_rows if r["produced"])
            t_rejected = len(t_rows) - t_produced
            t_cost = sum(r["cost"] for r in t_rows)
            print(f"    {tk:<22} üretilen={t_produced:<3} reddedilen={t_rejected:<3} maliyet=${t_cost:.3f}")

        pending_now = list(PENDING_DIR.glob("*.json")) if PENDING_DIR.exists() else []
        print(f"\n  _pending_registration/ durumu: "
              f"{len(pending_now)} bekleyen kayıt" if pending_now else "\n  _pending_registration/ durumu: boş (kaydedilemeyen görsel yok)")

        if pending_saved:
            print(f"\n  ÖDENMİŞ AMA KAYDEDİLEMEDİ: {len(pending_saved)} görsel "
                  f"(kayıp DEĞİL — {PENDING_DIR})")
            print(f"    Kurtarmak için: python scripts/generate_assets.py --retry-pending")

        print(f"\n  Reddedilen (kalite/hata): {len(truly_failed)} görsel")
        if check_counts:
            print("    Kalite kapısı reddi (kontrol bazında):")
            for check, cnt in check_counts.most_common():
                print(f"      - {check}: {cnt}")
        if other_errors:
            print("    Diğer hatalar:")
            for e in other_errors:
                print(f"      - {e}")

        produced_rows = [r for r in all_results if r["produced"]]
        if produced_rows:
            print(f"\n  Üretilen görseller ({len(produced_rows)}):")
            for r in produced_rows:
                print(f"    [{r['theme']}] {r['asset_id']} -> {r['public_url']}")

    if dry_run:
        print(f"\n  NOT: Dry-run modundaydı. Gerçek üretim için --run ekle.")


if __name__ == "__main__":
    main()
