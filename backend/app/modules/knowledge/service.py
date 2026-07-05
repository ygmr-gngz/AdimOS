import logging
from app.db.repositories.documents_repo import create_document, update_document_status, get_documents, get_document, delete_document
from app.db.repositories.chunks_repo import insert_chunks, delete_chunks_by_document_id
from app.db.storage import upload_file, delete_file
from app.modules.knowledge.pdf_loader import load_pdf
from app.modules.knowledge.chunker import split_into_chunks
from app.modules.knowledge.embeddings import embed_texts
from app.schemas.document import DocumentStatus

logger = logging.getLogger(__name__)
BUCKET = "documents"


def process_document(file_name: str, file_bytes: bytes, mime_type: str = "application/pdf") -> dict:
    logger.info(f"[knowledge] döküman işleniyor: {file_name} ({len(file_bytes)} byte)")
    doc = create_document(file_name, f"{BUCKET}/{file_name}", len(file_bytes), mime_type)
    document_id = doc["id"]

    try:
        update_document_status(document_id, DocumentStatus.PROCESSING)

        logger.info(f"[knowledge] storage'a yükleniyor: {document_id}")
        upload_file(BUCKET, f"{document_id}/{file_name}", file_bytes)

        logger.info(f"[knowledge] PDF metni çıkarılıyor")
        text = load_pdf(file_bytes)
        raw_chunks = split_into_chunks(text)
        logger.info(f"[knowledge] {len(raw_chunks)} chunk oluşturuldu")

        texts = [c["text"] for c in raw_chunks]
        embeddings = embed_texts(texts)
        logger.info(f"[knowledge] {len(embeddings)} embedding üretildi")

        chunks_with_embeddings = [
            {"text": c["text"], "embedding": embeddings[i]}
            for i, c in enumerate(raw_chunks)
        ]

        insert_chunks(document_id, chunks_with_embeddings)
        logger.info(f"[knowledge] chunk'lar Supabase'e yazıldı")

        final_doc = update_document_status(document_id, DocumentStatus.INDEXED)
        logger.info(f"[knowledge] döküman hazır: {document_id}")
        return final_doc or doc

    except Exception as e:
        logger.error(f"[knowledge] hata — adım bilinmiyor — {e}", exc_info=True)
        update_document_status(document_id, DocumentStatus.FAILED)
        raise e


def list_documents(source_module: str | None = None) -> list[dict]:
    return get_documents(source_module=source_module)


def fetch_document(document_id: str) -> dict | None:
    return get_document(document_id)


def remove_document(document_id: str, storage_path: str):
    delete_chunks_by_document_id(document_id)
    try:
        clean_path = storage_path.replace(f"{BUCKET}/", "", 1)
        delete_file(BUCKET, clean_path)
    except Exception:
        pass
    delete_document(document_id)


def reindex_document(document_id: str, storage_path: str, file_name: str):
    logger.info(f"[knowledge] yeniden indeksleme başladı: {document_id}")
    import tempfile, os
    from app.db.storage import download_file
    from app.modules.knowledge.summarizer import invalidate_summary_cache
    tmp_path = None
    try:
        update_document_status(document_id, DocumentStatus.PROCESSING)
        delete_chunks_by_document_id(document_id)
        invalidate_summary_cache(document_id)

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp_path = tmp.name
        clean_path = storage_path.replace(f"{BUCKET}/", "", 1)

        try:
            download_file(BUCKET, clean_path, tmp_path)
        except Exception as dl_err:
            err_str = str(dl_err)
            if "not_found" in err_str or "Object not found" in err_str or "404" in err_str:
                logger.warning(
                    f"[knowledge] dosya storage'da bulunamadı, kayıt failed yapılıyor: {document_id}"
                )
                update_document_status(document_id, DocumentStatus.FAILED)
                return
            raise

        with open(tmp_path, "rb") as f:
            file_bytes = f.read()

        text = load_pdf(file_bytes)
        raw_chunks = split_into_chunks(text)
        texts = [c["text"] for c in raw_chunks]
        embeddings = embed_texts(texts)
        chunks_with_embeddings = [
            {"text": c["text"], "embedding": embeddings[i]}
            for i, c in enumerate(raw_chunks)
        ]
        insert_chunks(document_id, chunks_with_embeddings)
        update_document_status(document_id, DocumentStatus.INDEXED)
        logger.info(f"[knowledge] yeniden indeksleme tamamlandı: {document_id}")
    except Exception as e:
        logger.error(f"[knowledge] yeniden indeksleme hatası: {document_id} — {e}")
        update_document_status(document_id, DocumentStatus.FAILED)
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
