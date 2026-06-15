from fastapi import APIRouter, UploadFile, File, HTTPException
from app.modules.knowledge.service import process_document, list_documents, fetch_document, remove_document

router = APIRouter()


@router.post("")
async def upload_document(file: UploadFile = File(...)):
    content = await file.read()
    return process_document(file.filename, content)


@router.get("")
def get_documents():
    return list_documents()


@router.get("/{document_id}")
def get_document(document_id: str):
    doc = fetch_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Döküman bulunamadı")
    return doc


@router.delete("/{document_id}")
def delete_document(document_id: str):
    doc = fetch_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Döküman bulunamadı")
    remove_document(document_id, doc["storage_path"])
    return {"message": "Döküman silindi"}
