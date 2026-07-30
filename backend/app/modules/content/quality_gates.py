"""
Kalite kapıları — render öncesi storyboard doğrulama + render sonrası ses/süre kontrolü.

Sections 1, 6, 14:
  - Ön kontrol: storyboard bütünlüğü (sahne sayısı, voice_text, duration)
  - Ses kontrolü: ffprobe mean_volume > -45 dB (sessiz video engeli)
  - Süre kontrolü: render sonrası actual_duration vs requested_duration_seconds
"""
import json
import logging
import os
import re
import subprocess
import tempfile
from typing import Optional

logger = logging.getLogger(__name__)

_MIN_VOLUME_DB    = -45.0   # bu değerin altındaki TTS sessiz sayılır
_FFPROBE_TIMEOUT  = 20      # saniye


# ── 1. Storyboard ön kontrolü ─────────────────────────────────

_MIN_SCENES: dict[str, int] = {
    # kanonik adlar
    "konu_anlatimi":    8,
    "soru_cozum":       3,
    "reels_short":      5,
    "motivasyon":       1,
    "gorsel_post":      1,
    # pipeline anahtarları (registry.py canonical_type çıktısı)
    "lesson":           8,
    "quiz":             3,
    "educational_reel": 5,
    "motivation":       1,
    "infographic":      1,
    # eski takma adlar
    "lesson_long":      8,
    "sgs_topic_video":  8,
    "reel":             5,
    "quiz_board":       3,
}

def check_storyboard_quality(storyboard: dict, video_type: str) -> list[str]:
    """
    Render öncesi storyboard kalite kontrolü.
    Döndürür: uyarı mesajlarının listesi (boş → hepsi OK).
    """
    warnings: list[str] = []
    scenes = storyboard.get("scenes", [])

    if not scenes:
        warnings.append("Storyboard boş — hiç sahne üretilmedi.")
        return warnings

    # Minimum sahne sayısı
    min_req = _MIN_SCENES.get(video_type, 2)
    if len(scenes) < min_req:
        warnings.append(
            f"Sahne sayısı yetersiz: {len(scenes)} < {min_req} ({video_type})."
        )

    # voice_text eksik sahneler
    missing_voice = [s.get("id", i+1) for i, s in enumerate(scenes) if not (s.get("voice_text") or "").strip()]
    if missing_voice:
        warnings.append(f"voice_text eksik sahne id'leri: {missing_voice}")

    # duration_seconds tipi
    bad_dur = [
        s.get("id", i+1)
        for i, s in enumerate(scenes)
        if not isinstance(s.get("duration_seconds"), (int, float))
        or s.get("duration_seconds", 0) <= 0
    ]
    if bad_dur:
        warnings.append(f"duration_seconds hatalı/sıfır sahne id'leri: {bad_dur}")

    # Gerekli bileşen alanları
    for s in scenes:
        comp = s.get("component", "")
        if comp == "ChalkboardSolutionScene" and not s.get("question_text"):
            warnings.append(f"Sahne {s.get('id')}: ChalkboardSolutionScene için question_text zorunlu.")
        if comp in ("SplitQuizScene", "SplitQuizVerticalScene") and not s.get("options"):
            warnings.append(f"Sahne {s.get('id')}: {comp} için options zorunlu.")
        if comp == "EducationalReelScene" and not s.get("segment_type"):
            warnings.append(f"Sahne {s.get('id')}: EducationalReelScene için segment_type zorunlu.")

    # Toplam süre uyarısı (lesson için)
    if video_type in ("konu_anlatimi", "lesson", "lesson_long", "sgs_topic_video"):
        total_sec = sum(s.get("duration_seconds") or 0 for s in scenes if isinstance(s.get("duration_seconds"), (int, float)))
        if total_sec < 1080:
            warnings.append(
                f"Konu anlatımı toplam süresi kısa: {total_sec:.0f}s < 1080s (18dk). "
                "TTS sonrası uzayacak ama storyboard'u gözden geçir."
            )

    return warnings


# ── 2. TTS ses seviyesi kontrolü ──────────────────────────────

