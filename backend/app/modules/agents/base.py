from app.core.llm_client import chat as llm_chat


class BaseAgent:
    model = "gpt-4o-mini"
    temperature = 0.4
    max_tokens = 1500

    def __init__(self, system_prompt: str):
        self.system_prompt = system_prompt

    def chat(self, message: str, history: list[dict] | None = None) -> str:
        messages = [{"role": "system", "content": self.system_prompt}]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": message})

        return llm_chat(
            messages,
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            caller=type(self).__name__,
        )
