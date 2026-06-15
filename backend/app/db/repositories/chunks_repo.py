from app.db.supabase import get_supabase_client

def insert_chunks(document_id: str, chunks: list[dict]):
    supabase = get_supabase_client()
    rows = [
        {"document_id": document_id, "chunk_index": i, "chunk_data": c["text"], "embedding": c.get("embedding")}
        for i, c in enumerate(chunks)
    ]
    response = supabase.table("chunks").insert(rows).execute()
    return response.data if response.data else []


def get_chunks_by_document_id(document_id:str):
    supabase = get_supabase_client()
    response = supabase.table("chunks").select("*").eq("document_id", document_id).order("chunk_index", desc=False).execute()
    return response.data if response.data else []

def delete_chunks_by_document_id(document_id: str):
    supabase = get_supabase_client()
    response = supabase.table("chunks").delete().eq("document_id", document_id).execute()
    return response.data if response.data else []

def search_similar_chunks(embedding: list[float], match_count: int = 5) -> list[dict]:
    supabase = get_supabase_client()
    response = supabase.rpc("match_chunks", {
        "query_embedding": embedding,
        "match_count": match_count,
    }).execute()
    return response.data if response.data else []