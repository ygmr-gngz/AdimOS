from app.core.llm_client import embed as _embed, embed_batch as _embed_batch


def embed_text(text: str) -> list[float]:
    return _embed(text)


def embed_texts(texts: list[str]) -> list[list[float]]:
    return _embed_batch(texts)
