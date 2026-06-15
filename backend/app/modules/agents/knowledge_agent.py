from app.modules.agents.base import BaseAgent
from app.modules.knowledge.rag import query


class KnowledgeAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            "Sen Adım Müşavirlik'in bilgi asistanısın. Mevzuat, muhasebe ve danışmanlık sorularını yanıtlarsın."
        )

    def ask(self, message: str, history: list[dict] | None = None) -> dict:
        return query(message, history)