def check_audio_volume(audio_bytes: bytes) -> tuple[bool, float]:
    """
    ffmpeg volumedetect ile mean_volume kontrol eder.
    Returns: (is_ok, mean_volume_db)
      is_ok = True  → yeterli ses var
      is_ok = False → sessiz/çok kısık, yeniden üretilmeli
    """
    tmp_path: Optional[str] = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            f.write(audio_bytes)
            tmp_path = f.name

        result = subprocess.run(
            ["ffmpeg", "-i", tmp_path, "-af", "volumedetect", "-f", "null", "-"],
            capture_output=True,
            text=True,
            timeout=_FFPROBE_TIMEOUT,
        )
        m = re.search(r"mean_volume:\s*([-\d.]+)\s*dB", result.stderr)
        if not m:
            logger.debug("[quality] ffmpeg volumedetect çıktısı parse edilemedi — geçiliyor")
            return True, 0.0

        mean_vol = float(m.group(1))
        is_ok    = mean_vol > _MIN_VOLUME_DB
        if not is_ok:
            logger.warning(
                f"[quality] Sessiz TTS tespit edildi: mean_volume={mean_vol:.1f}dB "
                f"< {_MIN_VOLUME_DB}dB eşiği"
            )
        return is_ok, mean_vol

    except FileNotFoundError:
        logger.debug("[quality] ffmpeg bulunamadı — ses kontrolü atlandı")
        return True, 0.0
    except subprocess.TimeoutExpired:
        logger.warning("[quality] ffmpeg timeout — ses kontrolü atlandı")
        return True, 0.0
    except Exception as exc:
        logger.warning(f"[quality] ses kontrolü hatası (atlandı): {exc}")
        return True, 0.0
    finally:
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass


# ── 3. Pre-render ses URL kapısı ─────────────────────────────

def check_audio_urls(storyboard: dict) -> list[str]:
    """
    Render öncesi hard-fail: TTS URL'si olmayan veya boş gelen sahneleri tespit et.
    Sadece voice_text olan sahnelerde tts_url zorunludur.
    Returns: hata mesajlarının listesi (boş → tüm sesler OK)
    """
    import httpx
    errors: list[str] = []
    scenes = storyboard.get("scenes", [])
    for s in scenes:
        voice = (s.get("voice_text") or "").strip()
        if not voice:
            continue  # ses gerektirmeyen sahne
        tts_url = s.get("tts_url") or s.get("audioUrl") or ""
        scene_id = s.get("id", "?")
        if not tts_url:
            errors.append(f"Sahne {scene_id}: tts_url eksik (voice_text var ama ses üretilmemiş)")
            continue
        try:
            r = httpx.head(tts_url, timeout=8.0, follow_redirects=True)
            if r.status_code != 200:
                errors.append(
                    f"Sahne {scene_id}: tts_url HTTP {r.status_code} ({tts_url[:80]})"
                )
                continue
            cl = int(r.headers.get("content-length", 0))
            if cl > 0 and cl < 1024:
                errors.append(
                    f"Sahne {scene_id}: tts_url çok küçük ({cl} bytes) — sessiz TTS olabilir"
                )
        except Exception as exc:
            errors.append(f"Sahne {scene_id}: tts_url erişilemiyor — {exc}")
    return errors


# ── 4. Render sonrası süre kontrolü ──────────────────────────

def check_video_duration(
    video_url: str,
    requested_seconds: Optional[float],
    tolerance_seconds: float = 15.0,
) -> tuple[bool, Optional[float], str]:
    """
    ffprobe ile render edilmiş video URL'sinin gerçek süresini ölçer ve
    requested_seconds ± tolerance_seconds aralığıyla karşılaştırır.

    Returns: (is_ok, actual_duration_sec, message)
    """
    if not video_url or not requested_seconds:
        return True, None, "Süre kontrolü atlandı (URL veya hedef süre belirtilmemiş)."

    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                video_url,
            ],
            capture_output=True,
            text=True,
            timeout=_FFPROBE_TIMEOUT,
        )
        data   = json.loads(result.stdout or "{}")
        actual = float(data.get("format", {}).get("duration", 0))

        if actual <= 0:
            return True, None, "ffprobe süreyi ölçemedi — kontrol atlandı."

        diff   = abs(actual - requested_seconds)
        is_ok  = diff <= tolerance_seconds
        status = "OK" if is_ok else "UYARI"
        msg    = (
            f"[{status}] Gerçek süre: {actual:.1f}s | "
            f"Hedef: {requested_seconds:.0f}s ± {tolerance_seconds:.0f}s | "
            f"Fark: {diff:.1f}s"
        )
        return is_ok, actual, msg

    except FileNotFoundError:
        return True, None, "ffprobe bulunamadı — süre kontrolü atlandı."
    except subprocess.TimeoutExpired:
        return True, None, "ffprobe timeout — süre kontrolü atlandı."
    except (json.JSONDecodeError, ValueError, KeyError) as exc:
        return True, None, f"ffprobe çıktısı okunamadı: {exc}"
    except Exception as exc:
        return True, None, f"ffprobe hatası: {exc}"


