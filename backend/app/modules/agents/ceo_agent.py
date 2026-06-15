from app.modules.agents.base import BaseAgent
from app.db.repositories.leads_repo import get_leads
from app.db.repositories.students_repo import get_students
from app.db.repositories.briefs_repo import create_brief


class CEOAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            "Sen bir CEO asistanısın. İşletmenin genel durumunu analiz eder, strateji ve karar desteği sunarsın. Türkçe, net ve özlü yanıt ver."
        )

    def generate_daily_brief(self) -> dict:
        leads = get_leads()
        students = get_students()

        new_leads = [l for l in leads if l.get("status") == "new"]
        active_students = [s for s in students if s.get("status") == "active"]

        prompt = f"""Günlük yönetim özeti oluştur:
- Müşteri adayı: {len(leads)} toplam, {len(new_leads)} yeni
- Öğrenci: {len(students)} toplam, {len(active_students)} aktif

Kısa, madde madde Türkçe özet yaz."""

        content = self.chat(prompt)
        return create_brief("Günlük Özet", content, "daily_brief")

    def ask(self, message: str, history: list[dict] | None = None) -> str:
        return self.chat(message, history)
