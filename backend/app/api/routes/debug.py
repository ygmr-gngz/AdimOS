from fastapi import APIRouter
from app.db.supabase import get_supabase_client
from app.core.config import settings
from app.modules.knowledge.embeddings import embed_text
from app.db.repositories.chunks_repo import search_similar_chunks

router = APIRouter()


@router.get("/rag")
def debug_rag(q: str = "mali tablolar nedir"):
    """RAG pipeline'ını test eder: embed → match_chunks → sonuçları döndür"""
    result = {}
    try:
        embedding = embed_text(q)
        result["embed_ok"] = True
        result["embedding_dim"] = len(embedding)
    except Exception as e:
        result["embed_ok"] = False
        result["embed_error"] = str(e)
        return result

    try:
        chunks = search_similar_chunks(embedding, 5)
        result["chunks_found"] = len(chunks)
        result["chunks"] = [
            {"chunk_data": c.get("chunk_data", "")[:120], "similarity": c.get("similarity")}
            for c in chunks
        ]
    except Exception as e:
        result["chunks_error"] = str(e)

    return result


@router.get("")
def debug_supabase():
    result = {
        "env": {
            "supabase_url": bool(settings.SUPABASE_URL),
            "service_role_key": bool(settings.SUPABASE_SERVICE_ROLE_KEY),
            "openai_api_key": bool(settings.OPENAI_API_KEY),
        },
        "tables": {},
        "storage": {},
    }

    try:
        supabase = get_supabase_client()

        for table in ("documents", "chunks", "generated_contents"):
            try:
                r = supabase.table(table).select("*", count="exact").limit(0).execute()
                result["tables"][table] = {"ok": True, "count": r.count}
            except Exception as e:
                result["tables"][table] = {"ok": False, "error": str(e)}

        for bucket in ("documents", "content"):
            try:
                supabase.storage.from_(bucket).list()
                result["storage"][bucket] = {"ok": True}
            except Exception as e:
                result["storage"][bucket] = {"ok": False, "error": str(e)}

    except Exception as e:
        result["connection_error"] = str(e)

    return result
