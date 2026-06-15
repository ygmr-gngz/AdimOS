from app.modules.agents.base import BaseAgent
from app.modules.knowledge.rag import query


class VoiceAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            "Sen bir sesli asistanısın. Cevapların sesli okunacağından kısa, net ve doğal konuşma diliyle yanıt ver. Türkçe konuş."
        )

    def respond(self, transcript: str, history: list[dict] | None = None) -> dict:
        return query(transcript, history)
