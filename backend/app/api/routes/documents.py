import logging
import os
import re
import tempfile
from datetime import datetime, timezone
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks, Query
from app.modules.knowledge.service import list_documents, fetch_document, remove_document, reindex_document
from app.db.repositories.sgs_repo import list_analyses
from app.db.repositories.documents_repo import create_document, update_document_status, get_documents as db_get_documents
from app.db.supabase import get_supabase_client
from app.db.storage import upload_file, download_file
from app.schemas.document import DocumentStatus

logger = logging.getLogger(__name__)
router = APIRouter()

_MAX_UPLOAD_BYTES = 50 * 1024 * 1024  # 50 MB
_BUCKET = "documents"
_SAFE_NAME_RE = re.compile(r'[^\w\-.]')


def _index_background(doc_id: str, file_bytes: bytes) -> None:
    """
    Arka planda çalışır — HTTP zaman aşımından bağımsız.
    PDF metin çıkarma → chunking → embedding → Supabase yazma.
    """
    from app.modules.knowledge.pdf_loader import load_pdf
    from app.modules.knowledge.chunker import split_into_chunks
    from app.modules.knowledge.embeddings import embed_texts
    from app.db.repositories.chunks_repo import insert_chunks
    logger.info(f"[documents] arka plan indexleme başladı: {doc_id}")
    try:
        update_document_status(doc_id, DocumentStatus.PROCESSING)
        text = load_pdf(file_bytes)
        raw_chunks = split_into_chunks(text)
        texts = [c["text"] for c in raw_chunks]
        embeddings = embed_texts(texts)
        chunks_with_emb = [
            {"text": c["text"], "embedding": embeddings[i]}
            for i, c in enumerate(raw_chunks)
        ]
        insert_chunks(doc_id, chunks_with_emb)
        update_document_status(doc_id, DocumentStatus.INDEXED)
        logger.info(f"[documents] indexleme tamamlandı: {doc_id} ({len(raw_chunks)} chunk)")
    except Exception as e:
        logger.error(f"[documents] indexleme hatası {doc_id}: {e}", exc_info=True)
        update_document_status(doc_id, DocumentStatus.FAILED)


@router.post("")
async def upload_document(
    file: UploadFile = File(...),
    source_module: str = Form(default="knowledge_center"),
    bg: BackgroundTasks = BackgroundTasks(),
):
    content = await file.read()
    if len(content) > _MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"Dosya boyutu 50 MB sınırını aşıyor ({len(content) // (1024 * 1024)} MB).",
        )
    mime_type = file.content_type or "application/pdf"

    # Türkçe karakter ve boşluk içeren dosya adlarını sanitize et
    safe_name = _SAFE_NAME_RE.sub('_', file.filename or "upload.pdf")

    # AŞAMA 1 (hızlı — HTTP yanıtı bu kadarda biter):
    # Kayıt oluştur → doc_id al → doğru storage path hesapla → storage'a yükle → hemen dön
    doc = create_document(safe_name, "", len(content), mime_type, source_module=source_module)
    doc_id = doc["id"]
    storage_path = f"{_BUCKET}/{doc_id}/{safe_name}"

    sb = get_supabase_client()
    sb.table("documents").update({"storage_path": storage_path}).eq("id", doc_id).execute()
    doc["storage_path"] = storage_path

    upload_file(_BUCKET, f"{doc_id}/{safe_name}", content)

    # AŞAMA 2 (arka plan): metin çıkarma / embedding / indexleme
    bg.add_task(_index_background, doc_id, content)
    return doc


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


# ── GÖREV 6: Kayıp PDF yeniden bağlama ───────────────────────

@router.patch("/{document_id}/relink")
async def relink_document(document_id: str, bg: BackgroundTasks, file: UploadFile = File(...)):
    """
    Kayıp dosyayı yeniden yükle: storage'a yaz, file_status='yeniden_yuklendi',
    sonra arka planda yeniden indeksle.
    """
    doc = fetch_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Döküman bulunamadı")

    content = await file.read()
    if len(content) > _MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"Dosya 50 MB sınırını aşıyor ({len(content) // (1024 * 1024)} MB).",
        )

    storage_path = doc.get("storage_path", "")
    if not storage_path:
        raise HTTPException(status_code=422, detail="Dökümanın storage yolu kayıt dışı.")

    # Bucket prefix'i çıkar: "documents/{doc_id}/..." → "{doc_id}/..."
    clean_path = storage_path.replace("documents/", "", 1)

    try:
        sb = get_supabase_client()
        sb.storage.from_("documents").upload(
            clean_path, content,
            {"content-type": file.content_type or "application/pdf", "upsert": "true"},
        )
    except Exception as e:
        logger.error(f"[documents] relink storage yükleme hatası {document_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Dosya yüklenemedi: {str(e)[:200]}")

    now = datetime.now(timezone.utc).isoformat()
    sb = get_supabase_client()
    sb.table("documents").update({
        "file_status": "yeniden_yuklendi",
        "file_size": len(content),
        "storage_verified_at": now,
        "relinked_at": now,
        "updated_at": "now()",
    }).eq("id", document_id).execute()

    bg.add_task(reindex_document, document_id, storage_path, doc["file_name"])

    logger.info(f"[documents] relink tamamlandı: {document_id}")
    return {
        "message": "Dosya yeniden bağlandı ve indeksleniyor",
        "document_id": document_id,
    }


# ── GÖREV 6: Storage toplu doğrulama ─────────────────────────

def _run_storage_verification():
    """
    Tüm dokümanların storage'da mevcut olup olmadığını kontrol et.
    Arka planda çalışır — file_status'ı günceller.
    """
    sb = get_supabase_client()
    docs = (
        sb.table("documents")
        .select("id, file_name, storage_path, file_status")
        .execute().data or []
    )
    now = datetime.now(timezone.utc).isoformat()
    verified, missing, errors = 0, 0, 0

    for doc in docs:
        doc_id = doc["id"]
        storage_path = doc.get("storage_path", "")
        if not storage_path:
            continue
        clean_path = storage_path.replace("documents/", "", 1)
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".bin", delete=False) as tmp:
                tmp_path = tmp.name
            download_file("documents", clean_path, tmp_path)
            sb.table("documents").update({
                "file_status": "mevcut",
                "storage_verified_at": now,
            }).eq("id", doc_id).execute()
            verified += 1
        except Exception as e:
            err = str(e).lower()
            if "not_found" in err or "404" in err or "object not found" in err:
                sb.table("documents").update({"file_status": "kayip"}).eq("id", doc_id).execute()
                missing += 1
                logger.warning(f"[documents] storage kayıp: {doc_id} — {doc.get('file_name')}")
            else:
                errors += 1
                logger.warning(f"[documents] storage kontrol hatası {doc_id}: {e}")
        finally:
            if tmp_path:
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass

    logger.info(f"[documents] storage doğrulama tamamlandı — "
                f"mevcut={verified} kayip={missing} hata={errors} toplam={len(docs)}")


@router.post("/verify-storage")
def verify_storage(bg: BackgroundTasks):
    """
    Tüm dokümanların storage'da mevcut olup olmadığını arka planda kontrol et.
    Tamamlandığında documents tablosundaki file_status güncellenir.
    """
    bg.add_task(_run_storage_verification)
    return {"message": "Storage doğrulaması başlatıldı. İşlem tamamlandığında doküman listesini yenileyin."}
