import logging
from app.db.supabase import get_supabase_client

logger = logging.getLogger(__name__)


def insert_chunks(document_id: str, chunks: list[dict], workspace_id: str | None = None):
    supabase = get_supabase_client()
    if workspace_id is None:
        doc = supabase.table("documents").select("workspace_id").eq("id", document_id).single().execute()
        workspace_id = (doc.data or {}).get("workspace_id") or "default"
    rows = [
        {"document_id": document_id, "workspace_id": workspace_id, "chunk_index": i,
         "chunk_data": c["text"], "embedding": c.get("embedding")}
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
    workspace_id: str = "default",
) -> list[dict]:
    supabase = get_supabase_client()
    try:
        # Fail closed until migration 019 is applied: never fall back to the
        # legacy global RPC, because that would cross the workspace boundary.
        response = supabase.rpc("match_chunks_scoped", {
            "query_embedding": embedding,
            "match_count": match_count,
            "match_threshold": match_threshold,
            "filter_workspace_id": workspace_id,
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
