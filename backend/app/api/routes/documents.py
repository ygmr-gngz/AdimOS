import logging
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Query
from app.modules.knowledge.service import process_document, list_documents, fetch_document, remove_document, reindex_document
from app.db.repositories.sgs_repo import list_analyses
from app.db.repositories.documents_repo import create_document, get_documents as db_get_documents
from app.db.supabase import get_supabase_client

logger = logging.getLogger(__name__)
router = APIRouter()

_MAX_UPLOAD_BYTES = 50 * 1024 * 1024  # 50 MB


@router.post("")
async def upload_document(file: UploadFile = File(...)):
    content = await file.read()
    if len(content) > _MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"Dosya boyutu 50 MB sınırını aşıyor ({len(content) // (1024 * 1024)} MB).",
        )
    mime_type = file.content_type or "application/pdf"
    return process_document(file.filename or "upload", content, mime_type)


@router.get("")
def get_documents(source_module: str | None = Query(None)):
    return list_documents(source_module=source_module)


@router.post("/sync-sgs")
def sync_sgs_documents():
    """SGS Akademi analizlerini documents tablosuna senkronize et."""
    try:
        analyses = list_analyses()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SGS analizleri alınamadı: {e}")

    synced, already_exists, errors = 0, 0, 0
    for analysis in analyses:
        analysis_id = analysis.get("id")
        pdf_name = analysis.get("pdf_name", "unknown.pdf")
        try:
            sb = get_supabase_client()
            existing = sb.table("documents").select("id").eq("sgs_analysis_id", analysis_id).execute()
            if existing.data:
                already_exists += 1
                continue
            create_document(
                file_name=pdf_name,
                storage_path=f"sgs/{pdf_name}",
                file_size=0,
                mime_type="application/pdf",
                source_module="sgs_academy",
                sgs_analysis_id=analysis_id,
            )
            synced += 1
        except Exception as e:
            logger.warning(f"[documents] sgs sync hatası analysis_id={analysis_id}: {e}")
            errors += 1

    return {
        "synced": synced,
        "already_exists": already_exists,
        "errors": errors,
        "total_analyses": len(analyses),
    }


@router.get("/{document_id}")
def get_document(document_id: str):
    doc = fetch_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Döküman bulunamadı")
    return doc


@router.post("/{document_id}/reindex")
def reindex_doc(document_id: str, bg: BackgroundTasks):
    doc = fetch_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Döküman bulunamadı")
    bg.add_task(reindex_document, document_id, doc["storage_path"], doc["file_name"])
    return {"message": "Yeniden işleme başlatıldı", "document_id": document_id}


@router.delete("/{document_id}")
def delete_document(document_id: str):
    doc = fetch_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Döküman bulunamadı")
    remove_document(document_id, doc["storage_path"])
    return {"message": "Döküman silindi"}
