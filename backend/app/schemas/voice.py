from pydantic import BaseModel
from app.schemas.chat import ChatSource


class VoiceResponse(BaseModel):
    transcript: str
    answer_text: str
    answer_audio_base64: str
    agent_used: str
    sources: list[ChatSource] = []
