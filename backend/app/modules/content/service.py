import logging
from app.modules.content.script_generator import (
    generate_video_script, generate_shorts_script, generate_post_content,
    generate_question_solution_script, generate_topic_explanation_script,
)
from app.modules.content.audio_generator import generate_audio
from app.modules.content.slide_generator import (
    create_slide, create_intro_slide, create_cta_slide,
    create_shorts_slide, create_shorts_cta_slide,
    create_post_image, create_question_slide, create_answer_slide,
    create_summary_slide,
)
from app.modules.content.video_assembler import assemble_video
from app.modules.content.youtube_uploader import upload_to_youtube, make_public
from app.modules.content.instagram_poster import post_image_to_instagram, post_reel_to_instagram
from app.modules.content.storage import upload_image
from app.modules.content.gemini_image import generate_post_image_with_gemini
from app.modules.voice.tts import synthesize

logger = logging.getLogger(__name__)


def _sub_slides(sections: list[dict], words_per_slide: int = 35) -> list[dict]:
    result = []
    for sec in sections:
        words = sec["content"].split()
        chunks = [words[i:i + words_per_slide] for i in range(0, len(words), words_per_slide)]
        for idx, chunk in enumerate(chunks):
            result.append({"title": sec["title"] if idx == 0 else "", "content": " ".join(chunk)})
    return result


def _try_tts(text: str) -> str | None:
    try:
        return synthesize(text[:1200], voice="nova")
    except Exception:
        return None


def _stage(name: str, fn, *args, **kwargs):
    """Run fn(*args, **kwargs) and re-raise with stage name prepended on failure."""
    try:
        return fn(*args, **kwargs)
    except Exception as e:
        raise RuntimeError(f"[{name}] {e}") from e


# ─────────────────────────────────────────────────────────────
# Uzun Video (konu anlatım tarzı)
# ─────────────────────────────────────────────────────────────
def create_normal_video(topic: str, duration_minutes: int = 5) -> dict:
    script = _stage("script", generate_video_script, topic, duration_minutes)
    logger.info("[video] script hazır")

    full_text = " ".join(s["content"] for s in script["sections"])
    audio_path = _stage("audio", generate_audio, full_text, voice="nova")
    logger.info("[video] ses hazır")

    slides, stypes = [], []
    slides.append(create_intro_slide(script["title"], script.get("description", "")[:80]))
    stypes.append("intro")
    sub = _sub_slides(script["sections"])
    for i, s in enumerate(sub):
        slides.append(_stage("slide", create_slide, s["title"], s["content"], i + 1, len(sub)))
        stypes.append("content")
    slides.append(create_cta_slide())
    stypes.append("cta")
    logger.info(f"[video] {len(slides)} slayt hazır")

    video_path = _stage("video-assemble", assemble_video, slides, audio_path, stypes)
    logger.info(f"[video] video hazır: {video_path}")

    script_text = "\n\n".join(f"{s['title']}\n{s['content']}" for s in script["sections"])
    return {
        "type": "video",
        "topic": topic,
        "title": script["title"],
        "description": script.get("description", ""),
        "tags": script.get("tags", []),
        "video_path": video_path,
        "script": script_text,
        "audio_base64": _try_tts(script["sections"][0]["content"] if script["sections"] else topic),
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

    slides = [
        create_shorts_slide(title=script["title"], content="", hook=script["hook"]),
        create_shorts_slide(title=script["title"], content=script["content"], hook=""),
        create_shorts_cta_slide(),
    ]
    stypes = ["intro", "content", "cta"]
    video_path = _stage("video-assemble", assemble_video, slides, audio_path, stypes)
    logger.info(f"[short] video hazır: {video_path}")
    script_text = f"{script['hook']}\n\n{script['content']}\n\n{script['cta']}"

    return {
        "type": "short",
        "topic": topic,
        "title": script["title"],
        "caption": script["caption"],
        "tags": script.get("tags", []),
        "video_path": video_path,
        "script": script_text,
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

    slides, stypes = [], []

    # Soru slaytı
    q_text = script.get("question_text") or question_text or f"{topic} sorusu"
    slides.append(create_question_slide(q_text, topic)); stypes.append("question")

    # İçerik slaytları
    sections = script.get("sections", [])
    for i, s in enumerate(sections):
        sub = _sub_slides([s])
        for j, ss in enumerate(sub):
            slides.append(create_slide(ss["title"], ss["content"], i + 1, len(sections)))
            stypes.append("content")

    # Cevap slaytı
    correct = script.get("correct_option", "")
    explanation = ""
    for s in sections:
        if "doğru" in s.get("title", "").lower() or "cevap" in s.get("title", "").lower():
            explanation = s.get("content", "")
            break
    if not explanation and sections:
        explanation = sections[-2]["content"] if len(sections) >= 2 else sections[0]["content"]
    slides.append(create_answer_slide(explanation, correct)); stypes.append("answer")

    # Özet / puf nokta
    puf = script.get("puf_nokta", "")
    if puf:
        slides.append(create_slide("Sınavda Dikkat!", puf, len(sections), len(sections)))
        stypes.append("puf")

    slides.append(create_cta_slide()); stypes.append("cta")
    logger.info(f"[soru-cozum] {len(slides)} slayt hazır")
    video_path = _stage("video-assemble", assemble_video, slides, audio_path, stypes)
    logger.info(f"[soru-cozum] video hazır: {video_path}")
    script_text = "\n\n".join(f"{s['title']}\n{s['content']}" for s in sections)

    return {
        "type": "question_solution",
        "topic": topic,
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

    slides, stypes = [], []
    slides.append(create_intro_slide(script.get("title", topic), f"Konu Anlatımı: {topic}"))
    stypes.append("intro")

    sections = script.get("sections", [])
    for i, s in enumerate(sections):
        sub = _sub_slides([s])
        for ss in sub:
            slides.append(create_slide(ss["title"], ss["content"], i + 1, len(sections)))
            stypes.append("content")

    # Özet tablo slaytı
    summary_rows = script.get("summary_table", [])
    if summary_rows:
        slides.append(create_summary_slide(f"{topic} — Özet", summary_rows))
        stypes.append("summary")

    slides.append(create_cta_slide()); stypes.append("cta")
    logger.info(f"[konu-anlatim] {len(slides)} slayt hazır")
    video_path = _stage("video-assemble", assemble_video, slides, audio_path, stypes)
    logger.info(f"[konu-anlatim] video hazır: {video_path}")
    script_text = "\n\n".join(f"{s['title']}\n{s['content']}" for s in sections)

    return {
        "type": "topic_explanation",
        "topic": topic,
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
        logger.warning(f"[post] image upload hatası: {e}")
        image_url = None

    caption = script_text.split("\n\n")[-1] if "\n\n" in script_text else script_text[:200]

    return {
        "type": "post",
        "topic": topic,
        "title": topic,
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