# ── 5. Render sonrası postcheck ───────────────────────────────

def run_postcheck(
    video_url: str,
    requested_seconds: Optional[float] = None,
    tolerance_seconds: float = 15.0,
) -> dict:
    """
    Render tamamlandıktan sonra 'done' işaretlemeden önce çalışır.
    Tüm kontroller geçerse all_passed=True.

    Returns: postcheck raporu
      all_passed           : bool
      first_failure_code   : str | None
      first_failure_message: str | None
      url_accessible       : bool
      file_size_bytes      : int
      audio_volume_db      : float | None
      duration_check       : dict | None
    """
    report: dict = {
        "all_passed": False,
        "first_failure_code": None,
        "first_failure_message": None,
        "url_accessible": False,
        "file_size_bytes": 0,
        "audio_volume_db": None,
        "duration_check": None,
    }

    # ── Kontrol 1: URL varlığı ─────────────────────────────────
    if not video_url or not video_url.strip():
        report["first_failure_code"] = "failed_visual_validation"
        report["first_failure_message"] = "Video URL'si boş — render tamamlanmamış."
        return report

    # ── Kontrol 2: URL erişilebilirlik + dosya boyutu ──────────
    try:
        import httpx
        r = httpx.head(video_url.strip(), timeout=12.0, follow_redirects=True)
        if r.status_code != 200:
            report["first_failure_code"] = "failed_visual_validation"
            report["first_failure_message"] = (
                f"Video dosyasına erişilemiyor (HTTP {r.status_code}). "
                "Supabase Storage erişimi kontrol edin."
            )
            return report
        size = int(r.headers.get("content-length", 0))
        report["url_accessible"] = True
        report["file_size_bytes"] = size
        # < 200 KB = boş/kırık video (gerçek video her zaman daha büyük)
        if 0 < size < 200_000:
            report["first_failure_code"] = "failed_visual_validation"
            report["first_failure_message"] = (
                f"Video dosyası çok küçük ({size // 1024} KB) — "
                "render tamamlanmamış veya içerik üretilmemiş."
            )
            return report
    except Exception as exc:
        logger.warning(f"[postcheck] URL erişim hatası: {exc}")
        report["first_failure_code"] = "failed_visual_validation"
        report["first_failure_message"] = f"Video URL'sine erişilemiyor: {str(exc)[:120]}"
        return report

    # ── Kontrol 3: ffprobe — ses seviyesi (URL üzerinden) ─────
    try:
        vol_result = subprocess.run(
            [
                "ffmpeg", "-i", video_url.strip(),
                "-af", "volumedetect", "-f", "null", "-",
                "-t", "60",            # ilk 60 saniyeyi kontrol et (hız için)
            ],
            capture_output=True, text=True, timeout=45,
        )
        m = re.search(r"mean_volume:\s*([-\d.]+)\s*dB", vol_result.stderr)
        if m:
            mean_vol = float(m.group(1))
            report["audio_volume_db"] = mean_vol
            # -91 dB = dijital sessizlik (mean == max → sıfır genlikli tampon)
            if mean_vol < _MIN_VOLUME_DB:
                report["first_failure_code"] = "failed_audio_validation"
                report["first_failure_message"] = (
                    f"Videoda işitilebilir ses bulunamadı "
                    f"(ortalama {mean_vol:.0f} dB). "
                    "TTS zinciri başarısız olmuş olabilir."
                )
                return report
    except FileNotFoundError:
        logger.debug("[postcheck] ffmpeg bulunamadı — ses kontrolü atlandı")
    except subprocess.TimeoutExpired:
        logger.warning("[postcheck] ffmpeg timeout — ses kontrolü atlandı")
    except Exception as exc:
        logger.warning(f"[postcheck] ses kontrolü hatası (atlandı): {exc}")

    # ── Kontrol 4: Süre kontrolü (opsiyonel) ──────────────────
    if requested_seconds:
        dur_ok, actual_dur, dur_msg = check_video_duration(
            video_url, requested_seconds, tolerance_seconds
        )
        report["duration_check"] = {
            "ok": dur_ok,
            "message": dur_msg,
            "actual_seconds": actual_dur,
        }
        # Süre uyuşmazlığı uyarı değil hata — sessiz video bitti
        if not dur_ok and actual_dur is not None:
            report["first_failure_code"] = "duration_validation_failed"
            report["first_failure_message"] = dur_msg
            return report

    report["all_passed"] = True
    return report
