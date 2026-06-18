"""
Content service — storyboard + per-scene TTS audio for perfect A/V sync.

Pipeline:
  generate_storyboard(topic, type) → scenes[]
  for each scene:
      generate_audio_segment(scene.narration) → (path, duration)
      render_scene(scene, duration=audio_dur) → VideoClip
      clip.set_audio(audio)
  assemble_video(clips)  ← audio embedded, no single audio file needed
"""
import logging
from moviepy.editor import AudioFileClip

from app.modules.content.script_generator import (
    generate_storyboard,
    apply_director_pass,
    generate_post_content,
)
from app.modules.content.audio_generator import generate_audio_segment, generate_audio
from app.modules.content.scene_engine import render_scene
from app.modules.content.video_assembler import assemble_video
from app.modules.content.youtube_uploader import upload_to_youtube
from app.modules.content.instagram_poster import post_image_to_instagram, post_reel_to_instagram
from app.modules.content.storage import upload_image
from app.modules.content.gemini_image import generate_post_image_with_gemini
from app.modules.voice.tts import synthesize

logger = logging.getLogger(__name__)

_CTA_NARRATION = "Bu videoyu beğendiyseniz abone olmayı ve beğenmeyi unutmayın. Daha fazla içerik için Adım Müşavir'i takip edin. adimmusavir.com"


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


def _run_qc(clips: list, scenes: list, total_dur: float) -> None:
    """
    QC Agent — video üretimi sonrası kalite kontrolü.
    Sorunları loglar; üretimi durdurmaz, sadece raporlar.
    """
    issues: list[str] = []

    if total_dur < 30:
        issues.append(f"Video çok kısa: {total_dur:.1f}s (min 30s beklenir)")
    if total_dur > 900:
        issues.append(f"Video çok uzun: {total_dur:.1f}s (max 15dk beklenir)")

    for i, (clip, scene) in enumerate(zip(clips, scenes)):
        dur = clip.duration
        scene_type = scene.get("type", "?")
        if dur < 2:
            issues.append(f"Sahne {i+1} ({scene_type}): çok kısa {dur:.1f}s — TTS hatası olabilir")
        if dur > 40:
            issues.append(f"Sahne {i+1} ({scene_type}): çok uzun {dur:.1f}s — izlenme düşebilir")
        if clip.audio is None:
            issues.append(f"Sahne {i+1} ({scene_type}): ses yok — senkron problemi")

    # Sahne tipi tekrarı kontrolü
    types = [s.get("type", "") for s in scenes]
    for j in range(len(types) - 2):
        if types[j] == types[j+1] == types[j+2] and types[j] not in ("content",):
            issues.append(f"Sahne {j+1}-{j+3}: üst üste aynı tip '{types[j]}' — monoton görünebilir")

    if issues:
        logger.warning(f"[qc] {len(issues)} uyarı:")
        for issue in issues:
            logger.warning(f"[qc]   • {issue}")
    else:
        logger.info(f"[qc] geçti — {len(clips)} sahne, {total_dur:.1f}s, ses senkronu OK")


def _build_synced_video(
    topic: str,
    content_type: str,
    category: str = "smmm",
    extra: dict | None = None,
) -> dict:
    """
    Core pipeline:
    1. Generate storyboard (scenes with narration + display_lines)
    2. For each scene: TTS audio → measure duration → render scene at that duration
    3. Embed audio in each clip
    4. Concatenate → upload → public URL
    """
    storyboard = _stage("script", generate_storyboard, topic, content_type, category)

    # Director Agent — storyboard kalite geçişi (hata halinde orijinali kullan)
    storyboard = _stage("director", apply_director_pass, storyboard, topic, content_type)

    scenes = storyboard.get("scenes", [])
    if not scenes:
        raise RuntimeError("[script] Storyboard sahne içermiyor")

    logger.info(f"[service] storyboard hazır (director geçişi tamamlandı): {len(scenes)} sahne")

    # Inject extra data into matching scenes (question_text, options etc.)
    if extra:
        for scene in scenes:
            for k, v in extra.items():
                if k not in scene or not scene[k]:
                    scene[k] = v

    clips = []
    audio_clips = []   # track all open AudioFileClip for cleanup
    preview_text = ""

    for i, scene in enumerate(scenes):
        narration = str(scene.get("narration", "")).strip()
        if not narration:
            narration = scene.get("title", "devam")

        # Per-scene TTS → exact duration
        audio_path, audio_dur = _stage(f"audio-{i}", generate_audio_segment, narration)
        logger.info(f"[service] sahne {i+1}/{len(scenes)} ({scene.get('type')}) audio={audio_dur:.1f}s")

        # Render scene at exactly the audio duration
        clip = _stage(f"scene-{i}", render_scene, scene, i + 1, len(scenes))
        clip = clip.set_duration(audio_dur)

        # Embed audio
        aclip = AudioFileClip(audio_path)
        audio_clips.append(aclip)
        clip = clip.set_audio(aclip)
        clips.append(clip)

        if i == 1:  # hook/second scene preview
            preview_text = narration

    total_dur = sum(c.duration for c in clips)
    logger.info(f"[service] {len(clips)} clip hazır, toplam süre = {total_dur:.1f}s")

    video_path = _stage("video-assemble", assemble_video, clips)
    logger.info(f"[service] video hazır: {video_path}")

    # QC Agent — kalite kontrol raporu
    _run_qc(clips, scenes, total_dur)

    # Cleanup audio file handles
    for ac in audio_clips:
        try:
            ac.close()
        except Exception:
            pass

    # Build script text for display
    script_parts = []
    for scene in scenes:
        t = scene.get("title", "")
        n = scene.get("narration", "")
        if t and n:
            script_parts.append(f"{t}\n{n}")

    return {
        "video_path": video_path,
        "title": storyboard.get("title", topic),
        "description": storyboard.get("description", ""),
        "tags": storyboard.get("tags", []),
        "script": "\n\n".join(script_parts),
        "audio_base64": _try_tts(preview_text or topic),
    }


# ─────────────────────────────────────────────────────────────
# Uzun Video (konu anlatımı)
# ─────────────────────────────────────────────────────────────
def create_normal_video(topic: str, duration_minutes: int = 5, category: str = "smmm") -> dict:
    result = _build_synced_video(topic, "video", category)
    return {**result, "type": "video", "topic": topic, "status": "pending_approval"}


# ─────────────────────────────────────────────────────────────
# YouTube Shorts / Instagram Reel
# ─────────────────────────────────────────────────────────────
def create_short_video(topic: str, category: str = "smmm") -> dict:
    result = _build_synced_video(topic, "short", category)
    return {
        **result,
        "type": "short",
        "topic": topic,
        "caption": result.get("description", ""),
        "status": "pending_approval",
    }


# ─────────────────────────────────────────────────────────────
# Soru Çözüm Videosu
# ─────────────────────────────────────────────────────────────
def create_question_solution_video(topic: str, question_text: str = "", category: str = "smmm") -> dict:
    extra = {}
    if question_text:
        extra["question_text"] = question_text
    result = _build_synced_video(topic, "question_solution", category, extra)
    return {**result, "type": "question_solution", "topic": topic, "status": "pending_approval"}


# ─────────────────────────────────────────────────────────────
# Konu Anlatım Videosu
# ─────────────────────────────────────────────────────────────
def create_topic_explanation_video(topic: str, category: str = "smmm") -> dict:
    result = _build_synced_video(topic, "topic_explanation", category)
    return {**result, "type": "topic_explanation", "topic": topic, "status": "pending_approval"}


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
