"""Video Prodüksiyon Motoru — Quiz / Ders / Shorts / Motivasyon / EducationalReel120."""
import logging
import time
import uuid
from typing import Optional, List, Literal
from fastapi import APIRouter, BackgroundTasks, HTTPException
import math
import traceback as _traceback
from pydantic import BaseModel, field_validator
from openai import RateLimitError as OpenAIRateLimitError, APITimeoutError
from app.db.supabase import get_supabase_client
from app.core.config import settings
from app.core.content_constants import TR_SPS
from app.modules.content.pronunciation_dict import apply_pronunciation_dict
from app.modules.content.quality_gates import (
    check_storyboard_quality,
    check_audio_volume,
    check_audio_urls,
    check_marketing_compliance,
    run_postcheck,
    normalize_loudness,
)
from app.modules.content.content_dedup import check_content_duplicate, save_content_fingerprint

logger = logging.getLogger(__name__)
router = APIRouter()
public_router = APIRouter()  # auth gerektirmeyen internal callback'ler

VIDEO_BUCKET = "video-tts"
_TTS_BACKOFF = (2, 8, 20)       # saniye — 3 deneme
_MAX_CONCURRENT = 2             # eşzamanlı pipeline sınırı
_WATCHDOG_MINUTES = 45

import threading
_pipeline_semaphore = threading.Semaphore(_MAX_CONCURRENT)

# ── Remotion devre kesici ─────────────────────────────────────
_remotion_lock = threading.Lock()
_remotion_consecutive_failures = 0
_CIRCUIT_OPEN_THRESHOLD = 5


# ── Pydantic modeller ─────────────────────────────────────────

class QuizOption(BaseModel):
    label: str
    text: str

class QuizQuestion(BaseModel):
    text: str
    options: List[QuizOption]
    correct_label: str
    explanation: Optional[str] = None

class CreateVideoPayload(BaseModel):
    type: str                              # quiz | lesson | shorts | motivation | infographic | reel
    title: str
    lesson_name: Optional[str] = None
    topic: Optional[str] = None
    description: Optional[str] = None     # yönetmen notu / ek bağlam
    format: str = "16:9"
    target_duration_minutes: Optional[int] = 12
    questions: Optional[List[QuizQuestion]] = None
    pre_storyboard: Optional[dict] = None         # infografik önceden üretilmiş storyboard
    infographic_template: Optional[str] = None    # card_grid | comparison | process
    # Süre kalite kapısı (Section 1)
    requested_duration_seconds: Optional[int] = None
    duration_tolerance_seconds: int = 15
    # İçerik tekrar engeli (Section 2)
    content_series: Optional[str] = None   # cikmis_soru | iki_dakikada_sgs | sik_hata | ...
    storyboard_version: Optional[int] = None  # yeniden oluşturma sayacı
    # Hedef kitle hattı (Bölüm 0.1) — 'ogrenci' | 'danisan'.
    # M8: ZORUNLU alan, varsayılan YOK. Danışan hattı (check_marketing_compliance)
    # TÜRMOB uyum kapısını bu alandan tetikler — sessiz "ogrenci" varsayımı bu
    # kapıyı görünmeden atlatabiliyordu. Eksik/geçersiz değer → 422 (Pydantic).
    content_track: Literal["ogrenci", "danisan"]

    @field_validator("requested_duration_seconds", "duration_tolerance_seconds", mode="before")
    @classmethod
    def _coerce_duration_int(cls, v):
        if v is None:
            return v
        if isinstance(v, bool):
            raise ValueError("süre bool olamaz")
        if isinstance(v, int):
            return v
        if isinstance(v, float):
            if v != math.floor(v):
                raise ValueError(f"süre tam sayı olmalı, gelen: {v!r}")
            return int(v)
        if isinstance(v, str):
            v = v.strip().replace(",", ".")
            if not v:
                return None
            try:
                f = float(v)
            except ValueError:
                raise ValueError(f"süre sayısal olmalı, gelen: {v!r}")
            if f != math.floor(f):
                raise ValueError(f"süre tam sayı olmalı, gelen: {v!r}")
            return int(f)
        raise ValueError(f"süre için geçersiz tip: {type(v).__name__}")

class RejectBody(BaseModel):
    reason: Optional[str] = None

class RenderCallback(BaseModel):
    job_id: str
    status: str                            # done | failed
    video_url: Optional[str] = None
    error: Optional[str] = None
    cost_lambda_usd: Optional[float] = None   # bridge'den gelen render maliyeti
    render_id: Optional[str] = None
    elapsed_seconds: Optional[int] = None


# ── Veritabanı yardımcıları ───────────────────────────────────

def _get_job(job_id: str) -> dict:
    sb = get_supabase_client()
    r = sb.table("video_jobs").select("*").eq("id", job_id).execute()
    if not r.data:
        raise HTTPException(404, "Video görevi bulunamadı")
    return r.data[0]

def _set_status(job_id: str, status: str, extra: dict | None = None):
    sb = get_supabase_client()
    payload = {"status": status, "updated_at": "now()"}
    if extra:
        payload.update(extra)
    sb.table("video_jobs").update(payload).eq("id", job_id).execute()

def _get_brand() -> dict:
    try:
        sb = get_supabase_client()
        r = sb.table("brand_settings").select("*").eq("id", "default").execute()
        s = r.data[0] if r.data else {}
        return {
            "primary_color":    s.get("primary_color", "#0B2A4A"),
            "secondary_color":  s.get("secondary_color", "#C9A96E"),
            "background_color": s.get("background_color", "#FAF7F0"),
            "font_heading":     s.get("font_heading", "Playfair Display"),
            "font_body":        s.get("font_body", "Lato"),
            "logo_url":         s.get("logo_url"),
            "handle":           s.get("handle", "@adimmusavir"),
        }
    except Exception:
        return {
            "primary_color": "#0B2A4A", "secondary_color": "#C9A96E",
            "background_color": "#FAF7F0", "font_heading": "Playfair Display",
            "font_body": "Lato", "handle": "@adimmusavir",
        }


# ── Remotion warm-up ─────────────────────────────────────────

def _remotion_warm_up(url: str, job_id: str) -> bool:
    """
    Railway App Sleeping için warm-up: giderek artan timeout ile dener.
    Toplam max ~90 sn. True → yanıt verdi.
    """
    import httpx as _httpx
    attempts = [(15, 0), (30, 5), (45, 10)]  # (timeout_sn, önceki_bekleme_sn)
    for timeout, pre_sleep in attempts:
        if pre_sleep:
            logger.info(f"[video] {job_id[:8]} warm-up {pre_sleep}s bekliyor...")
            time.sleep(pre_sleep)
        try:
            r = _httpx.get(f"{url}/health", timeout=float(timeout))
            if r.status_code == 200:
                logger.info(f"[video] {job_id[:8]} Remotion yanıt verdi (timeout={timeout}s)")
                return True
            logger.warning(f"[video] {job_id[:8]} Remotion health HTTP {r.status_code}")
        except Exception as exc:
            logger.warning(f"[video] {job_id[:8]} warm-up timeout={timeout}s: {exc}")
    return False


# ── TTS — retry + pronunciation + cost tracking ───────────────

def _tts_bytes(text: str) -> tuple[bytes, int]:
    """
    OpenAI TTS — env'den gelen ses kimliği, exponential backoff.
    Pronunciation + TR normalizasyonu uygulanır.
    Returns: (ses_baytları, karakter_sayısı)
    Raises: PipelineErrorException — kota / auth hatası
            RuntimeError — geçici hata sonrası tüm denemeler başarısız
    """
    from openai import OpenAI
    from app.modules.content.openai_classifier import classify_openai_error
    from app.errors.registry import PipelineErrorException
    from app.modules.content.tr_speech_normalize import tr_speech_normalize

    text = apply_pronunciation_dict(tr_speech_normalize(text))

    # OpenAI TTS 4096 karakter sınırı — aşılırsa cümle sınırında kes
    _TTS_MAX = 4000
    if len(text) > _TTS_MAX:
        cut = text[:_TTS_MAX].rfind('. ')
        text = text[:cut + 1] if cut > _TTS_MAX // 2 else text[:_TTS_MAX]
        logger.warning(f"[tts] metin {len(text)} kara kısaltıldı (limit {_TTS_MAX})")

    char_count = len(text)
    client = OpenAI(api_key=settings.OPENAI_API_KEY, timeout=60.0)

    voice = settings.TTS_VOICE_ID
    model = settings.TTS_MODEL
    speed = settings.TTS_SPEED

    last_err = None
    for attempt, wait in enumerate(_TTS_BACKOFF, 1):
        try:
            resp = client.audio.speech.create(
                model=model,
                voice=voice,
                input=text,
                speed=speed,
            )
            logger.info(f"[tts] attempt={attempt} ok chars={char_count} voice={voice}")
            return resp.content, char_count
        except OpenAIRateLimitError as e:
            last_err = e
            kind = classify_openai_error(e)
            if kind == "insufficient_quota":
                raise PipelineErrorException(
                    "openai_insufficient_quota",
                    admin_detail={"raw_error": str(e)[:200], "stage": "tts"},
                    stage="tts",
                ) from e
            logger.warning(f"[tts] rate_limit attempt={attempt} retry_in={wait}s")
            time.sleep(wait)
        except APITimeoutError as e:
            last_err = e
            logger.warning(f"[tts] timeout attempt={attempt} retry_in={wait}s")
            time.sleep(wait)
        except Exception as e:
            raise RuntimeError(f"[tts] OpenAI hatası: {e}") from e

    raise RuntimeError(f"[tts] {len(_TTS_BACKOFF)} denemeden sonra başarısız: {last_err}")

# ── Hece bütçesi yardımcıları ─────────────────────────────────────────────────
TR_VOWELS: frozenset[str] = frozenset("aeıioöuüAEIİOÖUÜ")


def _syllable_count(text: str) -> int:
    return sum(1 for ch in text if ch in TR_VOWELS)


def _syllable_budget_params(
    budget_seconds: float, scene_count: int | None = None
) -> tuple[int, int, int]:
    """
    (toplam_hece_bütçesi, sahne_başına_hece, sahne_sayısı) hesaplar.
    scene_count verilmezse ceil(budget_seconds / 8.0) kullanılır.
    8.0 = ortalama sahne süresi saniye cinsinden (tek değişim noktası).
    TR_SPS (hece/saniye) shared/content-types.json'dan gelir — ölçülmüş
    değer (4.04-4.35, ort. ~4.15); eski 4.8 hiç ölçülmemişti.
    """
    import math
    n = scene_count if (scene_count and scene_count > 0) else math.ceil(budget_seconds / 8.0)
    n = max(1, n)
    total = round(budget_seconds * TR_SPS)
    per_scene = round(total / n)
    return total, per_scene, n


def _check_syllable_budget(
    storyboard: dict, budget_seconds: float
) -> tuple[bool, str | None]:
    """
    reels_short için sahne hece bütçesi doğrulaması.
    Bütçe = budget_seconds × TR_SPS hece/s; sahne başına hedef süreden türetilir.
    Toplam sahne hece sayısı %20'den fazla aşarsa (False, detay) döner.
    """
    scenes = storyboard.get("scenes", [])
    total_budget, syl_per_scene, _ = _syllable_budget_params(budget_seconds, len(scenes))
    tolerance = max(3, round(syl_per_scene * 0.15))
    lo, hi = syl_per_scene - tolerance, syl_per_scene + tolerance

    scene_details: list[str] = []
    total_syl = 0
    for s in scenes:
        syl = _syllable_count(s.get("voice_text") or "")
        total_syl += syl
        if syl < lo or syl > hi:
            scene_details.append(f"sahne {s.get('id', '?')}: {syl} hece")
    if total_syl > total_budget * 1.20:
        pct = (total_syl / total_budget - 1) * 100
        detail = (
            f"Hece bütçesi aşıldı: {total_syl:.0f}/{total_budget:.0f} hece "
            f"(%{pct:.0f} fazla). Sahne başına ~{syl_per_scene} hece (±{tolerance}) hedefle."
            + (f" Sorunlu: {'; '.join(scene_details[:4])}" if scene_details else "")
        )
        return False, detail
    return True, None


