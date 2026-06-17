import logging
from moviepy.editor import AudioFileClip
from app.modules.content.script_generator import (
    generate_video_script, generate_shorts_script, generate_post_content,
    generate_question_solution_script, generate_topic_explanation_script,
)
from app.modules.content.audio_generator import generate_audio
from app.modules.content.scene_engine import (
    render_intro_scene, render_content_scene, render_question_scene,
    render_answer_scene, render_exam_tip_scene, render_summary_scene,
    render_cta_scene, render_shorts_scene,
)
from app.modules.content.video_assembler import assemble_video
from app.modules.content.youtube_uploader import upload_to_youtube, make_public
from app.modules.content.instagram_poster import post_image_to_instagram, post_reel_to_instagram
from app.modules.content.storage import upload_image
from app.modules.content.gemini_image import generate_post_image_with_gemini
from app.modules.voice.tts import synthesize

logger = logging.getLogger(__name__)

_INTRO_DUR = 4.5
_CTA_DUR   = 4.0


def _audio_duration(path: str) -> float:
    c = AudioFileClip(path)
    d = c.duration
    c.close()
    return d


def _try_tts(text: str) -> str | None:
    try:
        return synthesize(text[:1200], voice="nova")
    except Exception:
        return None


def _stage(name: str, fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except Exception as e:
        raise RuntimeError(f"[{name}] {e}") from e


def _split_lines(content: str, max_per_scene: int = 5) -> list[str]:
    """Split a section body into bullet lines for scene_engine."""
    sents = [s.strip() for s in content.replace(". ", ".\n").split("\n") if s.strip()]
    if not sents:
        sents = [content.strip()]
    return sents[:max_per_scene]


# ─────────────────────────────────────────────────────────────
# Uzun Video (konu anlatım tarzı)
# ─────────────────────────────────────────────────────────────
def create_normal_video(topic: str, duration_minutes: int = 5) -> dict:
    script = _stage("script", generate_video_script, topic, duration_minutes)
    logger.info("[video] script hazır")

    full_text = " ".join(s["content"] for s in script["sections"])
    audio_path = _stage("audio", generate_audio, full_text, voice="nova")
    logger.info("[video] ses hazır")

    ad = _audio_duration(audio_path)
    sections = script["sections"]
    n_sec = max(len(sections), 1)
    sec_dur = max(3.5, (ad - _INTRO_DUR - _CTA_DUR) / n_sec)

    clips = []
    clips.append(_stage("scene-intro", render_intro_scene,
                         script["title"], script.get("description", "")[:80], _INTRO_DUR))

    for i, sec in enumerate(sections):
        lines = _split_lines(sec["content"])
        clips.append(_stage(f"scene-{i}", render_content_scene,
                             sec["title"], lines, i + 1, n_sec, sec_dur))

    clips.append(_stage("scene-cta", render_cta_scene, _CTA_DUR))
    logger.info(f"[video] {len(clips)} sahne hazır, audio={ad:.1f}s")

    video_path = _stage("video-assemble", assemble_video, clips, audio_path)
    logger.info(f"[video] video hazır: {video_path}")

    script_text = "\n\n".join(f"{s['title']}\n{s['content']}" for s in sections)
    return {
        "type": "video", "topic": topic,
        "title": script["title"],
        "description": script.get("description", ""),
        "tags": script.get("tags", []),
        "video_path": video_path,
        "script": script_text,
        "audio_base64": _try_tts(sections[0]["content"] if sections else topic),
        "status": "pending_approval",
    }


# ─────────────────────────────────────────────────────────────
# YouTube Shorts / Instagram Reel
# ─────────────────────────────────────────────────────────────
def create_short_video(topic: str) -> dict:
    script = _stage("script", generate_shorts_script, topic)
    logger.info("[short] script hazır")

    full_text = f"{script['hook']} {script['content']} {script['cta']}"
    audio_path = _stage("audio", generate_audio, full_text, voice="nova")
    logger.info("[short] ses hazır")

    clips = [
        _stage("scene-hook",    render_shorts_scene, script["title"], script["hook"], "", 4.0),
        _stage("scene-content", render_shorts_scene, script["title"], "", script["content"], 5.0),
        _stage("scene-cta",     render_cta_scene, 3.5),
    ]

    video_path = _stage("video-assemble", assemble_video, clips, audio_path)
    logger.info(f"[short] video hazır: {video_path}")

    return {
        "type": "short", "topic": topic,
        "title": script["title"],
        "caption": script.get("caption", ""),
        "tags": script.get("tags", []),
        "video_path": video_path,
        "script": f"{script['hook']}\n\n{script['content']}\n\n{script['cta']}",
        "audio_base64": _try_tts(full_text),
        "status": "pending_approval",
    }


# ─────────────────────────────────────────────────────────────
# Soru Çözüm Videosu
# ─────────────────────────────────────────────────────────────
def create_question_solution_video(topic: str, question_text: str = "") -> dict:
    script = _stage("script", generate_question_solution_script, topic, question_text)
    logger.info("[soru-cozum] script hazır")

    full_text = " ".join(s["content"] for s in script.get("sections", []))
    audio_path = _stage("audio", generate_audio, full_text or topic, voice="nova")
    logger.info("[soru-cozum] ses hazır")

    ad = _audio_duration(audio_path)
    sections = script.get("sections", [])
    options  = script.get("options", [])
    correct  = script.get("correct_option", "A")
    puf      = script.get("puf_nokta", "")

    # Fixed scene times
    q_dur   = 8.0
    ans_dur = 6.5
    puf_dur = 5.0 if puf else 0.0
    n_sec   = max(len(sections), 1)
    sec_dur = max(3.5, (ad - q_dur - ans_dur - puf_dur - _CTA_DUR) / n_sec)

    clips = []

    # Soru slaytı
    q_text = script.get("question_text") or question_text or f"{topic} sorusu"
    clips.append(_stage("scene-question", render_question_scene, q_text, options, q_dur))

    # İçerik slaytları (kavram, şık analizi)
    for i, sec in enumerate(sections):
        lines = _split_lines(sec["content"])
        clips.append(_stage(f"scene-{i}", render_content_scene,
                             sec["title"], lines, i + 1, n_sec, sec_dur))

    # Cevap slaytı — explanation from last content section
    explanation = ""
    for sec in sections:
        t = sec.get("title", "").lower()
        if "doğru" in t or "cevap" in t or "açıkla" in t:
            explanation = sec.get("content", "")
            break
    if not explanation and sections:
        explanation = sections[-1]["content"]

    clips.append(_stage("scene-answer", render_answer_scene, options, correct, explanation, ans_dur))

    # Puf nokta
    if puf:
        clips.append(_stage("scene-tip", render_exam_tip_scene, puf, puf_dur))

    clips.append(_stage("scene-cta", render_cta_scene, _CTA_DUR))
    logger.info(f"[soru-cozum] {len(clips)} sahne hazır, audio={ad:.1f}s")

    video_path = _stage("video-assemble", assemble_video, clips, audio_path)
    logger.info(f"[soru-cozum] video hazır: {video_path}")

    script_text = "\n\n".join(f"{s['title']}\n{s['content']}" for s in sections)
    return {
        "type": "question_solution", "topic": topic,
        "title": script.get("title", f"{topic} — Soru Çözümü"),
        "description": script.get("description", ""),
        "tags": script.get("tags", []),
        "video_path": video_path,
        "script": script_text,
        "audio_base64": _try_tts(full_text[:1200]),
        "status": "pending_approval",
    }


# ─────────────────────────────────────────────────────────────
# Konu Anlatım Videosu
# ─────────────────────────────────────────────────────────────
def create_topic_explanation_video(topic: str) -> dict:
    script = _stage("script", generate_topic_explanation_script, topic)
    logger.info("[konu-anlatim] script hazır")

    full_text = " ".join(s["content"] for s in script.get("sections", []))
    audio_path = _stage("audio", generate_audio, full_text or topic, voice="nova")
    logger.info("[konu-anlatim] ses hazır")

    ad = _audio_duration(audio_path)
    sections     = script.get("sections", [])
    summary_rows = script.get("summary_table", [])
    n_sec = max(len(sections), 1)
    sum_dur = 6.0 if summary_rows else 0.0
    sec_dur = max(3.5, (ad - _INTRO_DUR - sum_dur - _CTA_DUR) / n_sec)

    clips = []
    clips.append(_stage("scene-intro", render_intro_scene,
                         script.get("title", topic), f"Konu Anlatımı: {topic}", _INTRO_DUR))

    for i, sec in enumerate(sections):
        lines = _split_lines(sec["content"])
        clips.append(_stage(f"scene-{i}", render_content_scene,
                             sec["title"], lines, i + 1, n_sec, sec_dur))

    if summary_rows:
        clips.append(_stage("scene-summary", render_summary_scene,
                             f"{topic} — Özet", summary_rows, sum_dur))

    clips.append(_stage("scene-cta", render_cta_scene, _CTA_DUR))
    logger.info(f"[konu-anlatim] {len(clips)} sahne hazır, audio={ad:.1f}s")

    video_path = _stage("video-assemble", assemble_video, clips, audio_path)
    logger.info(f"[konu-anlatim] video hazır: {video_path}")

    script_text = "\n\n".join(f"{s['title']}\n{s['content']}" for s in sections)
    return {
        "type": "topic_explanation", "topic": topic,
        "title": script.get("title", f"{topic} — Konu Anlatımı"),
        "description": script.get("description", ""),
        "tags": script.get("tags", []),
        "video_path": video_path,
        "script": script_text,
        "audio_base64": _try_tts(full_text[:1200]),
        "status": "pending_approval",
    }


# ─────────────────────────────────────────────────────────────
# Instagram Post / Görsel
# ─────────────────────────────────────────────────────────────
def create_post(topic: str) -> dict:
    image_path, script_text = _stage("image-gen", generate_post_image_with_gemini, topic)
    logger.info("[post] görsel hazır")

    try:
        image_url = _stage("image-upload", upload_image, image_path)
        logger.info("[post] görsel yüklendi")
    except Exception as e:
        logger.warning(f"[post] upload hatası: {e}")
        image_url = None

    caption = script_text.split("\n\n")[-1] if "\n\n" in script_text else script_text[:200]
    return {
        "type": "post", "topic": topic, "title": topic,
        "caption": caption,
        "image_path": image_url or image_path,
        "script": script_text,
        "audio_base64": _try_tts(script_text[:1200]),
        "status": "pending_approval",
    }


# ─────────────────────────────────────────────────────────────
# Yayın
# ─────────────────────────────────────────────────────────────
def publish_to_youtube(content: dict) -> dict:
    return upload_to_youtube(
        video_path=content.get("video_path", ""),
        title=content.get("title", ""),
        description=content.get("description", ""),
        tags=content.get("tags", []),
        privacy="private",
    )


def publish_to_instagram(content: dict) -> dict:
    if content.get("type") == "post":
        return post_image_to_instagram(content.get("image_path", ""), content.get("caption", ""))
    return post_reel_to_instagram(content.get("video_path", ""), content.get("caption", ""))
