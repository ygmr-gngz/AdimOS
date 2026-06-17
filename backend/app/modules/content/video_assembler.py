import os
import uuid
import logging
import numpy as np
from PIL import Image
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
from app.db.supabase import get_supabase_client

_OUTPUT_DIR = "/tmp/outputs/videos"
_BUCKET = "content-videos"
_CF = 0.35   # crossfade overlap (seconds)
_FPS = 30

logger = logging.getLogger(__name__)

# Slide type → relative weight for time distribution
_WEIGHTS = {
    "intro":    0.65,
    "question": 1.70,
    "content":  1.00,
    "answer":   1.50,
    "summary":  1.40,
    "puf":      1.20,
    "cta":      0.50,
}

# Zoom amount per slide type (subtle = less, strong = more dynamic)
_ZOOM = {
    "intro":    0.03,
    "question": 0.04,
    "content":  0.05,
    "answer":   0.04,
    "summary":  0.03,
    "puf":      0.04,
    "cta":      0.02,
}


def _apply_zoom(clip: ImageClip, direction: str, amount: float) -> ImageClip:
    """
    Ken Burns: crop-and-zoom each frame so the output stays the same resolution
    while the content gently zooms in (direction='in') or out (direction='out').
    """
    tw, th = clip.w, clip.h
    d = max(clip.duration, 0.001)

    def fl(get_frame, t):
        frame = get_frame(t)
        progress = min(t / d, 1.0)
        scale = 1 + amount * progress if direction == "in" else 1 + amount * (1 - progress)
        fh, fw = frame.shape[:2]
        nw, nh = int(fw / scale), int(fh / scale)
        x0, y0 = (fw - nw) // 2, (fh - nh) // 2
        cropped = frame[y0:y0 + nh, x0:x0 + nw]
        resized = np.array(Image.fromarray(cropped).resize((tw, th), Image.LANCZOS))
        return resized

    return clip.fl(fl)


def assemble_video(
    slide_paths: list[str],
    audio_path: str,
    slide_types: list[str] | None = None,
) -> str:
    n = len(slide_paths)
    if n == 0:
        raise ValueError("Slayt listesi boş")

    types = (slide_types or ["content"] * n)[:n]
    # Pad types if shorter than slides
    while len(types) < n:
        types.append("content")

    audio = AudioFileClip(audio_path)
    ad = audio.duration

    # Total raw duration (clips will overlap by _CF each transition)
    total_raw = ad + (n - 1) * _CF
    weights = [_WEIGHTS.get(t, 1.0) for t in types]
    total_w = sum(weights)
    durations = [(w / total_w) * total_raw for w in weights]

    logger.info(f"[assembler] {n} slayt, audio={ad:.1f}s, toplam={sum(durations):.1f}s")

    clips = []
    for i, (path, dur, stype) in enumerate(zip(slide_paths, durations, types)):
        clip = ImageClip(path).set_duration(dur)

        # Ken Burns: alternate direction every slide
        direction = "in" if i % 2 == 0 else "out"
        amount = _ZOOM.get(stype, 0.04)
        clip = _apply_zoom(clip, direction, amount)

        # Dissolve transition — all clips except first fade in
        if i > 0:
            clip = clip.crossfadein(_CF)

        clips.append(clip)
        logger.info(f"[assembler] slayt {i+1}/{n} ({stype}) {dur:.1f}s, zoom-{direction}")

    video = concatenate_videoclips(clips, padding=-_CF, method="compose")
    video = video.set_audio(audio)

    os.makedirs(_OUTPUT_DIR, exist_ok=True)
    local_path = os.path.join(_OUTPUT_DIR, f"{uuid.uuid4()}.mp4")
    video.write_videofile(
        local_path,
        fps=_FPS,
        codec="libx264",
        audio_codec="aac",
        threads=4,
        logger=None,
        preset="fast",
    )

    for c in clips:
        try:
            c.close()
        except Exception:
            pass
    audio.close()
    video.close()

    public_url = _upload_to_supabase(local_path)

    try:
        os.remove(local_path)
    except OSError:
        pass

    logger.info(f"[assembler] yüklendi: {public_url}")
    return public_url


def _upload_to_supabase(local_path: str) -> str:
    supabase = get_supabase_client()
    file_name = f"videos/{uuid.uuid4()}.mp4"
    with open(local_path, "rb") as f:
        supabase.storage.from_(_BUCKET).upload(
            file_name,
            f,
            {"content-type": "video/mp4"},
        )
    return supabase.storage.from_(_BUCKET).get_public_url(file_name)
