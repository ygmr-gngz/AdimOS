from pydantic import BaseModel
from app.schemas.chat import Citation

class VoiceResponse(BaseModel):
    transcript: str
    answer_text: str
    answer_audio_base64: str
    agent_used: str
    citations: list[Citation] = []
