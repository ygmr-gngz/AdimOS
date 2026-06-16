from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
from app.db.supabase import get_supabase_client
import os
import uuid

_OUTPUT_DIR = "/tmp/outputs/videos"
_BUCKET = "content-videos"


def assemble_video(slide_paths: list[str], audio_path: str) -> str:
    os.makedirs(_OUTPUT_DIR, exist_ok=True)

    audio = AudioFileClip(audio_path)
    slide_duration = audio.duration / len(slide_paths)

    clips = [
        ImageClip(path).set_duration(slide_duration)
        for path in slide_paths
    ]

    video = concatenate_videoclips(clips, method="compose")
    video = video.set_audio(audio)

    local_path = os.path.join(_OUTPUT_DIR, f"{uuid.uuid4()}.mp4")
    video.write_videofile(
        local_path,
        fps=24,
        codec="libx264",
        audio_codec="aac",
        threads=4,
        logger=None,
    )

    audio.close()
    video.close()

    public_url = _upload_to_supabase(local_path)

    try:
        os.remove(local_path)
    except OSError:
        pass

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
