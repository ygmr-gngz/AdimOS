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
    "konu_anlatimi": 8,
    "lesson_long":   8,
    "sgs_topic_video": 8,
    "reel":          5,
    "educational_reel": 5,
    "quiz":          3,
    "motivation":    1,
    "infographic":   1,
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
    if video_type in ("konu_anlatimi", "lesson_long", "sgs_topic_video"):
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


# ── 3. Render sonrası süre kontrolü ──────────────────────────

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
