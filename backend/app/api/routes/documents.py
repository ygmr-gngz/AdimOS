from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from app.modules.knowledge.service import process_document, list_documents, fetch_document, remove_document, reindex_document

router = APIRouter()


@router.post("")
async def upload_document(file: UploadFile = File(...)):
    content = await file.read()
    mime_type = file.content_type or "application/pdf"
    return process_document(file.filename or "upload", content, mime_type)


@router.get("")
def get_documents():
    return list_documents()


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
