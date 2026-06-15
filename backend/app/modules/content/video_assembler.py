from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
import os
import uuid

_OUTPUT_DIR = "outputs/videos"


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

    output_path = os.path.join(_OUTPUT_DIR, f"{uuid.uuid4()}.mp4")
    video.write_videofile(
        output_path,
        fps=24,
        codec="libx264",
        audio_codec="aac",
        threads=4,
        logger=None,
    )

    audio.close()
    video.close()

    return output_path