def _generate_storyboard_for_regen(
    content_type: str,
    payload,
    brand: dict,
    corrected_seconds: float,
    correction_hint: str,
) -> dict | None:
    """
    Tek bir üretim denemesi — hece bütçesi doğrulaması yapmaz.
    Desteklenmeyen içerik tipleri için None döner.
    _regen_storyboard_for_duration tarafından (gerekirse 2 kez) çağrılır.
    """
    if content_type == "reels_short":
        from app.modules.sgs.educational_reel_storyboard import generate_educational_reel_storyboard
        _, _, _regen_sc = _syllable_budget_params(corrected_seconds)
        sb_new = generate_educational_reel_storyboard(
            title=payload.title,
            topic=payload.topic or payload.title,
            subject=payload.lesson_name or "SGS",
            content_series=payload.content_series,
            description=payload.description or "",
            brand=brand,
            budget_seconds=corrected_seconds,
            syllable_feedback=correction_hint,
            scene_count=_regen_sc,
        )
        sb_new["format"] = payload.format or "9:16"
        for i, s in enumerate(sb_new.get("scenes", []), 1):
            s["id"] = i
        return sb_new

    elif content_type == "motivasyon":
        from app.modules.content.motivation_generator import generate_motivation_storyboard
        result = generate_motivation_storyboard(
            topic=payload.topic or payload.title,
            duration=max(15, int(corrected_seconds)),
            platform="reels",
        )
        scenes = []
        for i, scene in enumerate(result.get("scenes", []), 1):
            s = dict(scene)
            s["id"] = i
            if not s.get("component"):
                s["component"] = "MotivationScene"
            if not s.get("voice_text"):
                s["voice_text"] = s.get("narration") or s.get("spoken_text") or ""
            scenes.append(s)
        return {
            "video_type": payload.type,
            "title": result.get("title", payload.title),
            "format": payload.format,
            "language": "tr",
            "brand": brand,
            "scenes": scenes,
        }

    elif content_type == "konu_anlatimi":
        from app.modules.sgs.lesson_storyboard import generate_lesson_storyboard
        corrected_min = max(1.0, corrected_seconds / 60.0)
        raw = generate_lesson_storyboard(
            title=payload.title,
            topic=payload.topic or payload.title,
            subject=payload.lesson_name or "SGS",
            target_minutes=corrected_min,
            description=payload.description or "",
        )
        scenes = raw.get("scenes", [])
        for i, s in enumerate(scenes, 1):
            s["id"] = i
        return {
            "video_type": "konu_anlatimi",
            "title": payload.title,
            "lesson_name": payload.lesson_name,
            "topic": payload.topic,
            "format": payload.format,
            "language": "tr",
            "brand": brand,
            "scenes": scenes,
        }

    return None  # soru_cozum / gorsel_post — yeniden üretim desteklenmiyor


def _regen_storyboard_for_duration(
    content_type: str,
    payload,
    brand: dict,
    corrected_seconds: float,
    correction_hint: str,
    turn: int = 0,
) -> tuple[dict | None, dict | None]:
    """
    Süre düzeltmesiyle storyboard yeniden üretir, ardından hece bütçesini
    doğrular (en fazla 2 deneme). Bu doğrulama reels_short/motivasyon/
    konu_anlatimi — _generate_storyboard_for_regen'in desteklediği TÜM
    tiplerde uygulanır, yalnızca reels_short'a özel değildir.

    Döner: (storyboard, None)                       → başarı
           (None, None)                              → içerik tipi desteklenmiyor
           (None, {"reason": ..., ...})               → 2 denemede de hece bütçesi
                                                          aşıldı — çağıran job'u
                                                          TTS'e göndermeden durdurmalı
    """
    sb_new = _generate_storyboard_for_regen(content_type, payload, brand, corrected_seconds, correction_hint)
    if sb_new is None:
        return None, None

    feedback = correction_hint
    for attempt in (1, 2):
        scenes = sb_new.get("scenes", [])
        total_budget, _, _ = _syllable_budget_params(corrected_seconds, len(scenes))
        actual_syl = sum(_syllable_count(s.get("voice_text") or "") for s in scenes)
        pct = ((actual_syl / total_budget) - 1) * 100 if total_budget else 0.0
        ok, detail = _check_syllable_budget(sb_new, corrected_seconds)
        logger.warning(
            "[syllable-budget] tur=%d hedef_hece=%d üretilen_hece=%d sapma=%%%.0f deneme=%d/2",
            turn, total_budget, actual_syl, pct, attempt,
        )
        if ok:
            return sb_new, None
        if attempt == 1:
            feedback = detail or feedback
            sb_new = _generate_storyboard_for_regen(content_type, payload, brand, corrected_seconds, feedback)
            if sb_new is None:
                return None, None

    # 2 deneme sonunda hâlâ aşılıyor — sessizce TTS'e gönderilmez (çağıran durdurur).
    return None, {
        "reason": "syllable_budget_exceeded_after_regen",
        "target_syllables": total_budget,
        "actual_syllables": actual_syl,
        "deviation_pct": round(pct, 1),
    }


