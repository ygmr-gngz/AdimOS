from openai import OpenAI
from app.core.config import settings
import io

_client = OpenAI(api_key=settings.OPENAI_API_KEY)


def transcribe(audio_bytes: bytes, filename: str = "audio.webm") -> str:
    audio_file = io.BytesIO(audio_bytes)
    audio_file.name = filename
    response = _client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file,
        language="tr",
    )
    return response.text
