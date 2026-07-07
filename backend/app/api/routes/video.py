"""Video Prodüksiyon Motoru — Quiz / Ders / Shorts / Motivasyon."""
import logging
import time
import uuid
from typing import Optional, List
from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from openai import RateLimitError as OpenAIRateLimitError, APITimeoutError
from app.db.supabase import get_supabase_client
from app.core.config import settings
from app.modules.content.pronunciation_dict import apply_pronunciation_dict

logger = logging.getLogger(__name__)
router = APIRouter()
public_router = APIRouter()  # auth gerektirmeyen internal callback'ler

VIDEO_BUCKET = "video-tts"
_TTS_BACKOFF = (2, 8, 20)       # saniye — 3 deneme
_MAX_CONCURRENT = 2             # eşzamanlı pipeline sınırı
_WATCHDOG_MINUTES = 30

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
    type: str                              # quiz | lesson | shorts | motivation | infographic
    title: str
    lesson_name: Optional[str] = None
    topic: Optional[str] = None
    description: Optional[str] = None     # yönetmen notu / ek bağlam
    format: str = "16:9"
    target_duration_minutes: Optional[int] = 12
    questions: Optional[List[QuizQuestion]] = None
    pre_storyboard: Optional[dict] = None         # infografik önceden üretilmiş storyboard
    infographic_template: Optional[str] = None    # card_grid | comparison | process

class RejectBody(BaseModel):
    reason: Optional[str] = None

