from fastapi import APIRouter, UploadFile, File
from app.schemas.voice import VoiceResponse
from app.modules.voice.service import process_voice

router = APIRouter()


@router.post("", response_model=VoiceResponse)
async def voice_chat(audio: UploadFile = File(...)):
    audio_bytes = await audio.read()
    result = process_voice(audio_bytes)
    return VoiceResponse(**result)
