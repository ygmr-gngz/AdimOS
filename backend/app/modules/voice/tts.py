from openai import OpenAI
from app.core.config import settings
import base64

_client = OpenAI(api_key=settings.OPENAI_API_KEY)


def synthesize(text: str, voice: str = "alloy") -> str:
    response = _client.audio.speech.create(
        model="tts-1",
        voice=voice,
        input=text,
    )
    return base64.b64encode(response.content).decode("utf-8")
