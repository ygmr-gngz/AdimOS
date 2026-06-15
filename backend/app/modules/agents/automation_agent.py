from app.modules.agents.base import BaseAgent


class AutomationAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            "Sen bir otomasyon asistanısın. İş süreçlerini otomatize etmek için görevler planlar ve yönetirsin. Türkçe yanıt ver."
        )

    def plan_workflow(self, description: str) -> str:
        return self.chat(f"Aşağıdaki süreci otomatize etmek için adım adım bir iş akışı planla:\n{description}")