class RenderCallback(BaseModel):
    job_id: str
    status: str                            # done | failed
    video_url: Optional[str] = None
    error: Optional[str] = None


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
        }
    except Exception:
        return {
            "primary_color": "#0B2A4A", "secondary_color": "#C9A96E",
            "background_color": "#FAF7F0", "font_heading": "Playfair Display",
            "font_body": "Lato",
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
    OpenAI TTS — 3 deneme, exponential backoff.
    Pronunciation sözlüğü uygulanır.
    Returns: (ses_baytları, karakter_sayısı)
    Raises: RuntimeError — tüm denemeler başarısız olursa
    """
    from openai import OpenAI
    text = apply_pronunciation_dict(text)
    char_count = len(text)
    client = OpenAI(api_key=settings.OPENAI_API_KEY, timeout=60.0)

    last_err = None
    for attempt, wait in enumerate(_TTS_BACKOFF, 1):
        try:
            resp = client.audio.speech.create(
                model="tts-1-hd",
                voice="onyx",
                input=text,
                speed=0.93,
            )
            logger.info(f"[tts] deneme {attempt} başarılı — {char_count} karakter")
            return resp.content, char_count
        except OpenAIRateLimitError as e:
            last_err = e
            err_str = str(e)
            if "insufficient_quota" in err_str:
                # Kota tükendi — yeniden denemek anlamsız
                raise RuntimeError(
                    "OpenAI TTS kotası tükendi (insufficient_quota). "
                    "API limitinizi kontrol edin."
                ) from e
            logger.warning(f"[tts] 429 rate limit · deneme {attempt} · {wait}s bekleniyor")
            time.sleep(wait)
        except APITimeoutError as e:
            last_err = e
            logger.warning(f"[tts] timeout · deneme {attempt} · {wait}s bekleniyor")
            time.sleep(wait)
        except Exception as e:
            raise RuntimeError(f"[tts] OpenAI hatası: {e}") from e

    raise RuntimeError(
        f"[tts] {len(_TTS_BACKOFF)} denemeden sonra başarısız: {last_err}"
    )

def _estimate_duration(text: str) -> float:
    """Karakter sayısına göre saniye tahmini (~13 karakter/saniye Türkçe)."""
    return max(5.0, len(text) / 13.0)

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
    job_id: str, title: str, lesson_name: str, topic: str,
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

    _set_status(job_id, "rendering")
    logger.info(f"[video] {job_id[:8]} Remotion render tetikleniyor")
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

def _run_pipeline(job_id: str, payload: CreateVideoPayload):
    """
    Storyboard → TTS → Remotion render pipeline'ı.
    Eşzamanlı çalışma _pipeline_semaphore ile sınırlandırılır.
    """
    acquired = _pipeline_semaphore.acquire(timeout=600)
    if not acquired:
        logger.error(f"[video] {job_id} semaphore alınamadı — başka pipeline dolup taştı")
        _set_status(job_id, "failed", {
            "error_message": "Sistem meşgul. Lütfen birkaç dakika sonra yeniden deneyin."
        })
        return

    try:
        _run_pipeline_inner(job_id, payload)
    finally:
        _pipeline_semaphore.release()


def _run_pipeline_inner(job_id: str, payload: CreateVideoPayload):
    """Gerçek pipeline mantığı — semaphore altında çalışır."""
    import httpx
    sb = get_supabase_client()
    brand = _get_brand()
    total_tts_chars = 0

    try:
        # ── 0. İnfografik (TTS yok, Remotion olmadan doğrudan hazır) ──
        if payload.type == "infographic":
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
        logger.info(f"[video] {job_id} senaryo oluşturuluyor tip={payload.type}")

        if payload.type == "quiz" and payload.questions:
            storyboard = _build_quiz_storyboard(
                job_id=job_id,
                title=payload.title,
                lesson_name=payload.lesson_name or "",
                topic=payload.topic or "",
                questions=payload.questions,
                format=payload.format,
                brand=brand,
                description=payload.description or "",
            )
        elif payload.type == "motivation":
            from app.modules.content.motivation_generator import generate_motivation_storyboard
            platform = "reels" if payload.format == "9:16" else "shorts"
            tone = payload.description or "sıcak ve samimi"
            topic_text = payload.topic or payload.title
            result = generate_motivation_storyboard(topic_text, platform, tone)
            scenes = []
            for i, scene in enumerate(result.get("scenes", []), 1):
                narration = scene.get("narration", "")
                scenes.append({
                    "id": i, "component": "MotivationScene", "duration_seconds": 15,
                    "message": narration or " ".join(scene.get("display_lines", [])),
                    "message_author": "@adimmusavir",
                    "voice_text": narration,
                })
            storyboard = {
                "video_type": "motivation",
                "title": result.get("title", payload.title),
                "format": payload.format,
                "language": "tr",
                "brand": brand,
                "scenes": scenes,
            }
        else:
            topic_text = payload.topic or payload.title
            desc_text = payload.description or ""
            intro_voice = f"Bu videoda {topic_text} konusunu ele alacağız."
            if desc_text:
                intro_voice += f" {desc_text}"

            storyboard = {
                "video_type": payload.type,
                "title": payload.title,
                "lesson_name": payload.lesson_name,
                "topic": payload.topic,
                "format": payload.format,
                "language": "tr",
                "brand": brand,
                "scenes": [
                    {
                        "id": 1, "component": "IntroScene", "duration_seconds": 8,
                        "title": payload.title,
                        "subtitle": payload.topic or "",
                        "voice_text": intro_voice,
                    },
                    {
                        "id": 2, "component": "OutroScene", "duration_seconds": 8,
                        "title": "Tamamlandı",
                        "subtitle": "Bir sonraki videoda görüşmek üzere!",
                        "voice_text": "Videoyu izlediğiniz için teşekkürler. Başarılar!",
                    },
                ],
            }

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

        # ── 2. TTS ─────────────────────────────────────────────
        _set_status(job_id, "tts_generating")
        logger.info(f"[video] {job_id} TTS başlıyor ({len(storyboard['scenes'])} sahne)")

        scenes_in_db = (
            sb.table("video_scenes")
            .select("*").eq("job_id", job_id).order("scene_index")
            .execute().data or []
        )

        for scene_row in scenes_in_db:
            voice_text = (scene_row.get("voice_text") or "").strip()
            if not voice_text:
                continue
            try:
                audio_bytes, char_count = _tts_bytes(voice_text)
                total_tts_chars += char_count
                filename = f"{job_id}_{scene_row['scene_index']}.mp3"
                tts_url = _upload_tts(audio_bytes, filename)
                duration = _estimate_duration(voice_text)

                sb.table("video_scenes").update({
                    "tts_url": tts_url,
                    "duration_seconds": duration,
                    "status": "tts_done",
                }).eq("id", scene_row["id"]).execute()

                for s in storyboard["scenes"]:
                    if s["id"] - 1 == scene_row["scene_index"]:
                        s["tts_url"] = tts_url
                        s["duration_seconds"] = duration
                        break

                logger.info(f"[video] {job_id} sahne {scene_row['scene_index']} TTS ok ({duration:.1f}s)")

            except RuntimeError as e:
                err_str = str(e)
                if "insufficient_quota" in err_str or "kotası tükendi" in err_str:
                    logger.error(f"[video] {job_id} kota hatası — pipeline durduruluyor")
                    _set_status(job_id, "failed", {
                        "error_message": (
                            "OpenAI TTS kotası tükendi. "
                            "API kota limitinizi kontrol ettikten sonra yeniden deneyin."
                        ),
                        "cost_tts_chars": total_tts_chars,
                    })
                    return
                # Diğer hatalarda sahneyi atla, devam et
                logger.error(f"[video] {job_id} sahne {scene_row['scene_index']} TTS hatası: {e}")
                sb.table("video_scenes").update({"status": "tts_failed"}).eq("id", scene_row["id"]).execute()

        # Cost tracking
        tts_cost_usd = round((total_tts_chars / 1_000_000) * 15.00, 6)
        sb.table("video_jobs").update({
            "storyboard": storyboard,
            "cost_tts_chars": total_tts_chars,
            "cost_tts_usd": tts_cost_usd,
        }).eq("id", job_id).execute()

        # ── 3. Remotion render ─────────────────────────────────
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
            detail = "Render worker geri dönüş yapmadı — büyük olasılıkla OOM (bellek baskısı). Railway RAM metriklerini ve Remotion loglarını kontrol edin."
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
            )
            t = threading.Thread(target=_run_pipeline, args=(job["id"], rebuilt), daemon=True)
            t.start()
            logger.info(f"[video] {job['id'][:8]} recovery thread başlatıldı")
    except Exception as e:
        logger.error(f"[video] startup recovery hatası: {e}")


# ── Endpoint'ler ──────────────────────────────────────────────

@router.post("/create")
def create_video_job(payload: CreateVideoPayload, background_tasks: BackgroundTasks):
    sb = get_supabase_client()
    job_id = str(uuid.uuid4())

    try:
        payload_json = payload.model_dump(mode="json")
    except Exception as e:
        logger.error(f"[video] payload serialize hatası: {e}", exc_info=True)
        raise HTTPException(status_code=422, detail=f"Payload hatası: {e}")

    try:
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
        }).execute()
    except Exception as e:
        logger.error(f"[video] DB insert hatası: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Veritabanı hatası: {str(e)[:200]}")

    if not r.data:
        logger.error(f"[video] DB insert boş döndü job_id={job_id}")
        raise HTTPException(status_code=500, detail="Video görevi oluşturulamadı — DB boş yanıt")

    job = r.data[0]
    background_tasks.add_task(_run_pipeline, job_id, payload)
    logger.info(f"[video] görev oluşturuldu: {job_id} tip={payload.type}")
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


@router.post("/jobs/{job_id}/approve")
def approve_job(job_id: str):
    _get_job(job_id)
    _set_status(job_id, "approved")
    return {"message": "Video onaylandı"}


@router.post("/jobs/{job_id}/reject")
def reject_job(job_id: str, body: RejectBody = RejectBody()):
    _get_job(job_id)
    _set_status(job_id, "rejected", {
        "error_message": body.reason or "Kullanıcı tarafından reddedildi"
    })
    return {"message": "Video reddedildi"}


@router.post("/jobs/{job_id}/regenerate")
def regenerate_job(job_id: str, background_tasks: BackgroundTasks):
    job = _get_job(job_id)
    sb = get_supabase_client()
    sb.table("video_scenes").delete().eq("job_id", job_id).execute()
    _set_status(job_id, "pending", {"storyboard": None, "video_url": None, "error_message": None})

    # payload_json öncelikli — yoksa storyboard'dan geri çıkar
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
        rebuilt = CreateVideoPayload(
            type=raw.get("type", job["type"]),
            title=raw.get("title", job["title"]),
            lesson_name=raw.get("lesson_name", job.get("lesson_name")),
            topic=raw.get("topic", job.get("topic")),
            description=raw.get("description"),
            format=raw.get("format", job.get("format", "16:9")),
            target_duration_minutes=raw.get("target_duration_minutes", job.get("target_duration_minutes")),
            questions=questions_raw,
        )
    else:
        # Fallback: storyboard'dan soruları çıkar
        storyboard = job.get("storyboard") or {}
        questions_raw = []
        for scene in storyboard.get("scenes", []):
            if scene.get("component") == "QuestionScene":
                questions_raw.append(QuizQuestion(
                    text=scene.get("question_text", ""),
                    options=[QuizOption(**o) for o in scene.get("options", [])],
                    correct_label=scene.get("correct_label", "A"),
                ))
        rebuilt = CreateVideoPayload(
            type=job["type"], title=job["title"],
            lesson_name=job.get("lesson_name"), topic=job.get("topic"),
            format=job.get("format", "16:9"),
            target_duration_minutes=job.get("target_duration_minutes"),
            questions=questions_raw or None,
        )

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
            duration = _estimate_duration(voice_text)
            get_supabase_client().table("video_scenes").update({
                "tts_url": tts_url,
                "duration_seconds": duration,
                "status": "tts_done",
            }).eq("id", scene_id).execute()
            logger.info(f"[video] sahne {scene_id} yeniden üretildi")
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
    platform: str = "reels"        # reels | shorts | carousel | post
    tone: str = "sıcak ve samimi"
    format: str = "9:16"

@router.post("/generate-motivation")
def generate_motivation(payload: GenerateMotivationPayload):
    from app.modules.content.motivation_generator import generate_motivation_storyboard
    try:
        result = generate_motivation_storyboard(
            topic=payload.topic,
            platform=payload.platform,
            tone=payload.tone,
        )
        scenes = []
        for i, scene in enumerate(result.get("scenes", []), 1):
            narration = scene.get("narration", "")
            display_lines = scene.get("display_lines", [])
            scenes.append({
                "id": i,
                "component": "MotivationScene",
                "duration_seconds": 15,
                "message": narration or " ".join(display_lines),
                "message_author": "@adimmusavir",
                "voice_text": narration,
            })
        storyboard = {
            "video_type": "motivation",
            "title": result.get("title", payload.topic),
            "format": payload.format,
            "language": "tr",
            "brand": {
                "primary_color": "#0D1B3E",
                "secondary_color": "#2B7FE0",
                "background_color": "#08121E",
                "font_heading": "Playfair Display",
                "font_body": "Lato",
            },
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

@public_router.post("/render-callback")
def render_callback(body: RenderCallback):
    """Remotion render servisi tamamlandığında çağırır."""
    if body.status == "done":
        _set_status(body.job_id, "ready_for_review", {
            "video_url": body.video_url,
            "error_message": None,
        })
        logger.info(f"[video] {body.job_id} render tamamlandı: {body.video_url}")
    else:
        _set_status(body.job_id, "failed", {
            "error_message": body.error or "Render başarısız"
        })
        logger.error(f"[video] {body.job_id} render hatası: {body.error}")
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
