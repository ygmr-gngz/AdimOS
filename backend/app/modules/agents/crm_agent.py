from app.modules.agents.base import BaseAgent
from app.db.repositories.leads_repo import get_leads, get_lead


class CRMAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            "Sen bir CRM asistanısın. Müşteri adaylarını takip eder, skorlar ve sonraki adım önerirsin. Türkçe yanıt ver."
        )

    def analyze_lead(self, lead_id: str) -> str:
        lead = get_lead(lead_id)
        if not lead:
            return "Müşteri adayı bulunamadı."
        return self.chat(f"Bu müşteri adayını analiz et ve sonraki adımı öner:\n{lead}")

    def summarize_pipeline(self) -> str:
        leads = get_leads()
        return self.chat(f"Bu müşteri listesini analiz et ve genel durumu özetle:\n{leads}")
