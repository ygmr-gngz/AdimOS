from app.db.supabase import get_supabase_client
from app.schemas.document import DocumentStatus


def create_document(file_name: str, storage_path: str):
    supabase = get_supabase_client()
    response = supabase.table("documents").insert({
        "file_name": file_name,
        "storage_path": storage_path,
        "status": DocumentStatus.UPLOADED,
    }).execute()
    return response.data[0] if response.data else None


def get_documents():
    supabase = get_supabase_client()
    response = supabase.table("documents").select("*").order("created_at", desc=True).execute()
    return response.data if response.data else []


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
