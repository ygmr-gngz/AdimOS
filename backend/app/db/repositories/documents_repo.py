from app.db.supabase import get_supabase_client
from app.schemas.document import DocumentStatus


def create_document(
    file_name: str,
    storage_path: str,
    file_size: int = 0,
    mime_type: str = "application/pdf",
    source_module: str = "knowledge_center",
    sgs_analysis_id: str | None = None,
):
    supabase = get_supabase_client()
    payload: dict = {
        "file_name": file_name,
        "storage_path": storage_path,
        "status": DocumentStatus.UPLOADED,
        "file_size": file_size,
        "mime_type": mime_type,
        "source_module": source_module,
    }
    if sgs_analysis_id:
        payload["sgs_analysis_id"] = sgs_analysis_id
    response = supabase.table("documents").insert(payload).execute()
    return response.data[0] if response.data else None


def get_documents(source_module: str | None = None):
    supabase = get_supabase_client()
    query = supabase.table("documents").select("*").order("created_at", desc=True)
    if source_module:
        query = query.eq("source_module", source_module)
    response = query.execute()
    return response.data if response.data else []


def get_latest_document(source_module: str | None = "knowledge_center") -> dict | None:
    """En son yüklenen dokümanı döndür (created_at DESC)."""
    supabase = get_supabase_client()
    query = supabase.table("documents").select("*").order("created_at", desc=True).limit(1)
    if source_module:
        query = query.eq("source_module", source_module)
    response = query.execute()
    if response.data:
        return response.data[0]
    # source_module filtresi sonuç vermediyse tüm modüllere bak
    if source_module:
        response = supabase.table("documents").select("*").order("created_at", desc=True).limit(1).execute()
        return response.data[0] if response.data else None
    return None


def get_document(document_id: str):
    supabase = get_supabase_client()
    response = supabase.table("documents").select("*").eq("id", document_id).execute()
    return response.data[0] if response.data else None


def update_document_status(document_id: str, status: DocumentStatus):
    supabase = get_supabase_client()
    response = supabase.table("documents").update({
        "status": status,
    }).eq("id", document_id).execute()
    return response.data[0] if response.data else None


def delete_document(document_id: str):
    supabase = get_supabase_client()
    supabase.table("documents").delete().eq("id", document_id).execute()
