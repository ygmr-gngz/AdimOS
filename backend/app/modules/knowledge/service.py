import logging
from app.db.repositories.documents_repo import create_document, update_document_status, get_documents, get_document
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


def list_documents() -> list[dict]:
    return get_documents()


def fetch_document(document_id: str) -> dict | None:
    return get_document(document_id)


def remove_document(document_id: str, storage_path: str):
    delete_chunks_by_document_id(document_id)
    delete_file(BUCKET, storage_path)
