from openai import OpenAI
from app.core.config import settings
import os
import uuid

_client = OpenAI(api_key=settings.OPENAI_API_KEY)
_OUTPUT_DIR = "/tmp/audio"


def generate_audio_segment(text: str, voice: str = "nova") -> tuple[str, float]:
    """
    TTS üretir ve (dosya_yolu, süre_saniye) döndürür.
    Her sahne için ayrı çağrılır → mükemmel sync.
    """
    path = generate_audio(text, voice)
    from moviepy.editor import AudioFileClip
    c = AudioFileClip(path)
    dur = c.duration
    c.close()
    return path, dur


def generate_audio(text: str, voice: str = "onyx") -> str:
    """
    Metni sese çevirir ve dosya yolunu döndürür.
    Sesler: onyx (erkek, derin), nova (kadın), alloy, echo, fable, shimmer
    """
    os.makedirs(_OUTPUT_DIR, exist_ok=True)
    file_path = os.path.join(_OUTPUT_DIR, f"{uuid.uuid4()}.mp3")

    response = _client.audio.speech.create(
        model="tts-1-hd",
        voice=voice,
        input=text,
        speed=0.93,
    )

    with open(file_path, "wb") as f:
        f.write(response.content)

    return file_path
