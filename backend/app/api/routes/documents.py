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


def _log_upload_attempt(
    file_name: str,
    file_size: int,
    phase: str,
    error: str | None = None,
    doc_id: str | None = None,
) -> None:
    """Her yükleme denemesini notifications tablosuna yazar — başarısız denemeler de iz bırakır."""
    try:
        sb = get_supabase_client()
        status = "error" if error else "success"
        body = f"Aşama: {phase}" + (f" — Hata: {error[:200]}" if error else " — Başarılı")
        sb.table("notifications").insert({
            "type": "upload_attempt",
            "title": f"Yükleme: {file_name}",
            "body": body,
            "is_read": False,
            "status": status,
            "priority": "high" if error else "low",
            "details": {
                "file_name": file_name,
                "file_size": file_size,
                "phase": phase,
                "error": error,
                "doc_id": doc_id,
            },
        }).execute()
    except Exception as e:
        logger.debug(f"[documents] upload log yazılamadı: {e}")


def _sgs_pipeline_background(doc_id: str, file_bytes: bytes, pdf_name: str) -> None:
    """Bilgi Merkezi PDF'ini SGS soru çıkarım hattına besler (arka planda)."""
    from app.modules.knowledge.pdf_loader import load_pdf
    from app.modules.sgs.analyzer import analyze_sgs_pdf
    from app.db.repositories.sgs_repo import (
        create_analysis, find_analysis_by_pdf_name, update_analysis, parse_questions_by_ranges,
    )
    logger.info(f"[documents] SGS pipeline başladı: {doc_id} — {pdf_name}")
    try:
        existing = find_analysis_by_pdf_name(pdf_name)
        if existing:
            existing_q = existing.get("total_questions") or 0
            if existing_q > 0:
                logger.info(f"[documents] SGS analizi zaten mevcut ({existing_q} soru), atlanıyor: {pdf_name}")
                return
            logger.info(f"[documents] SGS analizi mevcut ama 0 soru — yeniden analiz deneniyor: {pdf_name}")

        text = load_pdf(file_bytes)
        if not text or len(text.strip()) < 100:
            logger.warning(
                f"[documents] SGS pipeline: PDF metni çıkarılamadı — "
                f"taranmış/görüntü PDF olabilir (OCR desteklenmiyor): {pdf_name} doc={doc_id}"
            )
            return

        result = analyze_sgs_pdf(text, pdf_name)
        if not result.get("total_questions"):
            logger.info(f"[documents] SGS pipeline: LLM soru bulamadı (format tanınmadı?): {pdf_name}")
            return

        sb = get_supabase_client()
        if existing:
            analysis_id = existing["id"]
            update_analysis(
                analysis_id,
                total_questions=result["total_questions"],
                subjects=result.get("subjects", []),
                questions=result.get("questions", []),
                video_plan=result.get("video_plan", []),
            )
            logger.info(f"[documents] SGS analizi güncellendi: analysis_id={analysis_id}")
        else:
            saved = create_analysis(
                pdf_name=result.get("pdf_name", pdf_name),
                total_questions=result["total_questions"],
                subjects=result.get("subjects", []),
                questions=result.get("questions", []),
                video_plan=result.get("video_plan", []),
            )
            if not saved:
                logger.error(f"[documents] SGS create_analysis başarısız: {pdf_name}")
                return
            analysis_id = saved["id"]

        sb.table("documents").update({"sgs_analysis_id": analysis_id}).eq("id", doc_id).execute()
        parse_questions_by_ranges(analysis_id=analysis_id)
        logger.info(f"[documents] SGS pipeline tamamlandı: {doc_id} — {result['total_questions']} soru")
    except Exception as e:
        logger.error(f"[documents] SGS pipeline hatası {doc_id}: {e}", exc_info=True)


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
    exclude_from_sgs: bool = Form(default=False),
    bg: BackgroundTasks = BackgroundTasks(),
):
    content = await file.read()
    file_name = file.filename or "upload.pdf"
    file_size = len(content)

    if file_size > _MAX_UPLOAD_BYTES:
        _log_upload_attempt(file_name, file_size, "boyut_kontrolu",
                            error=f"50 MB sınırı aşıldı ({file_size // (1024 * 1024)} MB)")
        raise HTTPException(
            status_code=413,
            detail=f"Dosya boyutu 50 MB sınırını aşıyor ({file_size // (1024 * 1024)} MB).",
        )
    mime_type = file.content_type or "application/pdf"

    # Türkçe karakter ve boşluk içeren dosya adlarını sanitize et
    safe_name = _SAFE_NAME_RE.sub('_', file_name)

    doc_id = None
    try:
        # AŞAMA 1 (hızlı — HTTP yanıtı bu kadarda biter):
        doc = create_document(safe_name, "", file_size, mime_type, source_module=source_module, exclude_from_sgs=exclude_from_sgs)
        doc_id = doc["id"]
        storage_path = f"{_BUCKET}/{doc_id}/{safe_name}"

        sb = get_supabase_client()
        sb.table("documents").update({"storage_path": storage_path}).eq("id", doc_id).execute()
        doc["storage_path"] = storage_path

        upload_file(_BUCKET, f"{doc_id}/{safe_name}", content)
    except Exception as e:
        _log_upload_attempt(file_name, file_size, "storage_yukleme", error=str(e), doc_id=doc_id)
        logger.error(f"[documents] yükleme hatası {file_name}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Dosya yüklenemedi: {str(e)[:200]}")

    _log_upload_attempt(file_name, file_size, "tamamlandi", doc_id=doc_id)

    # AŞAMA 2 (arka plan): metin çıkarma / embedding / indexleme
    bg.add_task(_index_background, doc_id, content)

    # AŞAMA 3 (arka plan): SGS soru çıkarımı — sadece PDF ve SGS dışında tutulmamışsa
    if (
        source_module != "sgs_academy"
        and not exclude_from_sgs
        and mime_type in ("application/pdf", "application/octet-stream")
    ):
        bg.add_task(_sgs_pipeline_background, doc_id, content, safe_name)

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

    sb = get_supabase_client()
    sb.table("documents").update({
        "file_size": len(content),
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
        .select("id, file_name, storage_path")
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
            verified += 1
        except Exception as e:
            err = str(e).lower()
            if "not_found" in err or "404" in err or "object not found" in err:
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
    """Tüm dokümanların storage'da mevcut olup olmadığını arka planda kontrol et."""
    bg.add_task(_run_storage_verification)
    return {"message": "Storage doğrulaması başlatıldı. İşlem tamamlandığında doküman listesini yenileyin."}


@router.get("/indexing-audit")
def indexing_audit():
    """
    Tüm dokümanlar için 5-aşamalı indeksleme zinciri denetimi.
    Aşamalar: yüklendi → metin çıkarıldı → chunk'landı → embedding → konu eşlendi
    """
    sb = get_supabase_client()

    # 1. Tüm dokümanları çek
    docs = sb.table("documents").select("id, file_name, status, source_module, created_at, file_size, storage_path").order("created_at", desc=True).limit(500).execute().data or []

    # 2. Chunk sayıları (doc_id → chunk_count, embedded_count)
    chunks_raw = sb.table("chunks").select("document_id, embedding", count="exact").limit(50000).execute().data or []
    chunk_count_map: dict[str, int] = {}
    embed_count_map: dict[str, int] = {}
    for c in chunks_raw:
        did = c["document_id"]
        chunk_count_map[did] = chunk_count_map.get(did, 0) + 1
        if c.get("embedding"):
            embed_count_map[did] = embed_count_map.get(did, 0) + 1

    # 3. Konu eşleme (doc_id → topic_count)
    sq_raw = sb.table("sgs_questions").select("document_id", count="exact").limit(50000).execute().data or []
    topic_map: dict[str, int] = {}
    for r in sq_raw:
        did = r.get("document_id")
        if did:
            topic_map[did] = topic_map.get(did, 0) + 1

    rows = []
    stalled_by_stage: dict[str, int] = {"metin_cikarmadi": 0, "chunk_yok": 0, "embedding_yok": 0, "konu_eslemedi": 0}

    for doc in docs:
        did = doc["id"]
        st = doc["status"]

        # Aşama belirle
        a1 = True   # DB'de kayıt var
        a2 = st not in ("uploaded",)  # PROCESSING veya ötesi = metin çıkarma girişildi
        a3 = chunk_count_map.get(did, 0) > 0
        a4 = embed_count_map.get(did, 0) > 0
        a5 = topic_map.get(did, 0) > 0

        # Hangi aşamada takılı?
        stalled = None
        if not a2 and st == "uploaded":
            stalled = "metin_cikarmadi"
            stalled_by_stage["metin_cikarmadi"] += 1
        elif not a3 and st not in ("uploaded", "processing"):
            stalled = "chunk_yok"
            stalled_by_stage["chunk_yok"] += 1
        elif a3 and not a4:
            stalled = "embedding_yok"
            stalled_by_stage["embedding_yok"] += 1

        rows.append({
            "id": did,
            "file_name": doc["file_name"],
            "status": st,
            "source_module": doc["source_module"],
            "created_at": doc["created_at"],
            "file_size": doc["file_size"],
            "has_storage_path": bool(doc.get("storage_path")),
            "stages": {
                "1_yuklendi":       a1,
                "2_metin_cikardi":  a2,
                "3_chunklandi":     a3,
                "4_embedding":      a4,
                "5_konu_eslendi":   a5,
            },
            "stage_score": sum([a1, a2, a3, a4, a5]),
            "stalled_at": stalled,
            "chunk_count": chunk_count_map.get(did, 0),
            "embedded_count": embed_count_map.get(did, 0),
            "topic_count": topic_map.get(did, 0),
        })

    complete   = [r for r in rows if r["stage_score"] == 5]
    incomplete = [r for r in rows if r["stage_score"] < 5]
    can_reindex = [r for r in incomplete if r["has_storage_path"] and r["status"] in ("uploaded", "failed", "indexed")]

    return {
        "total": len(rows),
        "complete_5_5": len(complete),
        "incomplete": len(incomplete),
        "can_reindex": len(can_reindex),
        "stalled_by_stage": stalled_by_stage,
        "documents": rows,
    }


@router.post("/backfill-indexing")
def backfill_indexing(bg: BackgroundTasks, dry_run: bool = True, limit: int = 20):
    """
    İndeksleme zinciri eksik olan dokümanları kaldığı aşamadan devam ettirerek tamamlar.
    dry_run=True (varsayılan): sadece sayım raporlar, hiçbir şeyi işlemez.
    dry_run=False: gerçekten başlatır (her doküman için ayrı bg task).
    """
    sb = get_supabase_client()

    # Eksik chunk'lı ama storage_path'i olan dokümanlar
    docs = (
        sb.table("documents")
        .select("id, file_name, status, storage_path, source_module")
        .in_("status", ["uploaded", "failed"])
        .limit(limit * 3)
        .execute().data or []
    )

    # Chunk'ı olanları çıkar
    chunk_docs_resp = sb.table("chunks").select("document_id").limit(50000).execute().data or []
    has_chunks = {r["document_id"] for r in chunk_docs_resp}

    needs_indexing = [
        d for d in docs
        if d["id"] not in has_chunks
        and d.get("storage_path")
        and d["storage_path"] not in ("", "sgs/")
        and not d.get("storage_path", "").startswith("sgs/")
    ][:limit]

    if dry_run:
        return {
            "dry_run": True,
            "would_reindex": len(needs_indexing),
            "documents": [
                {"id": d["id"], "file_name": d["file_name"], "status": d["status"]}
                for d in needs_indexing
            ],
            "note": "dry_run=false ile gerçek işlemi başlatın",
        }

    # Gerçek backfill — her doküman için reindex bg task
    launched = 0
    for doc in needs_indexing:
        try:
            bg.add_task(reindex_document, doc["id"], doc["storage_path"], doc["file_name"])
            launched += 1
            logger.info(f"[documents] backfill başlatıldı: {doc['id']} — {doc['file_name']}")
        except Exception as e:
            logger.warning(f"[documents] backfill task hatası {doc['id']}: {e}")

    return {
        "dry_run": False,
        "launched": launched,
        "total_eligible": len(needs_indexing),
        "note": "İşlemler arka planda çalışıyor — /indexing-audit ile durumu izleyin",
    }


@router.get("/upload-log")
def upload_log(limit: int = 50):
    """Son yükleme denemelerini göster (başarılı ve başarısız)."""
    sb = get_supabase_client()
    r = (
        sb.table("notifications")
        .select("id,title,body,status,priority,details,created_at")
        .eq("type", "upload_attempt")
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return r.data or []
