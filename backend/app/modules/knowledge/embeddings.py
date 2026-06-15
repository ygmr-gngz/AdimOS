from openai import OpenAI
from app.core.config import settings

_client = OpenAI(api_key=settings.OPENAI_API_KEY)
_MODEL = "text-embedding-3-small"


def embed_text(text: str) -> list[float]:
    response = _client.embeddings.create(model=_MODEL, input=text)
    return response.data[0].embedding


def embed_texts(texts: list[str]) -> list[list[float]]:
    response = _client.embeddings.create(model=_MODEL, input=texts)
    return [item.embedding for item in response.data]
