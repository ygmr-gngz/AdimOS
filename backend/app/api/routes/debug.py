from fastapi import APIRouter
from app.db.supabase import get_supabase_client
from app.core.config import settings

router = APIRouter()


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
