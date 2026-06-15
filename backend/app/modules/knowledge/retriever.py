from app.db.repositories.chunks_repo import search_similar_chunks
from app.modules.knowledge.embeddings import embed_text


def retrieve(query: str, match_count: int = 5) -> list[dict]:
    embedding = embed_text(query)
    return search_similar_chunks(embedding, match_count)
