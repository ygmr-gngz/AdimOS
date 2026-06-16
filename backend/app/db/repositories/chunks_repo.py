import logging
from app.db.supabase import get_supabase_client

logger = logging.getLogger(__name__)


def insert_chunks(document_id: str, chunks: list[dict]):
    supabase = get_supabase_client()
    rows = [
        {"document_id": document_id, "chunk_index": i, "chunk_data": c["text"], "embedding": c.get("embedding")}
        for i, c in enumerate(chunks)
    ]
    response = supabase.table("chunks").insert(rows).execute()
    return response.data if response.data else []


def get_chunks_by_document_id(document_id: str):
    supabase = get_supabase_client()
    response = (
        supabase.table("chunks")
        .select("*")
        .eq("document_id", document_id)
        .order("chunk_index", desc=False)
        .execute()
    )
    return response.data if response.data else []


def delete_chunks_by_document_id(document_id: str):
    supabase = get_supabase_client()
    response = supabase.table("chunks").delete().eq("document_id", document_id).execute()
    return response.data if response.data else []


def get_total_chunks() -> int:
    supabase = get_supabase_client()
    try:
        resp = supabase.table("chunks").select("*", count="exact").limit(0).execute()
        return resp.count or 0
    except Exception as e:
        logger.error(f"[chunks] toplam sayı alınamadı: {e}")
        return 0


def search_similar_chunks(
    embedding: list[float],
    match_count: int = 10,
    match_threshold: float = 0.3,
) -> list[dict]:
    supabase = get_supabase_client()
    try:
        response = supabase.rpc("match_chunks", {
            "query_embedding": embedding,
            "match_count": match_count,
            "match_threshold": match_threshold,
        }).execute()
        data = response.data or []
        # normalize: new RPC returns 'content', old returned 'chunk_data'
        for item in data:
            if "content" not in item and "chunk_data" in item:
                item["content"] = item["chunk_data"]
        logger.info(f"[chunks] similarity search: {len(data)} sonuç (threshold={match_threshold})")
        return data
    except Exception as e:
        logger.error(f"[chunks] similarity search hatası: {e}")
        return []
