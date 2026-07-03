"""SGS servis katmanı — PDF analiz + video üretim."""
import logging
import os
from moviepy.editor import AudioFileClip

from app.modules.knowledge.pdf_loader import load_pdf
from app.modules.sgs.analyzer import analyze_sgs_pdf
from app.modules.sgs.storyboard import generate_sgs_topic_storyboard
from app.modules.content.audio_generator import generate_audio_segment
from app.modules.content.scene_engine import render_scene
from app.modules.content.video_assembler import assemble_video
from app.modules.voice.tts import synthesize

logger = logging.getLogger(__name__)


def analyze_pdf_bytes(pdf_bytes: bytes, pdf_name: str) -> dict:
    """PDF bayt dizisi → soru analizi + video planı."""
    logger.info(f"[sgs] PDF yükleniyor: {pdf_name}")
    pdf_text = load_pdf(pdf_bytes)
    if not pdf_text or len(pdf_text.strip()) < 100:
        raise ValueError("PDF'ten metin çıkarılamadı veya metin çok kısa")
    logger.info(f"[sgs] {len(pdf_text)} karakter çıkarıldı")
    return analyze_sgs_pdf(pdf_text, pdf_name)


def build_sgs_topic_video(
    video_plan_item: dict,
    all_questions: list[dict],
) -> dict:
    """
    Video planının tek bir öğesini videoya çevirir.

    video_plan_item: {title, topic, subject, question_ids[], description}
    all_questions: tüm soru listesi (id alanlarıyla)
    """
    title   = video_plan_item.get("title", "SGS Video")
    topic   = video_plan_item.get("topic", "")
    subject = video_plan_item.get("subject", "")
    q_ids   = set(video_plan_item.get("question_ids", []))

    # Sadece bu videodaki soruları filtrele
    questions = [q for q in all_questions if q.get("id") in q_ids]
    if not questions:
        raise ValueError(f"Video için soru bulunamadı: {q_ids}")

    logger.info(f"[sgs] video üretimi başladı: '{title}' — {len(questions)} soru")

    # Storyboard üret
    storyboard = generate_sgs_topic_storyboard(title, topic, subject, questions)
    scenes = storyboard.get("scenes", [])
    if not scenes:
        raise RuntimeError("[sgs] Storyboard sahne içermiyor")

    logger.info(f"[sgs] storyboard hazır: {len(scenes)} sahne")

    clips = []
    audio_clips = []
    audio_paths = []
    preview_narration = ""

    for i, scene in enumerate(scenes):
        narration = str(scene.get("narration", "")).strip()
        if not narration:
            narration = scene.get("title", "devam")

        audio_path, audio_dur = generate_audio_segment(narration)
        audio_paths.append(audio_path)
        logger.info(f"[sgs] sahne {i+1}/{len(scenes)} ({scene.get('type')}) audio={audio_dur:.1f}s")

        clip = render_scene(scene, i + 1, len(scenes))
        clip = clip.set_duration(audio_dur)

        aclip = AudioFileClip(audio_path)
        audio_clips.append(aclip)
        clip = clip.set_audio(aclip)
        clips.append(clip)

        if i == 1:
            preview_narration = narration

    total_dur = sum(c.duration for c in clips)
    logger.info(f"[sgs] {len(clips)} clip, toplam {total_dur:.1f}s")

    video_path = assemble_video(clips)
    logger.info(f"[sgs] video hazır: {video_path}")

    for ac in audio_clips:
        try:
            ac.close()
        except Exception:
            pass

    for ap in audio_paths:
        try:
            os.remove(ap)
        except OSError:
            pass

    script_parts = [
        f"{s.get('title', '')}\n{s.get('narration', '')}"
        for s in scenes
        if s.get("title") and s.get("narration")
    ]

    try:
        audio_b64 = synthesize(preview_narration[:800], voice="nova")
    except Exception:
        audio_b64 = None

    return {
        "video_path": video_path,
        "title": storyboard.get("title", title),
        "description": storyboard.get("description", ""),
        "tags": storyboard.get("tags", []),
        "script": "\n\n".join(script_parts),
        "audio_base64": audio_b64,
        "question_count": len(questions),
        "topic": topic,
        "subject": subject,
        "duration_seconds": total_dur,
    }
