from openai import OpenAI
from app.core.config import settings


class BaseAgent:
    model = "gpt-4o-mini"

    def __init__(self, system_prompt: str):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.system_prompt = system_prompt

    def chat(self, message: str, history: list[dict] | None = None) -> str:
        messages = [{"role": "system", "content": self.system_prompt}]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": message})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
        )
        return response.choices[0].message.content