def _ffprobe_duration(audio_bytes: bytes) -> tuple[float | None, str | None]:
    """ffprobe ile gerçek ses süresini ölçer.
    Dönüş: (saniye, None) — başarı | (None, hata_mesajı) — başarısızlık.
    "estimated" yolu yoktur; hata_mesajı duration_source="missing" yazarken kaydedilir.
    """
    import subprocess
    import tempfile
    import os
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name
        result = subprocess.run(
            [
                "ffprobe", "-v", "quiet",
                "-print_format", "json",
                "-show_streams",
                tmp_path,
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            err = f"ffprobe returncode={result.returncode} stderr={result.stderr[:200]}"
            return None, err
        import json as _json_probe
        data = _json_probe.loads(result.stdout)
        for stream in data.get("streams", []):
            dur = stream.get("duration")
            if dur is not None:
                return float(dur), None
        return None, "ffprobe: akışlarda 'duration' alanı bulunamadı"
    except Exception as exc:
        err = f"{type(exc).__name__}: {exc}"
        logger.warning("[video] ffprobe ölçümü başarısız: %s", exc)
        return None, err
    finally:
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

def _upload_tts(audio_bytes: bytes, filename: str) -> str:
    """TTS ses dosyasını Supabase Storage'a yükle, public URL döndür."""
    sb = get_supabase_client()
    try:
        buckets = [b.name if hasattr(b, "name") else b.get("name", "") for b in sb.storage.list_buckets()]
        if VIDEO_BUCKET not in buckets:
            sb.storage.create_bucket(VIDEO_BUCKET, options={"public": True})
    except Exception as e:
        logger.warning(f"[video] TTS bucket kontrol: {e}")
    path = f"scenes/{filename}"
    sb.storage.from_(VIDEO_BUCKET).upload(path, audio_bytes, {"content-type": "audio/mpeg", "upsert": "true"})
    return sb.storage.from_(VIDEO_BUCKET).get_public_url(path)


# ── Quiz storyboard üretimi ───────────────────────────────────

def _build_quiz_storyboard(
    title: str, lesson_name: str, topic: str,
    questions: List[QuizQuestion], format: str, brand: dict,
    description: str = "",
) -> dict:
    """
    Her soru için bir SplitQuizScene (16:9) veya SplitQuizVerticalScene (9:16) üretir.
    Sol panel = soru + şıklar, Sağ panel = çözüm adımları animasyonlu açılır.
    """
    total = len(questions)
    scenes = []
    sid = 1
    scene_component = "SplitQuizVerticalScene" if format == "9:16" else "SplitQuizScene"

    intro_voice = (
        f"Merhaba. Bu videoda {lesson_name} dersinden {topic} konusuna ait "
        f"{total} soruyu birlikte çözeceğiz."
    )
    if description:
        intro_voice += f" {description}"

    scenes.append({
        "id": sid, "component": "IntroScene", "duration_seconds": 8,
        "title": title,
        "subtitle": f"{lesson_name} — Soru Çözüm Serisi",
        "voice_text": intro_voice,
    })
    sid += 1

    for i, q in enumerate(questions):
        qno = i + 1
        correct_opt = next((o for o in q.options if o.label == q.correct_label), None)
        explanation = q.explanation or (f"{correct_opt.text}" if correct_opt else "")

        solution_steps = []
        solution_steps.append({
            "type": "text",
            "text": f"Doğru cevap: {q.correct_label} — {correct_opt.text if correct_opt else ''}",
        })
        if explanation:
            solution_steps.append({"type": "text", "text": explanation})

        voice_text = (
            f"{qno}. soru: {q.text}. "
            "Seçenekler: "
            + " ".join(f"{o.label} şıkkı: {o.text}" for o in q.options)
            + f". Doğru cevap {q.correct_label} şıkkıdır. {explanation}"
        )

        scenes.append({
            "id": sid,
            "component": scene_component,
            "duration_seconds": 35,
            "question_number": qno,
            "total_questions": total,
            "question_text": q.text,
            "options": [{"label": o.label, "text": o.text} for o in q.options],
            "correct_label": q.correct_label,
            "reveal_correct": True,
            "solution_steps": solution_steps,
            "explanation": explanation,
            "title": lesson_name,
            "voice_text": voice_text,
        })
        sid += 1

    scenes.append({
        "id": sid, "component": "OutroScene", "duration_seconds": 8,
        "title": "Soru Çözümü Tamamlandı",
        "subtitle": f"{lesson_name} dersinden {total} soru çözüldü. Başarılar!",
        "voice_text": (
            f"Bu videoda {lesson_name} dersinden {total} soruyu birlikte çözdük. "
            "Umarım faydalı olmuştur. Başarılar!"
        ),
    })

    return {
        "video_type": "quiz",
        "title": title,
        "lesson_name": lesson_name,
        "topic": topic,
        "format": format,
        "language": "tr",
        "brand": brand,
        "scenes": scenes,
    }


# ── Remotion render yardımcısı ───────────────────────────────

def _run_remotion_render(job_id: str, storyboard: dict, has_audio: bool = True) -> None:
    """Devre kesici → warm-up → /render POST → status güncelleme."""
    import httpx
    global _remotion_consecutive_failures

    remotion_url = settings.REMOTION_URL
    is_configured = bool(
        remotion_url
        and "localhost" not in remotion_url
        and "127.0.0.1" not in remotion_url
    )
    if not is_configured:
        logger.info(f"[video] {job_id[:8]} Remotion yapılandırılmamış → hazır")
        _set_status(job_id, "ready_for_review", {
            "error_message": (
                ("Render sunucusu bağlı değil — ses sahneleri hazır. " if has_audio
                 else "Render sunucusu bağlı değil — storyboard hazır. ")
                + "REMOTION_URL ortam değişkenini yapılandırın."
            )
        })
        return

    with _remotion_lock:
        circuit_open = _remotion_consecutive_failures >= _CIRCUIT_OPEN_THRESHOLD
        fail_count = _remotion_consecutive_failures

    if circuit_open:
        logger.warning(f"[video] {job_id[:8]} devre kesici açık ({fail_count} ardışık hata)")
        _set_status(job_id, "ready_for_review", {
            "error_message": (
                f"Render servisi yanıt vermiyor (devre kesici: {fail_count} ardışık hata). "
                + ("Ses sahneleri hazır — servis düzelince 'Yeniden Dene' ile render başlatın."
                   if has_audio else
                   "Storyboard hazır — servis düzelince 'Yeniden Dene' ile render başlatın.")
            )
        })
        return

    _set_status(job_id, "warmup_pinging")
    logger.info(f"[video] {job_id[:8]} Remotion warm-up başlıyor ({remotion_url})")
    service_up = _remotion_warm_up(remotion_url, job_id)

    if not service_up:
        with _remotion_lock:
            _remotion_consecutive_failures += 1
            fail_count = _remotion_consecutive_failures
        logger.error(f"[video] {job_id[:8]} Remotion 90s içinde yanıt vermedi (ardışık: {fail_count})")
        _set_status(job_id, "failed", {
            "error_message": (
                "Render servisi 90 saniye boyunca yanıt vermedi. "
                "Railway servisinin ayakta olduğundan emin olup 'Yeniden Dene' ile tekrar başlatın."
            )
        })
        return

    with _remotion_lock:
        _remotion_consecutive_failures = 0

    # Bridge atomik geçişi: status='warmup_pinging' → 'rendering' (bridge tarafında kontrol edilir).
    # Backend 'warmup_pinging' yazar; bridge POST aldıktan sonra 'warmup_pinging'→'rendering' günceller.
    # Eğer iki worker aynı job'u gönderirse, ikincisi bridge'de WHERE status='warmup_pinging'
    # koşulunu geçemez ve render atlanır.
    _set_status(job_id, "warmup_pinging")
    logger.info(f"[video] {job_id[:8]} Remotion render tetikleniyor (status=warmup_pinging)")
    try:
        resp = httpx.post(
            f"{remotion_url}/render",
            json={"job_id": job_id, "storyboard": storyboard},
            timeout=60,
        )
        if resp.status_code != 200:
            raise Exception(f"Render başarısız (HTTP {resp.status_code}): {resp.text[:200]}")
        logger.info(f"[video] {job_id[:8]} Remotion render başlatıldı: {resp.json()}")
    except Exception as e:
        with _remotion_lock:
            _remotion_consecutive_failures += 1
        logger.error(f"[video] {job_id[:8]} Remotion render hatası: {e}")
        _set_status(job_id, "failed", {
            "error_message": (
                f"Render başarısız: {str(e)[:300]} — "
                + ("Ses sahneleri hazır. Railway servisini kontrol edip 'Yeniden Dene' ile tekrar başlatın."
                   if has_audio else
                   "Railway servisini kontrol edip 'Yeniden Dene' ile tekrar başlatın.")
            )
        })


# ── Arkaplan pipeline ─────────────────────────────────────────

def _run_pipeline(
    job_id: str,
    payload: CreateVideoPayload,
    _seed_corrected_sec: float | None = None,
    _seed_hint: str | None = None,
    _seed_turn: int = 0,
):
    """
    Storyboard → TTS → Remotion render pipeline'ı.
    Eşzamanlı çalışma _pipeline_semaphore ile sınırlandırılır.

    _seed_* parametreleri yalnızca render-sonrası süre kapalı döngüsü
    (bkz. render_callback) tarafından kullanılır: postcheck ölçülen gerçek
    süreyle storyboard'u yeniden ürettirmek için mevcut süre döngüsünü
    (bkz. _run_pipeline_inner) belirli bir turdan başlatır.
    """
    acquired = _pipeline_semaphore.acquire(timeout=600)
    if not acquired:
        logger.error(f"[video] {job_id} semaphore alınamadı — başka pipeline dolup taştı")
        _set_status(job_id, "failed", {
            "error_message": "Sistem meşgul. Lütfen birkaç dakika sonra yeniden deneyin."
        })
        return

    try:
        _run_pipeline_inner(job_id, payload, _seed_corrected_sec, _seed_hint, _seed_turn)
    finally:
        _pipeline_semaphore.release()


def _run_pipeline_inner(
    job_id: str,
    payload: CreateVideoPayload,
    _seed_corrected_sec: float | None = None,
    _seed_hint: str | None = None,
    _seed_turn: int = 0,
):
    """Gerçek pipeline mantığı — semaphore altında çalışır."""
    from app.domain.content_type import normalize_content_type
    from app.errors.registry import PipelineErrorException
    sb = get_supabase_client()
    brand = _get_brand()
    total_tts_chars = 0

    # ── 0. Tip normalizasyonu (kanonik türe çevir) ────────────────
    try:
        content_type = normalize_content_type(payload.type)
    except PipelineErrorException as e:
        logger.error(f"[video] {job_id[:8]} unknown_content_type raw={payload.type!r}")
        _set_status(job_id, "failed", {
            "error_code": e.error_code,
            "error_message": e.user_message,
        })
        return
    logger.info(f"[video] {job_id[:8]} content_type={content_type!r} raw={payload.type!r}")

    try:
        # ── -1. İçerik tekrar kontrolü (Section 2) ─────────────────
        if payload.content_series and content_type not in ("gorsel_post", "infographic"):
            is_dup, similar_title, sim_score = check_content_duplicate(
                title=payload.title,
                topic=payload.topic or payload.title,
                content_series=payload.content_series,
            )
            if is_dup:
                logger.warning(
                    f"[video] {job_id[:8]} tekrar içerik: '{similar_title}' "
                    f"(benzerlik={sim_score:.3f}) — devam ediliyor (override)"
                )
                sb.table("video_jobs").update({
                    "error_message": (
                        f"Uyarı: Benzer içerik daha önce üretildi → '{similar_title}' "
                        f"(benzerlik: {sim_score:.0%}). Yine de üretildi."
                    )
                }).eq("id", job_id).execute()

        # ── 0. İnfografik / Görsel post (TTS yok, Remotion olmadan doğrudan hazır) ──
        if content_type == "gorsel_post":
            _set_status(job_id, "scripting")
            storyboard = payload.pre_storyboard or {}
            if not storyboard:
                from app.modules.content.infographic_generator import generate_infographic_storyboard
                topic = payload.topic or payload.title or "Genel Muhasebe"
                template = payload.infographic_template or "card_grid"
                storyboard = generate_infographic_storyboard(topic, template=template)
                logger.info(f"[video] {job_id[:8]} infografik storyboard üretildi topic='{topic}'")
            sb.table("video_jobs").update({"storyboard": storyboard, "updated_at": "now()"}).eq("id", job_id).execute()
            _set_status(job_id, "ready_for_review")
            logger.info(f"[video] {job_id[:8]} infografik bağımsız yol — Remotion atlandı, storyboard hazır")
            return

        # ── 1. Senaryo ──────────────────────────────────────────
        _set_status(job_id, "scripting")
        logger.info(f"[video] {job_id} senaryo oluşturuluyor content_type={content_type}")

        if content_type == "soru_cozum" and payload.questions:
            if payload.format == "9:16":
                # Dikey kısa quiz — SplitQuizVerticalScene kalır
                storyboard = _build_quiz_storyboard(
                    title=payload.title,
                    lesson_name=payload.lesson_name or "",
                    topic=payload.topic or "",
                    questions=payload.questions,
                    format=payload.format,
                    brand=brand,
                    description=payload.description or "",
                )
            else:
                # Yatay 16:9 quiz — öğretmen tahtası (ChalkboardSolutionScene)
                from app.modules.sgs.storyboard import generate_sgs_question_storyboard
                questions_dict = [
                    {
                        "question_text": q.text,
                        "options": [{"label": o.label, "text": o.text} for o in q.options],
                        "correct_option": q.correct_label,
                        "explanation": q.explanation or "",
                    }
                    for q in payload.questions
                ]
                raw = generate_sgs_question_storyboard(
                    title=payload.title,
                    topic=payload.topic or payload.title,
                    subject=payload.lesson_name or "SGS",
                    questions=questions_dict,
                )
                scenes = raw.get("scenes", [])
                for i, s in enumerate(scenes, 1):
                    s["id"] = i
                storyboard = {
                    "video_type": "quiz",
                    "title": payload.title,
                    "lesson_name": payload.lesson_name,
                    "topic": payload.topic,
                    "format": payload.format,
                    "language": "tr",
                    "brand": brand,
                    "scenes": scenes,
                }
                chalk_count = sum(1 for s in scenes if s.get("component") == "ChalkboardSolutionScene")
                if chalk_count < len(payload.questions):
                    logger.warning(
                        f"[video] {job_id[:8]} kalite: {chalk_count}/{len(payload.questions)} "
                        "ChalkboardSolutionScene üretildi — storyboard eksik olabilir"
                    )
        elif content_type == "soru_cozum" and not payload.questions:
            # Soru çözüm — soru listesi olmadan gelen istek (panel topic-only gönderimi)
            raise RuntimeError(
                "Soru çözüm videosu için en az 1 soru gerekli. "
                "Panel'de soruları ekleyin veya İçerik Otomasyonu'ndan soru seçin."
            )

        elif content_type == "motivasyon":
            from app.modules.content.motivation_generator import generate_motivation_storyboard
            topic_text = payload.topic or payload.title
            # requested_duration_seconds Pydantic validator ile int garantili
            raw_dur = payload.requested_duration_seconds
            if raw_dur is None and payload.target_duration_minutes:
                raw_dur = payload.target_duration_minutes * 60
            duration_sec: int = raw_dur if (raw_dur and 15 <= raw_dur <= 300) else 120
            result = generate_motivation_storyboard(
                topic=topic_text,
                duration=duration_sec,
                platform="reels",
            )
            scenes = []
            for i, scene in enumerate(result.get("scenes", []), 1):
                s = dict(scene)
                s["id"] = i
                # component yoksa fallback
                if not s.get("component"):
                    s["component"] = "MotivationScene"
                # voice_text normalizasyonu
                if not s.get("voice_text"):
                    s["voice_text"] = s.get("narration") or s.get("spoken_text") or ""
                scenes.append(s)
            storyboard = {
                "video_type": payload.type,
                "title": result.get("title", payload.title),
                "format": payload.format,
                "language": "tr",
                "brand": brand,
                "scenes": scenes,
            }

        elif content_type == "reels_short":
            # EducationalReel120 — GPT storyboard + EducationalReelScene bileşeni
            from app.modules.sgs.educational_reel_storyboard import generate_educational_reel_storyboard
            _reel_budget_sec = float(payload.requested_duration_seconds or 120)
            _, _, _reel_sc = _syllable_budget_params(_reel_budget_sec)
            storyboard = generate_educational_reel_storyboard(
                title=payload.title,
                topic=payload.topic or payload.title,
                subject=payload.lesson_name or "SGS",
                content_series=payload.content_series,
                description=payload.description or "",
                brand=brand,
                budget_seconds=_reel_budget_sec,
                scene_count=_reel_sc,
            )
            storyboard["format"] = payload.format or "9:16"
            for i, s in enumerate(storyboard.get("scenes", []), 1):
                s["id"] = i

            # ── Hece bütçesi kontrolü — TTS'den önce, 1 yeniden deneme ──────
            _syl_ok, _syl_detail = _check_syllable_budget(storyboard, _reel_budget_sec)
            if not _syl_ok:
                logger.warning(
                    "[video] %s hece bütçesi aşıldı — 1 yeniden deneme: %s",
                    job_id[:8], _syl_detail,
                )
                storyboard = generate_educational_reel_storyboard(
                    title=payload.title,
                    topic=payload.topic or payload.title,
                    subject=payload.lesson_name or "SGS",
                    content_series=payload.content_series,
                    description=payload.description or "",
                    brand=brand,
                    budget_seconds=_reel_budget_sec,
                    syllable_feedback=_syl_detail,
                    scene_count=_reel_sc,
                )
                storyboard["format"] = payload.format or "9:16"
                for i, s in enumerate(storyboard.get("scenes", []), 1):
                    s["id"] = i
                _syl_ok2, _syl_detail2 = _check_syllable_budget(storyboard, _reel_budget_sec)
                if not _syl_ok2:
                    logger.warning(
                        "[video] %s 2. deneme sonrası hece aşımı devam ediyor: %s — devam edildi",
                        job_id[:8], _syl_detail2,
                    )

        elif content_type == "konu_anlatimi":
            from app.modules.sgs.lesson_storyboard import generate_lesson_storyboard
            raw = generate_lesson_storyboard(
                title=payload.title,
                topic=payload.topic or payload.title,
                subject=payload.lesson_name or "SGS",
                target_minutes=payload.target_duration_minutes or 20,
                description=payload.description or "",
            )
            scenes = raw.get("scenes", [])
            if len(scenes) < 8:
                raise RuntimeError(
                    f"Konu anlatımı: yalnızca {len(scenes)} sahne üretildi "
                    "(minimum 8 gerekli, ideal 12-15). Storyboard yeniden üretiliyor."
                )
            total_sec = sum(s.get("duration_seconds") or 0 for s in scenes)
            if total_sec < 600:
                logger.warning(
                    f"[video] {job_id[:8]} uyarı: toplam sahne süresi {total_sec:.0f}s < 600s (10dk). "
                    "Storyboard kısa olabilir."
                )
            for i, s in enumerate(scenes, 1):
                s["id"] = i
            storyboard = {
                "video_type": "konu_anlatimi",
                "title": payload.title,
                "lesson_name": payload.lesson_name,
                "topic": payload.topic,
                "format": payload.format,
                "language": "tr",
                "brand": brand,
                "scenes": scenes,
            }

        else:
            # Normalize edilmiş tip tanınmıyor — sessiz fallback yerine açık hata
            logger.error(
                f"[video] {job_id[:8]} bilinmeyen tip normalize_sonrasi={content_type!r} raw={payload.type!r}"
            )
            _set_status(job_id, "failed", {
                "error_code": "unknown_content_type",
                "error_message": f"Desteklenmeyen içerik türü: {payload.type!r}",
            })
            return

        # ── FAZ 2: Routing doğrulaması (hard fail) ───────────────
        from app.pipelines.registry import validate_routing
        try:
            validate_routing(content_type, storyboard.get("scenes", []))
        except PipelineErrorException as rte:
            logger.error(
                f"[video] {job_id[:8]} routing_failed error={rte.error_code} "
                f"detail={rte.admin_detail}"
            )
            _set_status(job_id, "failed", {
                "error_code": rte.error_code,
                "error_message": rte.user_message,
            })
            return

        # ── FAZ 5: Unicode doğrulaması (hard fail) ───────────────
        from app.modules.content.unicode_validator import (
            validate_storyboard_unicode, nfc_normalize_storyboard,
        )
        storyboard = nfc_normalize_storyboard(storyboard)
        unicode_errors = validate_storyboard_unicode(storyboard)
        if unicode_errors:
            logger.error(f"[video] {job_id[:8]} unicode_validation_failed: {unicode_errors[:3]}")
            _set_status(job_id, "failed", {
                "error_code": "unicode_validation_failed",
                "error_message": "Metinde bozuk karakter tespit edildi: " + unicode_errors[0],
            })
            return

        # ── FAZ 3: Asset doğrulaması (hard fail) ─────────────────
        from app.modules.content.asset_validator import validate_brand_assets
        asset_errors = validate_brand_assets(brand.get("logo_url"), job_id)
        if asset_errors:
            fatal = [e for e in asset_errors if e["error_code"] == "font_asset_missing"]
            if fatal:
                err = fatal[0]
                _set_status(job_id, "failed", {
                    "error_code": err["error_code"],
                    "error_message": err["detail"],
                })
                return
            # Logo hatası: sadece logla, Supabase URL fallback kullanılacak
            for ae in asset_errors:
                logger.warning(f"[asset] {job_id[:8]} {ae['error_code']}: {ae['detail']}")

        # ── Storyboard kalite kontrolü ────────────────────────────
        quality_warnings = check_storyboard_quality(storyboard, content_type)
        if quality_warnings:
            logger.warning(
                f"[video] {job_id[:8]} storyboard kalite uyarıları: {quality_warnings}"
            )
            sb.table("video_jobs").update({
                "error_message": "Kalite uyarısı: " + " | ".join(quality_warnings)
            }).eq("id", job_id).execute()

        # ── Pazarlama uyumu (danışan hattı) — hard fail ───────────
        job_row = sb.table("video_jobs").select("content_track").eq("id", job_id).execute()
        job_track = (job_row.data or [{}])[0].get("content_track")
        marketing_errors = check_marketing_compliance(storyboard, job_track)
        if marketing_errors:
            logger.error(f"[video] {job_id[:8]} marketing_compliance_failed: {marketing_errors[:2]}")
            _set_status(job_id, "failed", {
                "error_code": "marketing_compliance_failed",
                "error_message": (
                    "Danışan hattı içeriğinde yasak pazarlama ifadesi tespit edildi. "
                    "TÜRMOB meslek kuralları: bilgilendirici ton zorunlu."
                ),
                "admin_detail": {"violations": marketing_errors},
            })
            return

        # ── İçerik parmak izi kaydet ──────────────────────────────
        save_content_fingerprint(
            job_id=job_id,
            title=payload.title,
            topic=payload.topic or payload.title,
            content_series=payload.content_series,
        )

        # ── 2. TTS + süre kapalı döngüsü (maks 2 yeniden üretim) ───────────
        # Her turda: storyboard → sahne kayıtları → TTS → süre doğrulaması.
        # Süre tolerans dışındaysa storyboard düzeltme ipucuyla yeniden üretilir.
        # _seed_* doluysa bu çağrı render-sonrası kapalı döngüden (render_callback)
        # tetiklenmiştir — gerçek ölçülen süreyle hesaplanmış düzeltme burada devralınır.
        _dur_correction_hint: str | None = _seed_hint
        _dur_corrected_sec: float = (
            _seed_corrected_sec if _seed_corrected_sec is not None
            else float(payload.requested_duration_seconds or 0)
        )
        # Tolerans tek kaynaktan gelir: payload.duration_tolerance_seconds
        # (video_jobs.duration_tolerance_seconds kolonu, çağıranın gönderdiği değer).
        # Yüzde tabanlı ayrı bir formül YOK — panel ve kod aynı sayıyı görmeli.
        # Hem bu döngüde hem Remotion'a gönderilen storyboard'da (aşağıda) kullanılır.
        _dur_tolerance_sec: float | None = (
            float(payload.duration_tolerance_seconds)
            if payload.requested_duration_seconds else None
        )

        for _dur_turn in range(_seed_turn, 3):  # tur 0 = orijinal, tur 1-2 = yeniden üretim
            if _dur_turn > 0:
                logger.info(
                    "[video] %s duration döngüsü tur=%d yeniden üretim başlıyor: %s",
                    job_id[:8], _dur_turn, _dur_correction_hint,
                )
                _new_sb, _budget_exceeded = _regen_storyboard_for_duration(
                    content_type, payload, brand,
                    _dur_corrected_sec, _dur_correction_hint or "",
                    turn=_dur_turn,
                )
                if _budget_exceeded is not None:
                    logger.error(
                        "[syllable-budget] %s job durduruldu — 2 denemede de bütçe aşıldı: %s",
                        job_id[:8], _budget_exceeded,
                    )
                    _set_status(job_id, "failed", {
                        "error_code": "duration_validation_failed",
                        "error_message": (
                            f"Storyboard yeniden üretiminde hece bütçesi 2 denemede de aşıldı "
                            f"(hedef {_budget_exceeded['target_syllables']} hece, "
                            f"üretilen {_budget_exceeded['actual_syllables']} hece, "
                            f"%{_budget_exceeded['deviation_pct']:.0f} fazla). "
                            "TTS'e gönderilmedi."
                        ),
                        "admin_detail": {"budget_exceeded": _budget_exceeded},
                        "quality_report": {"budget_exceeded": _budget_exceeded},
                    })
                    return
                if _new_sb is None:
                    _set_status(job_id, "failed", {
                        "error_code": "duration_validation_failed",
                        "error_message": (
                            f"Süre toleransı 2 turda geçilemedi ve bu içerik tipi "
                            f"({content_type}) için otomatik yeniden üretim desteklenmiyor."
                        ),
                    })
                    return
                storyboard = _new_sb
                sb.table("video_scenes").delete().eq("job_id", job_id).execute()
                total_tts_chars = 0

            sb.table("video_jobs").update({"storyboard": storyboard, "updated_at": "now()"}).eq("id", job_id).execute()

            scene_records = [
                {
                    "job_id": job_id,
                    "scene_index": s["id"] - 1,
                    "component": s["component"],
                    "duration_seconds": s.get("duration_seconds", 10),
                    "data": s,
                    "voice_text": s.get("voice_text"),
                    "status": "pending",
                }
                for s in storyboard["scenes"]
            ]
            sb.table("video_scenes").insert(scene_records).execute()

            _set_status(job_id, "tts_generating")
            logger.info(
                "[video] %s TTS başlıyor tur=%d (%d sahne)",
                job_id, _dur_turn, len(storyboard["scenes"]),
            )

            scenes_in_db = (
                sb.table("video_scenes")
                .select("*").eq("job_id", job_id).order("scene_index")
                .execute().data or []
            )

            _tts_hard_fail = False
            for scene_row in scenes_in_db:
                voice_text = (scene_row.get("voice_text") or "").strip()
                if not voice_text:
                    continue
                try:
                    audio_bytes, char_count = _tts_bytes(voice_text)
                    total_tts_chars += char_count

                    # ses seviyesi kontrolü — sessiz TTS yeniden üretilir
                    vol_ok, mean_vol = check_audio_volume(audio_bytes)
                    if not vol_ok:
                        logger.warning(
                            "[video] %s sahne %s sessiz TTS (%.1fdB) — yeniden üretiliyor",
                            job_id, scene_row["scene_index"], mean_vol,
                        )
                        audio_bytes, char_count2 = _tts_bytes(voice_text)
                        total_tts_chars += char_count2
                        vol_ok2, mean_vol2 = check_audio_volume(audio_bytes)
                        if not vol_ok2:
                            logger.error(
                                "[video] %s sahne %s yeniden deneme de sessiz (%.1fdB) — durduruluyor",
                                job_id, scene_row["scene_index"], mean_vol2,
                            )
                            _set_status(job_id, "failed", {
                                "error_code": "tts_generation_failed",
                                "error_message": (
                                    f"Sahne {scene_row['scene_index'] + 1} için ses üretilemedi "
                                    f"(2 denemede de sessiz, {mean_vol2:.0f} dB). "
                                    "OpenAI TTS çıktısını kontrol edin."
                                ),
                                "cost_tts_chars": total_tts_chars,
                            })
                            _tts_hard_fail = True
                            break

                    # ── Ses normalizasyonu (M4) — hedef -16 LUFS ────────────
                    # Sessizlik kontrolünden SONRA (ham TTS'in gerçekten
                    # sessiz olup olmadığını maskelemeyelim), yüklemeden ÖNCE.
                    # Başarısızsa normalize_loudness ham ses döner (loglanır);
                    # kalıcı sapmayı postcheck'teki LUFS kapısı yakalar.
                    audio_bytes = normalize_loudness(audio_bytes)

                    filename = f"{job_id}_{scene_row['scene_index']}.mp3"
                    tts_url = _upload_tts(audio_bytes, filename)
                    audio_duration, ffprobe_err = _ffprobe_duration(audio_bytes)

                    if audio_duration is not None:
                        duration_source = "ffprobe"
                        duration = audio_duration
                        scene_update: dict = {
                            "tts_url": tts_url,
                            "audio_duration_seconds": audio_duration,
                            "duration_seconds": duration,
                            "duration_source": duration_source,
                            "status": "tts_done",
                        }
                        logger.info(
                            "[video] %s sahne %s ffprobe=%.2fs duration_source=ffprobe",
                            job_id, scene_row["scene_index"], audio_duration,
                        )

                        # ── Altyazı (M3) — yalnızca 9:16 (CaptionOverlay diğer
                        # formatlarda kapalı; gereksiz Whisper maliyeti önlenir) ──
                        captions: list[dict] = []
                        if storyboard.get("format") == "9:16":
                            from app.modules.content.caption_generator import (
                                generate_captions, transcribe_word_timestamps,
                            )
                            word_ts = transcribe_word_timestamps(
                                audio_bytes, scene_index=scene_row["scene_index"],
                            )
                            captions = generate_captions(
                                voice_text=voice_text,
                                total_seconds=audio_duration,
                                start_offset=0.0,   # sahne-göreli — Remotion kompozisyon offset'ini kendi ekliyor
                                word_timestamps=word_ts,
                            )
                            if not captions:
                                logger.error(
                                    "[caption] %s sahne %s altyazı üretilemedi (word_ts=%s)",
                                    job_id[:8], scene_row["scene_index"], bool(word_ts),
                                )
                            scene_update["captions"] = captions
                    else:
                        # "estimated" yolu yok — hard fail
                        scene_update = {
                            "tts_url": tts_url,
                            "duration_source": "missing",
                            "measurement_error": ffprobe_err or "ffprobe başarısız",
                            "status": "tts_failed",
                            "error_code": "failed_audio_validation",
                        }
                        sb.table("video_scenes").update(scene_update).eq("id", scene_row["id"]).execute()
                        logger.error(
                            "[video] %s sahne %s ffprobe başarısız — failed_audio_validation: %s",
                            job_id, scene_row["scene_index"], ffprobe_err,
                        )
                        from app.errors.registry import PipelineErrorException
                        raise PipelineErrorException(
                            error_code="failed_audio_validation",
                            user_message=(
                                f"Sahne {scene_row['scene_index'] + 1} ses süresi ölçülemedi "
                                f"(ffprobe başarısız). Render başlatılmadı."
                            ),
                            admin_detail={
                                "scene_index": scene_row["scene_index"],
                                "ffprobe_error": ffprobe_err,
                                "duration_source": "missing",
                            },
                        )

                    try:
                        sb.table("video_scenes").update(scene_update).eq("id", scene_row["id"]).execute()
                    except Exception as db_exc:
                        # M3 savunması: video_scenes.captions kolonunun canlı DB'de
                        # var olduğu migration'dan (014_p0_schema_fixes.sql) doğrulanamadı
                        # — o migration'ın canlıya hiç uygulanmadığı zaten biliniyor
                        # (bkz. render_cost_usd postmortem). Kolon yoksa TTS'in kendisi
                        # başarılıyken bu yüzden job'un tamamı düşmesin — captions'sız
                        # tekrar dene, açıkça logla (sessiz değil).
                        if "captions" in scene_update:
                            logger.error(
                                "[caption] %s sahne %s video_scenes güncellemesi captions "
                                "alanıyla başarısız (kolon eksik olabilir) — captions'sız "
                                "yeniden deneniyor: %s",
                                job_id[:8], scene_row["scene_index"], db_exc,
                            )
                            retry_update = {k: v for k, v in scene_update.items() if k != "captions"}
                            sb.table("video_scenes").update(retry_update).eq("id", scene_row["id"]).execute()
                        else:
                            raise

                    for s in storyboard["scenes"]:
                        if s["id"] - 1 == scene_row["scene_index"]:
                            s["tts_url"] = tts_url
                            s["duration_seconds"] = duration
                            s["duration_source"] = duration_source
                            if "captions" in scene_update:
                                s["captions"] = scene_update["captions"]
                            break

                    logger.info(
                        "[video] %s sahne %s TTS ok (%.1fs duration_source=%s)",
                        job_id, scene_row["scene_index"], duration, duration_source,
                    )

                except Exception as e:
                    from app.errors.registry import PipelineErrorException
                    if isinstance(e, PipelineErrorException) and e.error_code == "openai_insufficient_quota":
                        logger.error("[video] %s kota hatası — pipeline durduruluyor", job_id)
                        _set_status(job_id, "failed", {
                            "error_code": "openai_insufficient_quota",
                            "error_message": e.user_message,
                            "cost_tts_chars": total_tts_chars,
                        })
                        _tts_hard_fail = True
                        break
                    if isinstance(e, PipelineErrorException) and e.error_code == "failed_audio_validation":
                        _set_status(job_id, "failed", {
                            "error_code": "failed_audio_validation",
                            "error_message": e.user_message,
                            "admin_detail": e.admin_detail,
                            "cost_tts_chars": total_tts_chars,
                        })
                        _tts_hard_fail = True
                        break
                    import json as _json
                    detail = {
                        "exc_type": type(e).__name__,
                        "status_code": getattr(e, "status_code", None),
                        "message": str(e),
                        "scene_index": scene_row["scene_index"],
                        "traceback": _traceback.format_exc(),
                    }
                    _log_entry = {"event": "tts_scene_failed", "job_id": job_id, **detail}
                    logger.error(
                        "TTS_HATA %s",
                        _json.dumps(_log_entry, ensure_ascii=False, default=str),
                        exc_info=False,
                    )
                    try:
                        sb.table("video_scenes").update({
                            "status": "tts_failed",
                            "error_code": "tts_generation_failed",
                            "error_detail": detail,
                        }).eq("id", scene_row["id"]).execute()
                    except Exception as _db_err:
                        logger.error(
                            "[video] %s sahne %s video_scenes error_detail yazılamadı: %s",
                            job_id, scene_row["scene_index"], _db_err,
                        )
                    _set_status(job_id, "failed", {
                        "error_code": "tts_generation_failed",
                        "error_message": (
                            f"Sahne {scene_row['scene_index'] + 1} için seslendirme üretilemedi: "
                            f"{str(e)[:200]}"
                        ),
                        "cost_tts_chars": total_tts_chars,
                    })
                    _tts_hard_fail = True
                    break

            if _tts_hard_fail:
                return  # TTS hard fail — durum zaten ayarlandı, yeniden deneme yok

            # Cost tracking
            tts_cost_usd = round((total_tts_chars / 1_000_000) * 15.00, 6)
            sb.table("video_jobs").update({
                "storyboard": storyboard,
                "cost_tts_chars": total_tts_chars,
                "cost_tts_usd": tts_cost_usd,
            }).eq("id", job_id).execute()

            # ── Süre doğrulaması (döngü kontrolü) ────────────────────────────
            if payload.requested_duration_seconds:
                tts_total_sec = sum(
                    s.get("duration_seconds") or 0 for s in storyboard.get("scenes", [])
                )
                req = payload.requested_duration_seconds
                post_tolerance = _dur_tolerance_sec
                lo = req - post_tolerance
                hi = req + post_tolerance
                if tts_total_sec > 0 and not (lo <= tts_total_sec <= hi):
                    deviation = tts_total_sec - req
                    pct = abs(deviation / req) * 100
                    ratio = req / tts_total_sec if tts_total_sec > 0 else 1.0
                    # Sönümlü düzeltme: tam orantılı (ratio) yerine %60'ı uygulanır —
                    # aksi halde sistem hedefin üstünden altına salınıyordu (105s→38.6s
                    # ölçüldü). Taban "mevcut" = bu turu üretmek için kullanılan bütçe
                    # (_dur_corrected_sec), sabit req değil — iteratif olarak yakınsar.
                    _damped_corrected = _dur_corrected_sec * (1 + (ratio - 1) * 0.6)
                    _damped_corrected = max(
                        min(_damped_corrected, float(req) * 1.5), float(req) * 0.5
                    )
                    actual_syllables = sum(
                        _syllable_count(s.get("voice_text") or "")
                        for s in storyboard.get("scenes", [])
                    )
                    gercek_sps = actual_syllables / tts_total_sec if tts_total_sec > 0 else 0.0
                    logger.warning(
                        "[duration-loop] job=%s tur=%d ölçülen=%.1fs hedef=%ds ratio=%.3f "
                        "sönümlü_hedef=%.1fs gerçek_sps=%.2f",
                        job_id[:8], _dur_turn, tts_total_sec, req, ratio,
                        _damped_corrected, gercek_sps,
                    )
                    if _dur_turn < 2:
                        direction = "kısalt" if deviation > 0 else "uzat"
                        _dur_correction_hint = (
                            f"ÖNEMLİ DÜZELTME: Önceki storyboard ölçülen süre {tts_total_sec:.1f}s, "
                            f"hedef {req:.0f}s. voice_text içeriklerini %{pct:.0f} oranında {direction}. "
                            f"Sahne başına {'20-25' if deviation > 0 else '28-35'} hece kullan."
                        )
                        _dur_corrected_sec = _damped_corrected
                        continue  # storyboard yeniden üret
                    else:
                        _set_status(job_id, "failed", {
                            "error_code": "duration_validation_failed",
                            "error_message": (
                                f"{req:.0f} saniye istendi ancak 2 turdan sonra "
                                f"hâlâ {tts_total_sec:.1f}s üretiliyor "
                                f"(izin verilen aralık {lo:.0f}–{hi:.0f}s)."
                            ),
                        })
                        return

            break  # tolerans içinde veya süre kısıtı yok — döngüden çık

        # Remotion tarafındaki hard-fail kapısı (_toleranceCheck, server/index.ts)
        # bu iki alanı storyboard üzerinden okur — Python'daki tek kaynaktan besleniyor.
        # Alanlar yoksa (requested_duration_seconds boş) Remotion kapısı no-op kalır,
        # tıpkı bu döngünün de atlanması gibi (bilinçli, süre kısıtı olmayan içerikler için).
        if payload.requested_duration_seconds:
            storyboard["requested_duration_seconds"] = payload.requested_duration_seconds
            storyboard["duration_tolerance_seconds"] = _dur_tolerance_sec

        # ── 3. Pre-render ses kapısı (v2 §6.2) ────────────────
        audio_errors = check_audio_urls(storyboard)
        if audio_errors:
            logger.error(
                f"[video] {job_id[:8]} pre_render_audio_gate failed: {audio_errors[:3]} "
                f"render_started=false"
            )
            _set_status(job_id, "failed", {
                "error_code": "silent_audio",
                "error_message": "Render başlatılmadı — ses dosyası eksik veya erişilemiyor: "
                    + audio_errors[0],
            })
            return

        # ── 3b. duration_source kapısı — yalnızca ffprobe ölçümlü sahneler ──
        unmeasured = [
            i for i, s in enumerate(storyboard.get("scenes", []))
            if s.get("duration_source") != "ffprobe"
        ]
        if unmeasured:
            logger.error(
                f"[video] {job_id[:8]} duration_source_gate: "
                f"{len(unmeasured)} sahne ffprobe ile ölçülmemiş, render bloklandı: {unmeasured}"
            )
            _set_status(job_id, "failed", {
                "error_code": "failed_audio_validation",
                "error_message": (
                    f"{len(unmeasured)} sahnenin ses süresi ffprobe ile ölçülemedi. "
                    "Render başlatılmadı."
                ),
                "admin_detail": {"unmeasured_scene_indexes": unmeasured},
            })
            return

        # ── 3c. Altyazı kapısı (M3) — 9:16 formatlarda caption zorunlu ────
        # CaptionOverlay 9:16'da render'a girer; caption'sız 9:16 render
        # sessizce devam etmiyor — hard fail.
        if storyboard.get("format") == "9:16":
            missing_captions = [
                s.get("id", i)
                for i, s in enumerate(storyboard.get("scenes", []))
                if (s.get("voice_text") or "").strip() and not s.get("captions")
            ]
            if missing_captions:
                logger.error(
                    f"[caption] {job_id[:8]} caption_gate: "
                    f"{len(missing_captions)} sahnede altyazı yok, render bloklandı: {missing_captions}"
                )
                _set_status(job_id, "failed", {
                    "error_code": "caption_validation_failed",
                    "error_message": (
                        f"{len(missing_captions)} sahne için altyazı üretilemedi "
                        "(9:16 formatta zorunlu). Render başlatılmadı."
                    ),
                    "admin_detail": {"missing_caption_scene_ids": missing_captions},
                })
                return

        # ── 4. Remotion render ─────────────────────────────────
        _run_remotion_render(job_id, storyboard)

    except Exception as e:
        logger.exception(f"[video] {job_id} pipeline hatası")
        _set_status(job_id, "failed", {"error_message": str(e)[:500]})


# ── Watchdog ──────────────────────────────────────────────────

def _watchdog_sweep(sb=None) -> None:
    """
    Aktif işleri kontrol et; WATCHDOG_MINUTES+ süre ilerleme yoksa failed yap.
    Lazy (GET /jobs'ta) ve scheduled (lifespan) olarak çağrılabilir.
    """
    from datetime import datetime, timezone, timedelta
    if sb is None:
        sb = get_supabase_client()
    cutoff = (datetime.now(timezone.utc) - timedelta(minutes=_WATCHDOG_MINUTES)).isoformat()
    stuck = sb.table("video_jobs").select("id, status, updated_at").in_(
        "status", ["rendering", "tts_generating", "scripting", "warmup_pinging", "pending"]
    ).lt("updated_at", cutoff).execute()
    for j in (stuck.data or []):
        status = j["status"]
        logger.warning(f"[video] watchdog: {j['id'][:8]} {status} → failed")
        if status == "rendering":
            detail = "Remotion Lambda render callback'i gelmedi — Lambda loglarını (CloudWatch) ve Railway Remotion Bridge loglarını kontrol edin."
        elif status == "tts_generating":
            detail = "OpenAI TTS yanıt vermedi — API zaman aşımı veya ağ kopması."
        elif status == "warmup_pinging":
            detail = "Render servisi warm-up'ta yanıt vermedi — Railway App Sleeping kapalı değil veya servis down."
        elif status == "scripting":
            detail = "Senaryo üretimi zaman aşımı — OpenAI API yanıt vermedi veya semaphore doldu."
        else:
            detail = f"'{status}' aşamasında zaman aşımı — sessiz hata olmuş olabilir."
        sb.table("video_jobs").update({
            "status": "failed",
            "error_message": (
                f"Watchdog: {_WATCHDOG_MINUTES} dk boyunca '{status}' durumunda kaldı. "
                f"{detail}"
            ),
        }).eq("id", j["id"]).execute()


# ── Startup recovery ─────────────────────────────────────────

def recover_pending_jobs():
    """
    Uygulama başlatıldığında çağrılır.
    Railway restart'ında 'pending' kalmış işleri yeniden kuyruğa alır.
    """
    try:
        sb = get_supabase_client()
        # Önce takılı olanları temizle
        _watchdog_sweep(sb)
        # Hâlâ pending kalan işler (yeni oluşturulan) — payload_json ile yeniden başlat
        pending = sb.table("video_jobs").select("*").eq("status", "pending").execute().data or []
        if not pending:
            return
        logger.info(f"[video] startup recovery: {len(pending)} pending iş bulundu")
        import threading
        for job in pending:
            raw = job.get("payload_json") or {}
            if not raw:
                logger.warning(f"[video] {job['id'][:8]} payload_json yok — atlanıyor")
                continue
            questions_raw = None
            if raw.get("questions"):
                questions_raw = [
                    QuizQuestion(
                        text=q["text"],
                        options=[QuizOption(**o) for o in q["options"]],
                        correct_label=q["correct_label"],
                        explanation=q.get("explanation"),
                    )
                    for q in raw["questions"]
                ]
            rebuilt = CreateVideoPayload(
                type=raw.get("type", job["type"]),
                title=raw.get("title", job["title"]),
                lesson_name=raw.get("lesson_name", job.get("lesson_name")),
                topic=raw.get("topic", job.get("topic")),
                description=raw.get("description"),
                format=raw.get("format", job.get("format", "16:9")),
                target_duration_minutes=raw.get("target_duration_minutes", job.get("target_duration_minutes")),
                questions=questions_raw,
                # M8: content_track artık zorunlu (Literal) — bu recovery yolu
                # eski (bu alan zorunlu olmadan önce oluşturulmuş) job'ları da
                # yeniden kurabilmeli; payload_json'da yoksa 'ogrenci' varsayımı
                # burada BİLİNÇLİ bir geriye-dönük-uyumluluk fallback'i, yeni
                # job oluşturmadaki sessiz varsayılanla karıştırılmamalı.
                content_track=raw.get("content_track") or "ogrenci",
            )
            t = threading.Thread(target=_run_pipeline, args=(job["id"], rebuilt), daemon=True)
            t.start()
            logger.info(f"[video] {job['id'][:8]} recovery thread başlatıldı")
    except Exception as e:
        logger.error(f"[video] startup recovery hatası: {e}")


# ── Endpoint'ler ──────────────────────────────────────────────

def _idempotency_key(payload: "CreateVideoPayload") -> str:
    """
    content_type + topic + title + duration → hash.
    Aynı anahtarlı iş warmup_pinging/rendering durumundaysa job_already_running döner.
    """
    import hashlib, json
    data = json.dumps({
        "type": payload.type,
        "title": (payload.title or "").lower().strip(),
        "topic": (payload.topic or "").lower().strip(),
        "duration": payload.requested_duration_seconds,
    }, sort_keys=True)
    return hashlib.sha256(data.encode()).hexdigest()[:32]


@router.post("/create")
def create_video_job(payload: CreateVideoPayload, background_tasks: BackgroundTasks):
    sb = get_supabase_client()
    job_id = str(uuid.uuid4())

    # ── Idempotency check: aynı iş zaten çalışıyor mu? ───────────
    idem_key = _idempotency_key(payload)
    existing = sb.table("video_jobs").select("id,status").eq(
        "idempotency_key", idem_key
    ).in_("status", ["pending", "scripting", "tts_generating", "rendering", "warmup_pinging"]).execute()
    if existing.data:
        running = existing.data[0]
        logger.warning(f"[video] job_already_running idem_key={idem_key[:12]} existing={running['id'][:8]}")
        raise HTTPException(
            status_code=409,
            detail={
                "error_code": "job_already_running",
                "message": "Bu iş zaten kuyrukta.",
                "existing_job_id": running["id"],
            }
        )

    # Soru çözüm: soru listesi olmadan job oluşturmayı engelle
    from app.domain.content_type import normalize_content_type as _nct
    try:
        _ct = _nct(payload.type)
    except Exception:
        _ct = payload.type
    if _ct == "soru_cozum" and not payload.questions:
        raise HTTPException(
            status_code=422,
            detail={
                "error_code": "missing_questions",
                "message": (
                    "Soru çözüm videosu için en az 1 soru gerekli. "
                    "Panel'de soruları ekleyin veya İçerik Otomasyonu'ndan soru seçin."
                ),
            },
        )

    try:
        payload_json = payload.model_dump(mode="json")
    except Exception as e:
        logger.error(f"[video] payload serialize hatası: {e}", exc_info=True)
        raise HTTPException(status_code=422, detail=f"Payload hatası: {e}")

    try:
        # M8: content_track artık Pydantic seviyesinde zorunlu (Literal) —
        # buraya ulaştıysa geçerli "ogrenci"/"danisan" değeri garanti.
        r = sb.table("video_jobs").insert({
            "id": job_id,
            "type": payload.type,
            "title": payload.title,
            "lesson_name": payload.lesson_name,
            "topic": payload.topic,
            "format": payload.format,
            "target_duration_minutes": payload.target_duration_minutes,
            "status": "pending",
            "payload_json": payload_json,
            "idempotency_key": idem_key,
            "content_track": payload.content_track,
        }).execute()
    except Exception as e:
        logger.error(f"[video] DB insert hatası: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Veritabanı hatası: {str(e)[:200]}")

    if not r.data:
        logger.error(f"[video] DB insert boş döndü job_id={job_id}")
        raise HTTPException(status_code=500, detail="Video görevi oluşturulamadı — DB boş yanıt")

    job = r.data[0]
    background_tasks.add_task(_run_pipeline, job_id, payload)
    logger.info(f"[video] görev oluşturuldu: {job_id} tip={payload.type} idem={idem_key[:12]}")
    return job


_LIST_FIELDS = (
    "id,type,status,title,format,video_url,error_message,"
    "created_at,updated_at,cost_tts_chars,cost_tts_usd"
)

@router.get("/jobs")
def list_jobs(type: Optional[str] = None):
    sb = get_supabase_client()
    q = sb.table("video_jobs").select(_LIST_FIELDS).order("created_at", desc=True).limit(50)
    if type:
        q = q.eq("type", type)
    return q.execute().data or []


@router.get("/jobs/{job_id}")
def get_job(job_id: str):
    sb = get_supabase_client()
    job = _get_job(job_id)
    scenes = (
        sb.table("video_scenes").select("*")
        .eq("job_id", job_id).order("scene_index")
        .execute().data or []
    )
    job["scenes"] = scenes
    return job


def _bridge_to_content_automation(job: dict) -> None:
    """Video job onaylanınca generated_contents'a köprü kaydı ekle — İçerik Otomasyonu'nda görünsün."""
    job_id = job.get("id", "")
    sentinel = f"video_job:{job_id}"
    sb = get_supabase_client()
    existing = sb.table("generated_contents").select("id", count="exact").eq("topic", sentinel).execute()
    if (existing.count or 0) > 0:
        return
    content_type = job.get("type") or "video"
    title = job.get("title") or content_type.replace("_", " ").capitalize()
    row: dict = {
        "topic": sentinel,
        "type": content_type,
        "title": title,
        "status": "approved",
        "generated_by": "ai",
    }
    if job.get("video_url"):
        row["video_url"] = job["video_url"]
    try:
        sb.table("generated_contents").insert(row).execute()
        logger.info(f"[video] approve bridge: job={job_id[:8]} → generated_contents")
    except Exception as e:
        logger.warning(f"[video] approve bridge hatası job={job_id[:8]}: {e}")


@router.post("/jobs/{job_id}/approve")
def approve_job(job_id: str):
    job = _get_job(job_id)
    _set_status(job_id, "approved")
    _bridge_to_content_automation(job)
    return {"message": "Video onaylandı"}


@router.post("/jobs/{job_id}/reject")
def reject_job(job_id: str, body: RejectBody = RejectBody()):
    _get_job(job_id)
    _set_status(job_id, "rejected", {
        "error_message": body.reason or "Kullanıcı tarafından reddedildi"
    })
    return {"message": "Video reddedildi"}


def _rebuild_payload_from_job(job: dict) -> "CreateVideoPayload":
    """
    payload_json'dan (öncelikli) veya job satırından CreateVideoPayload yeniden kurar.
    Tek kaynak: hem manuel /regenerate hem render-sonrası süre kapalı döngüsü
    (render_callback) bu fonksiyonu kullanır — requested_duration_seconds ve
    duration_tolerance_seconds dahil TÜM alanlar korunur.
    """
    raw = job.get("payload_json") or {}
    if raw:
        questions_raw = None
        if raw.get("questions"):
            questions_raw = [
                QuizQuestion(
                    text=q["text"],
                    options=[QuizOption(**o) for o in q["options"]],
                    correct_label=q["correct_label"],
                    explanation=q.get("explanation"),
                )
                for q in raw["questions"]
            ]
        return CreateVideoPayload(
            type=raw.get("type", job.get("type")),
            title=raw.get("title", job.get("title")),
            lesson_name=raw.get("lesson_name", job.get("lesson_name")),
            topic=raw.get("topic", job.get("topic")),
            description=raw.get("description"),
            format=raw.get("format", job.get("format", "16:9")),
            target_duration_minutes=raw.get("target_duration_minutes", job.get("target_duration_minutes")),
            questions=questions_raw,
            requested_duration_seconds=raw.get("requested_duration_seconds"),
            duration_tolerance_seconds=raw.get("duration_tolerance_seconds") or 15,
            content_series=raw.get("content_series"),
            # M8: eski job'larda (zorunlu olmadan önce) content_track boş
            # olabilir — geriye dönük uyumluluk fallback'i (bkz. recovery yolu notu).
            content_track=raw.get("content_track") or "ogrenci",
            infographic_template=raw.get("infographic_template"),
            pre_storyboard=raw.get("pre_storyboard"),
        )
    # Fallback: storyboard'dan soruları çıkar (payload_json yoksa — eski işler)
    storyboard = job.get("storyboard") or {}
    questions_raw = []
    for scene in storyboard.get("scenes", []):
        if scene.get("component") == "QuestionScene":
            questions_raw.append(QuizQuestion(
                text=scene.get("question_text", ""),
                options=[QuizOption(**o) for o in scene.get("options", [])],
                correct_label=scene.get("correct_label", "A"),
            ))
    return CreateVideoPayload(
        type=job["type"], title=job["title"],
        lesson_name=job.get("lesson_name"), topic=job.get("topic"),
        format=job.get("format", "16:9"),
        target_duration_minutes=job.get("target_duration_minutes"),
        questions=questions_raw or None,
        requested_duration_seconds=job.get("requested_duration_seconds"),
        duration_tolerance_seconds=job.get("duration_tolerance_seconds") or 15,
        content_track=job.get("content_track") or "ogrenci",
    )


@router.post("/jobs/{job_id}/regenerate")
def regenerate_job(job_id: str, background_tasks: BackgroundTasks):
    job = _get_job(job_id)
    sb = get_supabase_client()
    sb.table("video_scenes").delete().eq("job_id", job_id).execute()
    _set_status(job_id, "pending", {"storyboard": None, "video_url": None, "error_message": None})

    rebuilt = _rebuild_payload_from_job(job)
    background_tasks.add_task(_run_pipeline, job_id, rebuilt)
    return {"message": "Yeniden üretim başlatıldı", "job_id": job_id}


@router.post("/scenes/{scene_id}/regenerate")
def regenerate_scene(scene_id: str, background_tasks: BackgroundTasks):
    sb = get_supabase_client()
    r = sb.table("video_scenes").select("*").eq("id", scene_id).execute()
    if not r.data:
        raise HTTPException(404, "Sahne bulunamadı")
    scene = r.data[0]

    def _regen(scene_id: str, voice_text: str, job_id: str, scene_index: int):
        try:
            if not voice_text.strip():
                return
            audio_bytes, _ = _tts_bytes(voice_text)
            filename = f"{job_id}_{scene_index}_r{uuid.uuid4().hex[:6]}.mp3"
            tts_url = _upload_tts(audio_bytes, filename)
            audio_duration, ffprobe_err = _ffprobe_duration(audio_bytes)
            if audio_duration is not None:
                get_supabase_client().table("video_scenes").update({
                    "tts_url": tts_url,
                    "audio_duration_seconds": audio_duration,
                    "duration_seconds": audio_duration,
                    "duration_source": "ffprobe",
                    "status": "tts_done",
                }).eq("id", scene_id).execute()
                logger.info(f"[video] sahne {scene_id} yeniden üretildi (ffprobe={audio_duration:.2f}s)")
            else:
                get_supabase_client().table("video_scenes").update({
                    "tts_url": tts_url,
                    "duration_source": "missing",
                    "measurement_error": ffprobe_err or "ffprobe başarısız",
                    "status": "tts_failed",
                    "error_code": "failed_audio_validation",
                }).eq("id", scene_id).execute()
                logger.error(
                    f"[video] sahne {scene_id} yeniden üretim: ffprobe başarısız — {ffprobe_err}"
                )
        except Exception as e:
            logger.error(f"[video] sahne {scene_id} yeniden üretim hatası: {e}")
            get_supabase_client().table("video_scenes").update(
                {"status": "failed"}
            ).eq("id", scene_id).execute()

    background_tasks.add_task(
        _regen, scene_id,
        scene.get("voice_text") or "", scene["job_id"], scene["scene_index"]
    )
    return {"message": "Sahne yeniden üretiliyor", "scene_id": scene_id}


# ── İnfografik üretim (GÖREV 4) ──────────────────────────────

class GenerateInfographicPayload(BaseModel):
    topic: str
    template: str = "card_grid"   # card_grid | comparison | process
    card_count: int = 6
    step_count: int = 5
    format: str = "9:16"

@router.post("/generate-infographic")
def generate_infographic(payload: GenerateInfographicPayload):
    from app.modules.content.infographic_generator import generate_infographic_storyboard
    try:
        storyboard = generate_infographic_storyboard(
            topic=payload.topic,
            template=payload.template,
            card_count=payload.card_count,
            step_count=payload.step_count,
            format=payload.format,
        )
        return {"ok": True, "storyboard": storyboard}
    except Exception as e:
        logger.error(f"[video] infografik üretim hatası: {e}")
        raise HTTPException(500, f"İnfografik üretilemedi: {str(e)[:300]}")


# ── Motivasyon video üretim (GÖREV 5) ────────────────────────

class GenerateMotivationPayload(BaseModel):
    topic: str
    duration_seconds: int = 120
    platform: str = "reels"
    format: str = "9:16"

@router.post("/generate-motivation")
def generate_motivation(payload: GenerateMotivationPayload):
    from app.modules.content.motivation_generator import generate_motivation_storyboard
    try:
        result = generate_motivation_storyboard(
            topic=payload.topic,
            duration=payload.duration_seconds,
            platform=payload.platform,
        )
        brand = _get_brand()
        scenes = []
        for i, scene in enumerate(result.get("scenes", []), 1):
            s = dict(scene)
            s["id"] = i
            if not s.get("component"):
                s["component"] = "MotivationScene"
            if not s.get("voice_text"):
                s["voice_text"] = s.get("narration") or s.get("spoken_text") or ""
            scenes.append(s)
        storyboard = {
            "video_type": "motivation",
            "title": result.get("title", payload.topic),
            "format": payload.format,
            "language": "tr",
            "brand": brand,
            "scenes": scenes,
        }
        return {
            "ok": True,
            "storyboard": storyboard,
            "metadata": {
                "title": result.get("title"),
                "description": result.get("description"),
                "hashtags": result.get("hashtags", []),
            },
        }
    except Exception as e:
        logger.error(f"[video] motivasyon üretim hatası: {e}")
        raise HTTPException(500, f"Motivasyon içeriği üretilemedi: {str(e)[:300]}")


# ── Render callback ───────────────────────────────────────────

_MAX_POSTRENDER_DURATION_TURNS = 2  # render-sonrası süre kapalı döngüsü — en fazla 2 yeniden üretim


@public_router.post("/render-callback")
def render_callback(body: RenderCallback, background_tasks: BackgroundTasks):
    """
    Remotion render servisi tamamlandığında çağırır.

    P0-5: 'done' kazanılan statüdür — postcheck geçmeden verilmez.
    P0-7: maliyet DB'ye yazılır, 0 yazan log artık oluşmaz.
    """
    sb_cb = get_supabase_client()

    # ── Render başarısız ─────────────────────────────────────────
    if body.status != "done":
        _set_status(body.job_id, "failed", {
            "error_message": body.error or "Render başarısız",
            "render_id": body.render_id,
        })
        logger.error(f"[video] {body.job_id[:8]} render_failed: {body.error}")
        return {"ok": True}

    # ── Maliyet kaydı (P0-7 / M6) ─────────────────────────────────
    cost_usd = body.cost_lambda_usd
    if cost_usd is not None and cost_usd > 0:
        try:
            sb_cb.table("video_jobs").update({
                "cost_lambda_usd": cost_usd,
            }).eq("id", body.job_id).execute()
            logger.info(
                f"[video] {body.job_id[:8]} cost_lambda_usd=${cost_usd:.4f} "
                f"elapsed={body.elapsed_seconds}s render_id={body.render_id}"
            )
        except Exception as cost_exc:
            logger.warning(f"[video] {body.job_id[:8]} maliyet yazılamadı: {cost_exc}")
    elif cost_usd is None:
        # Bridge costs.accruedSoFar'ı hiç okuyamadı (M6: cost_tracking_broken) —
        # sadece loglamak yetmez, kalite raporunda görünür olmalı.
        logger.warning(
            f"[video] {body.job_id[:8]} cost_lambda_usd=null — cost_tracking_broken "
            "(bridge maliyet bilgisi okuyamadı)"
        )
        try:
            existing = sb_cb.table("video_jobs").select("admin_detail").eq("id", body.job_id).execute()
            prior_admin_detail = (existing.data or [{}])[0].get("admin_detail") or {}
            sb_cb.table("video_jobs").update({
                "admin_detail": {**prior_admin_detail, "cost_tracking_broken": True},
            }).eq("id", body.job_id).execute()
        except Exception as admin_exc:
            logger.warning(f"[video] {body.job_id[:8]} cost_tracking_broken admin_detail yazılamadı: {admin_exc}")
    # cost_usd == 0 → $0 yazmak yerine null bırak (ölçülemeyen değeri maskeleme)

    # ── Postcheck (P0-5) — 'done' kazanılır, varsayılan değil ────
    try:
        job_row = sb_cb.table("video_jobs").select(
            "payload_json, admin_detail, type, title, lesson_name, topic, "
            "format, target_duration_minutes, storyboard"
        ).eq("id", body.job_id).execute().data
        job_full = job_row[0] if job_row else {}
        pj = job_full.get("payload_json") or {}
        req_sec = pj.get("requested_duration_seconds")
        tol_sec = float(pj.get("duration_tolerance_seconds") or 15.0)
    except Exception:
        job_full = {}
        pj = {}
        req_sec = None
        tol_sec = 15.0

    report = run_postcheck(
        video_url=body.video_url or "",
        requested_seconds=req_sec,
        tolerance_seconds=tol_sec,
    )
    logger.info(
        f"[video] {body.job_id[:8]} postcheck "
        f"passed={report['all_passed']} "
        f"url_ok={report['url_accessible']} "
        f"size={report['file_size_bytes']} "
        f"vol={report.get('audio_volume_db')} "
        f"failure={report.get('first_failure_code')}"
    )

    try:
        sb_cb.table("video_jobs").update({
            "postcheck_report": report,
        }).eq("id", body.job_id).execute()
    except Exception as pc_exc:
        logger.warning(f"[video] {body.job_id[:8]} postcheck raporu yazılamadı: {pc_exc}")

    if not report["all_passed"]:
        # ── Render-sonrası süre kapalı döngüsü ────────────────────────────
        # Postcheck'in ffprobe ile ölçtüğü GERÇEK süre, pre-render TTS toplamından
        # sapmış olabilir (bkz. P1 doğrulama: job d9907932, tts-toplamı toleransı
        # geçmişti ama render 109.2s çıktı). Bu durumda storyboard'u ölçülen
        # gerçek sapmayla yeniden ürettirip en fazla _MAX_POSTRENDER_DURATION_TURNS
        # kez yeniden render dene — hemen failed yazıp durma.
        dur_check = report.get("duration_check") or {}
        if (
            report["first_failure_code"] == "duration_validation_failed"
            and dur_check.get("actual_seconds")
            and req_sec
        ):
            admin_detail = job_full.get("admin_detail") or {}
            turn = int(admin_detail.get("duration_postrender_turn", 0))
            if turn < _MAX_POSTRENDER_DURATION_TURNS:
                actual = float(dur_check["actual_seconds"])
                deviation = actual - req_sec
                pct = abs(deviation / req_sec) * 100
                ratio = req_sec / actual if actual else 1.0
                # Sönümlü düzeltme (bkz. pre-render döngüsündeki aynı formül) —
                # "mevcut" bu render'ı üretmek için kullanılan bütçe; ilk post-render
                # turunda henüz kayıtlı değilse ilk render req ile üretildiği için
                # req_sec varsayılır.
                mevcut = float(admin_detail.get("last_budget_seconds") or req_sec)
                corrected_sec = mevcut * (1 + (ratio - 1) * 0.6)
                corrected_sec = max(min(corrected_sec, req_sec * 1.5), req_sec * 0.5)

                rendered_scenes = (job_full.get("storyboard") or {}).get("scenes", [])
                actual_syllables = sum(
                    _syllable_count(s.get("voice_text") or "") for s in rendered_scenes
                )
                gercek_sps = actual_syllables / actual if actual else 0.0

                direction = "kısalt" if deviation > 0 else "uzat"
                hint = (
                    f"ÖNEMLİ DÜZELTME: Render edilmiş videonun ffprobe ile ölçülen gerçek "
                    f"süresi {actual:.1f}s, hedef {req_sec:.0f}s. voice_text içeriklerini "
                    f"%{pct:.0f} oranında {direction}. Sahne başına "
                    f"{'20-25' if deviation > 0 else '28-35'} hece kullan."
                )
                next_turn = turn + 1
                logger.warning(
                    "[duration-loop] job=%s tur=%d/%d render_sonrasi=true ölçülen=%.1fs "
                    "hedef=%.0fs ratio=%.3f sönümlü_hedef=%.1fs gerçek_sps=%.2f",
                    body.job_id[:8], next_turn, _MAX_POSTRENDER_DURATION_TURNS,
                    actual, req_sec, ratio, corrected_sec, gercek_sps,
                )
                sb_cb.table("video_jobs").update({
                    "admin_detail": {
                        **admin_detail,
                        "duration_postrender_turn": next_turn,
                        "last_budget_seconds": corrected_sec,
                    },
                }).eq("id", body.job_id).execute()
                sb_cb.table("video_scenes").delete().eq("job_id", body.job_id).execute()
                _set_status(body.job_id, "pending", {
                    "video_url": None, "postcheck_report": report, "error_message": None,
                })
                rebuilt = _rebuild_payload_from_job({**job_full, "id": body.job_id})
                # _seed_turn=2: storyboard'u bu düzeltmeyle bir kez yeniden üret,
                # TTS ölçümü de toleransı geçerse render'a devam et; geçmezse
                # (turn 2'de yeniden deneme hakkı olmadığından) hemen hard-fail —
                # ikinci bir gereksiz Lambda render'ı denenmez.
                background_tasks.add_task(
                    _run_pipeline, body.job_id, rebuilt, corrected_sec, hint, 2,
                )
                logger.info(
                    "[duration-loop] job=%s tur=%d yeniden üretim + render tetiklendi",
                    body.job_id[:8], next_turn,
                )
                return {"ok": True}
            else:
                logger.error(
                    "[duration-loop] job=%s tur hakkı tükendi (%d/%d) — "
                    "duration_validation_failed ile durduruluyor",
                    body.job_id[:8], turn, _MAX_POSTRENDER_DURATION_TURNS,
                )

        _set_status(body.job_id, "failed", {
            "error_code": report["first_failure_code"],
            "error_message": report["first_failure_message"],
            "video_url": body.video_url,   # video var, incelenebilir
            "render_id": body.render_id,
        })
        logger.error(
            f"[video] {body.job_id[:8]} postcheck_failed "
            f"code={report['first_failure_code']} msg={report['first_failure_message']}"
        )
        return {"ok": True}

    # Tüm kontroller geçti → 'done' hak edildi
    actual_dur = (report.get("duration_check") or {}).get("actual_seconds")
    _set_status(body.job_id, "ready_for_review", {
        "video_url": body.video_url,
        "actual_duration_seconds": actual_dur,
        "render_id": body.render_id,
    })
    logger.info(
        f"[video] {body.job_id[:8]} postcheck_passed → ready_for_review "
        f"url={body.video_url} dur={actual_dur}"
    )
    return {"ok": True}


# ── Render health / devre kesici ──────────────────────────────

@router.get("/render-health")
def render_health():
    """Remotion devre kesici durumunu döndür."""
    with _remotion_lock:
        failures = _remotion_consecutive_failures
    remotion_url = settings.REMOTION_URL
    return {
        "circuit_open": failures >= _CIRCUIT_OPEN_THRESHOLD,
        "consecutive_failures": failures,
        "threshold": _CIRCUIT_OPEN_THRESHOLD,
        "remotion_url_configured": bool(remotion_url),
        "railway_config_tips": [
            "App Sleeping'i kapat: Railway → Service → Settings → Sleep Policy → Never Sleep",
            "Restart policy 'on-failure' yap: Settings → Deploy → Restart Policy → On Failure",
            "Health check: /health endpoint tanımla",
            "RAM: Remotion render yoğundur, en az 512MB-1GB öner",
        ],
    }


@router.post("/render-health/reset")
def render_health_reset():
    """Devre kesiciyi manuel sıfırla (servis düzeldikten sonra)."""
    global _remotion_consecutive_failures
    with _remotion_lock:
        old = _remotion_consecutive_failures
        _remotion_consecutive_failures = 0
    logger.info(f"[video] devre kesici sıfırlandı (eski değer: {old})")
    return {"ok": True, "reset_from": old}


# ── Section 13: Storyboard önizleme (TTS ve render yok) ──────

class PreviewPayload(BaseModel):
    type: str
    title: str
    lesson_name: Optional[str] = None
    topic: Optional[str] = None
    description: Optional[str] = None
    format: str = "9:16"
    target_duration_minutes: Optional[int] = 12
    questions: Optional[List[QuizQuestion]] = None
    content_series: Optional[str] = None

@router.post("/preview")
def preview_storyboard(payload: PreviewPayload):
    """
    TTS ve Remotion render olmadan sadece storyboard JSON üretir.
    Kullanıcı sahneleri gözden geçirip onayladıktan sonra /create ile tam pipeline başlatılabilir.
    """
    brand = _get_brand()
    try:
        if payload.type in ("reel", "educational_reel"):
            from app.modules.sgs.educational_reel_storyboard import generate_educational_reel_storyboard
            _prev_budget = float(payload.requested_duration_seconds or 120)
            _, _, _prev_sc = _syllable_budget_params(_prev_budget)
            storyboard = generate_educational_reel_storyboard(
                title=payload.title,
                topic=payload.topic or payload.title,
                subject=payload.lesson_name or "SGS",
                content_series=payload.content_series,
                description=payload.description or "",
                brand=brand,
                budget_seconds=_prev_budget,
                scene_count=_prev_sc,
            )
        elif payload.type in ("konu_anlatimi", "lesson_long", "sgs_topic_video"):
            from app.modules.sgs.lesson_storyboard import generate_lesson_storyboard
            storyboard_raw = generate_lesson_storyboard(
                title=payload.title,
                topic=payload.topic or payload.title,
                subject=payload.lesson_name or "SGS",
                target_minutes=payload.target_duration_minutes or 20,
                description=payload.description or "",
            )
            scenes = storyboard_raw.get("scenes", [])
            for i, s in enumerate(scenes, 1):
                s["id"] = i
            storyboard = {
                "video_type": "konu_anlatimi", "title": payload.title,
                "lesson_name": payload.lesson_name, "topic": payload.topic,
                "format": payload.format, "language": "tr", "brand": brand, "scenes": scenes,
            }
        elif payload.type == "quiz" and payload.questions:
            from app.modules.sgs.storyboard import generate_sgs_question_storyboard
            questions_dict = [
                {
                    "question_text": q.text,
                    "options": [{"label": o.label, "text": o.text} for o in q.options],
                    "correct_option": q.correct_label,
                    "explanation": q.explanation or "",
                }
                for q in payload.questions
            ]
            raw = generate_sgs_question_storyboard(
                title=payload.title, topic=payload.topic or payload.title,
                subject=payload.lesson_name or "SGS", questions=questions_dict,
            )
            scenes = raw.get("scenes", [])
            for i, s in enumerate(scenes, 1):
                s["id"] = i
            storyboard = {
                "video_type": "quiz", "title": payload.title,
                "lesson_name": payload.lesson_name, "topic": payload.topic,
                "format": payload.format, "language": "tr", "brand": brand, "scenes": scenes,
            }
        else:
            raise HTTPException(400, f"'{payload.type}' tipi önizleme için desteklenmiyor.")

        # Kalite uyarıları
        warnings = check_storyboard_quality(storyboard, payload.type)

        return {
            "ok": True,
            "storyboard": storyboard,
            "scene_count": len(storyboard.get("scenes", [])),
            "quality_warnings": warnings,
            "hint": "Storyboard'u onayladıktan sonra POST /video/create ile tam pipeline başlatın.",
        }

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"[video] preview hatası: {exc}", exc_info=True)
        raise HTTPException(500, f"Önizleme üretilemedi: {str(exc)[:300]}")


# ── GÖREV 4: Cleanup altyapısı ────────────────────────────────

@router.get("/cleanup/inventory")
def cleanup_inventory():
    """Video işlerini tara, sınıflandır ve say."""
    from datetime import datetime, timezone, timedelta
    sb = get_supabase_client()
    now = datetime.now(timezone.utc)
    stuck_cutoff = (now - timedelta(hours=4)).isoformat()

    all_jobs = (
        sb.table("video_jobs")
        .select("id, status, video_url, created_at, file_size_bytes, type")
        .order("created_at", desc=True)
        .execute().data or []
    )

    active_statuses = {"scripting", "tts_generating", "warmup_pinging", "rendering", "pending"}

    counts = {
        "completed_healthy": 0,
        "completed_broken": 0,
        "failed": 0,
        "stuck": 0,
        "archived": 0,
        "total": len(all_jobs),
    }
    for job in all_jobs:
        status = job["status"]
        if status == "archived":
            counts["archived"] += 1
        elif status in ("approved", "published") and job.get("video_url"):
            counts["completed_healthy"] += 1
        elif status in ("approved", "published") and not job.get("video_url"):
            counts["completed_broken"] += 1
        elif status == "failed":
            counts["failed"] += 1
        elif status in active_statuses and job["created_at"] < stuck_cutoff:
            counts["stuck"] += 1

    return {"inventory": counts, "jobs_sample": all_jobs[:20]}


@router.post("/cleanup/dry-run")
def cleanup_dry_run():
    """
    Dry-run: silinecek/arşivlenecek işleri listele, gerçek işlem yapma.
    Onaydan önce kullanıcıya sun.
    """
    from datetime import datetime, timezone, timedelta
    sb = get_supabase_client()
    now = datetime.now(timezone.utc)
    stuck_cutoff = (now - timedelta(hours=4)).isoformat()
    old_failed_cutoff = (now - timedelta(days=7)).isoformat()

    to_archive = []  # iş kayıtları arşivlenecek (silinmiyor)
    to_delete_tts = 0  # silme tahmini (TTS dosyaları)

    # 7 günden eski failed işler → arşiv
    old_failed = (
        sb.table("video_jobs").select("id, title, status, created_at")
        .eq("status", "failed").lt("created_at", old_failed_cutoff)
        .execute().data or []
    )
    for job in old_failed:
        to_archive.append({
            "id": job["id"], "title": job.get("title", "?"),
            "reason": f"7+ gün önce başarısız", "status": job["status"],
        })
        to_delete_tts += 1

    # 4+ saat stuck işler → arşiv
    active_statuses = ["scripting", "tts_generating", "warmup_pinging", "rendering", "pending"]
    stuck_jobs = (
        sb.table("video_jobs").select("id, title, status, created_at")
        .in_("status", active_statuses).lt("updated_at", stuck_cutoff)
        .execute().data or []
    )
    for job in stuck_jobs:
        to_archive.append({
            "id": job["id"], "title": job.get("title", "?"),
            "reason": f"4+ saat takılı ({job['status']})", "status": job["status"],
        })
        to_delete_tts += 1

    return {
        "dry_run": True,
        "to_archive_count": len(to_archive),
        "estimated_tts_files_to_delete": to_delete_tts,
        "items": to_archive,
        "note": "Onaylamak için POST /video/cleanup/apply çağırın.",
    }


@router.post("/cleanup/apply")
def cleanup_apply():
    """
    Temizliği uygula: stuck/eski-failed işleri 'archived' yap,
    orta TTS dosyalarını temizle.
    """
    from datetime import datetime, timezone, timedelta
    sb = get_supabase_client()
    now = datetime.now(timezone.utc)
    stuck_cutoff = (now - timedelta(hours=4)).isoformat()
    old_failed_cutoff = (now - timedelta(days=7)).isoformat()
    archived_at = now.isoformat()
    archived_count = 0

    # Eski failed → archived
    old_failed_ids = [
        r["id"] for r in (
            sb.table("video_jobs").select("id")
            .eq("status", "failed").lt("created_at", old_failed_cutoff)
            .execute().data or []
        )
    ]
    if old_failed_ids:
        sb.table("video_jobs").update({
            "status": "archived", "archived_at": archived_at,
        }).in_("id", old_failed_ids).execute()
        archived_count += len(old_failed_ids)

    # Stuck → archived
    active_statuses = ["scripting", "tts_generating", "warmup_pinging", "rendering", "pending"]
    stuck_ids = [
        r["id"] for r in (
            sb.table("video_jobs").select("id")
            .in_("status", active_statuses).lt("updated_at", stuck_cutoff)
            .execute().data or []
        )
    ]
    if stuck_ids:
        sb.table("video_jobs").update({
            "status": "archived", "archived_at": archived_at,
            "error_message": "Otomatik temizlik: 4+ saat takılı kaldı",
        }).in_("id", stuck_ids).execute()
        archived_count += len(stuck_ids)

    logger.info(f"[video] cleanup/apply: {archived_count} iş arşivlendi")
    return {
        "archived": archived_count,
        "archived_at": archived_at,
        "message": f"{archived_count} iş arşivlendi. Onaylı/yayınlanmış içeriklere dokunulmadı.",
    }
