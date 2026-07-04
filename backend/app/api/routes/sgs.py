"""SGS çıkmış soru analizi ve video serisi üretim endpoint'leri."""
import logging
from typing import Optional, List
from fastapi import APIRouter, BackgroundTasks, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from app.modules.sgs.service import analyze_pdf_bytes, build_sgs_topic_video
from app.db.repositories.sgs_repo import (
    create_analysis, find_analysis_by_pdf_name, update_analysis,
    list_analyses, get_analysis, delete_analysis, update_question_subject,
    save_range, get_ranges, delete_range, get_all_questions,
    get_questions_by_ranges, bulk_link_ranges_to_analysis,
    get_questions_for_topic, update_question_in_sgs_questions, get_topic_detail,
    get_areas_from_sgs_questions, get_lesson_topics_from_sgs_questions, reclassify_all_questions,
    parse_all_unparsed_analyses,
)
from app.config.sgs_groups import SGS_LESSON_GROUPS, get_lessons_for_group
from app.db.repositories.generated_contents_repo import (
    create_content, update_content,
)
from app.db.repositories.documents_repo import create_document

logger = logging.getLogger(__name__)
router = APIRouter()


# ── PDF Analiz ────────────────────────────────────────────────

@router.post("/analyze")
async def analyze_pdf(
    file: UploadFile = File(...),
    document_type: str = Form("Çıkmış Sorular"),
    year: str = Form(""),
    semester: str = Form(""),
    force: bool = Form(False),
):
    """SGS çıkmış soru PDF'ini analiz et → soru listesi + video serisi planı döndür.

    force=True: aynı isimde analiz zaten varsa üzerine yaz (re-analiz için).
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Sadece PDF dosyası yüklenebilir")

    pdf_bytes = await file.read()
    if len(pdf_bytes) < 500:
        raise HTTPException(status_code=400, detail="PDF dosyası çok küçük veya boş")
    if len(pdf_bytes) > 50 * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"PDF boyutu 50 MB sınırını aşıyor ({len(pdf_bytes) // (1024 * 1024)} MB).")

    # Aynı dosya adıyla daha önce yüklenmiş analiz varsa — force=False ise döndür
    existing = find_analysis_by_pdf_name(file.filename)
    if existing and not force:
        logger.info(f"[sgs] PDF zaten mevcut, tekrar analiz edilmiyor: {file.filename}")
        return {
            **existing,
            "analysis_id": existing["id"],
            "already_exists": True,
        }

    try:
        result = analyze_pdf_bytes(pdf_bytes, file.filename)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"[sgs] analiz hatası: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analiz başarısız: {e}")

    # Veritabanına kaydet (force=True → mevcut analizi güncelle)
    try:
        if existing and force:
            saved = update_analysis(
                existing["id"],
                total_questions=result.get("total_questions", 0),
                subjects=result.get("subjects", []),
                questions=result.get("questions", []),
                video_plan=result.get("video_plan", []),
                document_type=document_type or existing.get("document_type") or "Çıkmış Sorular",
                year=year or existing.get("year") or "",
                semester=semester or existing.get("semester") or "",
            )
            if saved:
                result["analysis_id"] = saved["id"]
                result["document_type"] = saved.get("document_type")
                result["year"] = saved.get("year")
                result["semester"] = saved.get("semester")
                result["force_updated"] = True
                logger.info(f"[sgs] force re-analiz güncellendi: {file.filename}, {result.get('total_questions', 0)} soru")
        else:
            saved = create_analysis(
                pdf_name=result.get("pdf_name", file.filename),
                total_questions=result.get("total_questions", 0),
                subjects=result.get("subjects", []),
                questions=result.get("questions", []),
                video_plan=result.get("video_plan", []),
                document_type=document_type or "Çıkmış Sorular",
                year=year or "",
                semester=semester or "",
            )
            if saved:
                analysis_id = saved.get("id")
                result["analysis_id"] = analysis_id
                result["document_type"] = saved.get("document_type")
                result["year"] = saved.get("year")
                result["semester"] = saved.get("semester")
                try:
                    create_document(
                        file_name=result.get("pdf_name", file.filename),
                        storage_path=f"sgs/{result.get('pdf_name', file.filename)}",
                        file_size=len(pdf_bytes),
                        mime_type="application/pdf",
                        source_module="sgs_academy",
                        sgs_analysis_id=analysis_id,
                    )
                except Exception as doc_err:
                    logger.warning(f"[sgs] documents tablosuna kayıt açılamadı: {doc_err}")
    except Exception as db_err:
        logger.warning(f"[sgs] analiz kaydedilemedi: {db_err}")
        result["analysis_id"] = None

    return result


# ── Video Üretim ──────────────────────────────────────────────

class VideoGenerateRequest(BaseModel):
    analysis_id: str
    video_plan_index: int   # video_plan listesindeki sıra no (0-based)


def _bg_sgs_video(content_id: str, video_plan_item: dict, questions: list):
    try:
        logger.info(f"[sgs] video üretimi başladı id={content_id}")
        result = build_sgs_topic_video(video_plan_item, questions)
        updates = {"status": "pending_approval"}
        if result.get("video_path"):
            updates["video_url"] = result["video_path"]
        for field in ("title", "script", "audio_base64"):
            if result.get(field):
                updates[field] = result[field]
        update_content(content_id, updates)
        logger.info(f"[sgs] video tamamlandı id={content_id}")
    except Exception as e:
        logger.error(f"[sgs] video hatası id={content_id}: {e}", exc_info=True)
        update_content(content_id, {"status": "error", "error_detail": str(e)[:300]})


@router.post("/generate-video")
def generate_sgs_video(req: VideoGenerateRequest, bg: BackgroundTasks):
    """Bir video planı öğesi için video üretimini arka planda başlat."""
    analysis = get_analysis(req.analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analiz bulunamadı")

    video_plan = analysis.get("video_plan", [])
    if req.video_plan_index >= len(video_plan):
        raise HTTPException(status_code=400, detail=f"video_plan_index geçersiz ({req.video_plan_index})")

    plan_item = video_plan[req.video_plan_index]
    questions = analysis.get("questions", [])

    title = plan_item.get("title", "SGS Video")
    row = create_content(title, "sgs_topic_video")

    bg.add_task(_bg_sgs_video, row["id"], plan_item, questions)
    return {
        "content_id": row["id"],
        "status": "generating",
        "title": title,
        "question_count": len(plan_item.get("question_ids", [])),
    }


# ── Analiz Listesi / Detay / Silme ────────────────────────────

@router.get("/analyses")
def list_sgs_analyses():
    try:
        return list_analyses()
    except Exception as e:
        logger.warning(f"[sgs] analiz listesi alınamadı: {e}")
        return []


@router.get("/analyses/{analysis_id}")
def get_sgs_analysis(analysis_id: str):
    analysis = get_analysis(analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analiz bulunamadı")
    return analysis


@router.delete("/analyses/{analysis_id}")
def delete_sgs_analysis(analysis_id: str):
    try:
        delete_analysis(analysis_id)
    except Exception:
        pass
    return {"message": "Analiz silindi"}


class QuestionLessonUpdate(BaseModel):
    new_subject: str


@router.patch("/analyses/{analysis_id}/question/{question_id}")
def update_question_lesson(analysis_id: str, question_id: int, body: QuestionLessonUpdate):
    """Bir sorunun dersini manuel düzelt."""
    from app.modules.sgs.analyzer import SGS_LESSONS
    if body.new_subject not in SGS_LESSONS and body.new_subject != "Belirsiz":
        raise HTTPException(status_code=400, detail=f"Geçersiz ders: {body.new_subject}")
    updated = update_question_subject(analysis_id, question_id, body.new_subject)
    if not updated:
        raise HTTPException(status_code=404, detail="Analiz bulunamadı")
    return {"message": "Ders güncellendi", "question_id": question_id, "new_subject": body.new_subject}

class RangeCreateRequest(BaseModel):
    document_name:str
    document_id: str | None = None
    start_question_no:int
    end_question_no:int
    lesson_name:str
    notes: str | None = None

@router.post("/ranges")
def create_range(body: RangeCreateRequest):
    result = save_range(
        body.document_name, body.start_question_no, body.end_question_no,
        body.lesson_name, body.notes, body.document_id
    )
    return result


@router.get("/ranges")
def list_ranges(document_name: str | None = None):
    return get_ranges(document_name)


@router.delete("/ranges/{range_id}")
def remove_range(range_id: str):
    delete_range(range_id)
    return {"message": "Aralık silindi"}


class BulkLinkRequest(BaseModel):
    analysis_id: str


@router.post("/ranges/bulk-link")
def bulk_link_ranges(body: BulkLinkRequest):
    """document_id boş olan tüm aralıkları seçilen analize bağla."""
    result = bulk_link_ranges_to_analysis(body.analysis_id)
    if result.get("error"):
        raise HTTPException(status_code=404, detail=result["error"])
    return result

class ParseRequest(BaseModel):
    analysis_id: str
    range_ids: Optional[List[str]] = None
    document_id: Optional[str] = None


@router.post("/questions/parse-by-ranges")
def parse_questions(body: ParseRequest):
    if not body.analysis_id or not body.analysis_id.strip():
        raise HTTPException(status_code=400, detail="analysis_id boş gönderilemez. Frontend'den analysis_id eksik gönderilmiş.")

    if body.range_ids is not None and len(body.range_ids) == 0:
        raise HTTPException(
            status_code=400,
            detail="range_ids boş liste geldi. Önce 'Aralıkları PDF'e Bağla' yapın veya range_ids göndermeden tekrar deneyin."
        )

    from app.db.repositories.sgs_repo import parse_questions_by_ranges
    result = parse_questions_by_ranges(
        analysis_id=body.analysis_id.strip(),
        range_ids=body.range_ids,
        document_id=body.document_id or body.analysis_id.strip(),
    )

    if result.get("error"):
        logger.warning(f"[parse endpoint] hata: {result['error']}")
        raise HTTPException(status_code=400, detail=result["error"])

    logger.info(f"[parse endpoint] başarı: {result.get('questions_created', 0)} soru, {result.get('failed_count', 0)} başarısız")
    return {
        "success": True,
        "parsed_count": result.get("questions_created", 0),
        "failed_count": result.get("failed_count", 0),
        "questions_created": result.get("questions_created", 0),
        "lessons": result.get("lessons", []),
        "analysis_id": result.get("analysis_id"),
        "message": f"{result.get('questions_created', 0)} soru başarıyla parse edildi",
    }



# ── 15-16: Alan / Ders Bazlı Konu Frekans Analizi ────────────

from fastapi import Query as Q
from collections import Counter

@router.get("/topic-analysis")
def topic_analysis(
    lesson: str | None = Q(None, description="Tek ders adı"),
    group: str | None = Q(None, description="Alan adı: Hukuk, Muhasebe, Finans, Genel Dersler"),
    year: str | None = Q(None, description="Yıl filtresi (örn: 2024)"),
):
    """15-16: Ders veya alan bazlı soru frekans analizi."""
    group_lessons: list[str] | None = None
    if group:
        group_lessons = get_lessons_for_group(group)
        if not group_lessons:
            raise HTTPException(status_code=400, detail=f"Geçersiz alan: {group}. Geçerli alanlar: {list(SGS_LESSON_GROUPS.keys())}")

    questions = get_all_questions(lesson_name=lesson, group_lessons=group_lessons, year=year)

    topic_counts = Counter(q.get("topic", "Belirsiz") for q in questions)
    lesson_counts = Counter(q.get("subject", "Belirsiz") for q in questions)
    year_counts = Counter(q.get("source_year") or q.get("year", "?") for q in questions)

    top_topics = [{"topic": t, "count": c} for t, c in topic_counts.most_common(20)]

    return {
        "lesson": lesson,
        "group": group,
        "year_filter": year,
        "total": len(questions),
        "top_topics": top_topics,
        "lesson_breakdown": [{"lesson": l, "count": c} for l, c in lesson_counts.most_common()],
        "year_breakdown": [{"year": y, "count": c} for y, c in sorted(year_counts.items())],
        "sample_questions": questions[:30],
    }


# ── 17: Konu Analizinden Video Üretimi ───────────────────────

class TopicVideoRequest(BaseModel):
    lesson: str
    topic: str
    year: str | None = None
    max_questions: int = 5


def _bg_topic_video(content_id: str, video_plan_item: dict, questions: list):
    from app.api.routes.notifications import push_notification
    topic = video_plan_item.get("topic", "")
    subject = video_plan_item.get("subject", "")
    try:
        from app.db.repositories.brand_repo import configure_video_watermark
        configure_video_watermark("sgs_topic_video")
        logger.info(f"[sgs] konu videosu başladı id={content_id} topic={topic}")
        result = build_sgs_topic_video(video_plan_item, questions)
        updates = {"status": "pending_approval"}
        for field in ("video_path", "title", "script", "audio_base64"):
            if result.get(field):
                updates["video_url" if field == "video_path" else field] = result[field]
        update_content(content_id, updates)
        push_notification(
            "content_ready",
            f"SGS videosu hazır: {topic}",
            status="success",
            message=f"{subject} — {topic} konusu çözüm videosu oluşturuldu. Onay bekliyor.",
            details={"content_id": content_id, "topic": topic, "subject": subject,
                     "question_count": len(questions), "video_type": "sgs_topic_video"},
            related_entity_type="content", related_entity_id=content_id,
            action_url="/automation",
        )
        logger.info(f"[sgs] konu videosu tamamlandı id={content_id}")
    except Exception as e:
        logger.error(f"[sgs] konu video hatası id={content_id}: {e}", exc_info=True)
        update_content(content_id, {"status": "error", "error_detail": str(e)[:300]})
        push_notification(
            "content_failed",
            f"SGS videosu üretilemedi: {topic}",
            status="error",
            message=str(e)[:200],
            details={"content_id": content_id, "topic": topic},
            related_entity_type="content", related_entity_id=content_id,
            action_url="/automation",
        )


@router.post("/generate-topic-video")
def generate_topic_video(req: TopicVideoRequest, bg: BackgroundTasks):
    """17: Ders + konu için soru topla (sgs_questions öncelikli) ve video üret."""
    # 1. sgs_questions tablosu — en doğru sınıflandırma, tam soru detayı
    topic_questions = get_questions_for_topic(topic=req.topic, lesson_name=req.lesson, limit=req.max_questions * 3)

    # 2. Case insensitive fallback (konu adı büyük/küçük harf farkı)
    if not topic_questions:
        topic_questions = get_questions_for_topic(topic=req.topic.lower(), lesson_name=req.lesson, limit=req.max_questions * 3)

    # 3. Aralık tablosu (eski yol)
    if not topic_questions:
        questions = get_questions_by_ranges(lesson_name=req.lesson, year=req.year)
        topic_questions = [q for q in questions if req.topic.lower() in (q.get("topic") or "").lower()]

    # 4. JSONB fallback
    if not topic_questions:
        questions = get_all_questions(lesson_name=req.lesson, year=req.year)
        topic_questions = [q for q in questions if req.topic.lower() in (q.get("topic") or "").lower()]

    if not topic_questions:
        raise HTTPException(
            status_code=404,
            detail=f"'{req.topic}' konusunda soru bulunamadı. Ders: {req.lesson}"
        )

    selected = topic_questions[:req.max_questions]
    q_ids = [q["id"] for q in selected]

    title = f"SGS {req.lesson}: {req.topic} Çıkmış Sorular"
    video_plan_item = {
        "title": title,
        "topic": req.topic,
        "subject": req.lesson,
        "question_ids": q_ids,
        "estimated_duration": f"{len(selected) * 2}-{len(selected) * 3} dakika",
        "description": f"{req.lesson} dersinden {req.topic} konusunun çıkmış sorularının çözümü.",
    }

    row = create_content(title, "sgs_topic_video")
    bg.add_task(_bg_topic_video, row["id"], video_plan_item, selected)

    return {
        "content_id": row["id"],
        "status": "generating",
        "title": title,
        "question_count": len(selected),
        "topic": req.topic,
        "lesson": req.lesson,
    }


# ── 18+: Alan Bazlı Analiz (Aralık Öncelikli) ────────────────

@router.get("/areas")
def list_areas(year: str | None = Q(None)):
    """Alan bazlı soru özeti — sgs_questions tablosu tek kaynak."""
    return {"areas": get_areas_from_sgs_questions(year=year)}


@router.get("/areas/{area_name}/topic-analysis")
def area_topic_analysis(area_name: str, year: str | None = Q(None)):
    """Alan bazlı konu frekans analizi — aralık öncelikli, yoksa AI'ya dön."""
    group_lessons = get_lessons_for_group(area_name)
    if not group_lessons:
        raise HTTPException(400, f"Geçersiz alan: {area_name}")

    questions = get_questions_by_ranges(group_lessons=group_lessons, year=year)
    data_source = "ranges"
    if not questions:
        questions = get_all_questions(group_lessons=group_lessons, year=year)
        data_source = "ai"

    topic_counts = Counter(q.get("topic", "Belirsiz") for q in questions)
    lesson_counts = Counter(q.get("subject", "Belirsiz") for q in questions)
    year_counts = Counter(q.get("source_year") or q.get("year", "?") for q in questions)

    return {
        "area": area_name,
        "total": len(questions),
        "top_topics": [{"topic": t, "count": c} for t, c in topic_counts.most_common(20)],
        "lesson_breakdown": [{"lesson": l, "count": c} for l, c in lesson_counts.most_common()],
        "year_breakdown": [{"year": y, "count": c} for y, c in sorted(year_counts.items())],
        "data_source": data_source,
    }


@router.get("/lessons/{lesson_name}/topic-analysis")
def lesson_topic_analysis(lesson_name: str, year: str | None = Q(None)):
    """Ders bazlı konu analizi — sgs_questions tablosu tek kaynak."""
    return get_lesson_topics_from_sgs_questions(lesson_name=lesson_name, year=year)


# ── Konu Detay ────────────────────────────────────────────────

@router.get("/topic-detail")
def topic_detail(
    topic: str = Q(..., description="Konu adı"),
    lesson: str | None = Q(None, description="Ders adı (opsiyonel)"),
):
    """Belirli bir konu için toplam soru, yıl dağılımı ve çıkma oranı."""
    return get_topic_detail(topic=topic, lesson_name=lesson)


# ── Soru Listesi (konu/ders bazlı, tam detay) ─────────────────

@router.get("/questions")
def list_questions_by_topic(
    topic: str | None = Q(None, description="Konu adı"),
    lesson: str | None = Q(None, description="Ders adı"),
):
    """Konu ve ders bazlı soru listesi — tam soru metni, şıklar, cevap."""
    if not topic and not lesson:
        return {"questions": [], "total": 0}
    questions = get_questions_for_topic(topic=topic or "", lesson_name=lesson)
    return {"questions": questions, "total": len(questions)}


# ── Soru Düzeltme (ders / konu) ───────────────────────────────

class QuestionUpdateRequest(BaseModel):
    lesson_name: Optional[str] = None
    topic: Optional[str] = None


@router.patch("/questions/{question_id}")
def update_question(question_id: int, body: QuestionUpdateRequest):
    """Bir sorunun dersini veya konusunu manuel düzelt (sgs_questions tablosu)."""
    if not body.lesson_name and not body.topic:
        raise HTTPException(status_code=400, detail="lesson_name veya topic gerekli")
    success = update_question_in_sgs_questions(
        question_number=question_id,
        lesson_name=body.lesson_name,
        topic=body.topic,
    )
    if not success:
        raise HTTPException(status_code=404, detail=f"Soru bulunamadı (question_number={question_id})")
    return {"message": "Soru güncellendi", "question_id": question_id}


# ── Yeniden Sınıflandırma ─────────────────────────────────────

@router.post("/questions/reclassify")
def reclassify_questions():
    """sgs_questions tablosundaki tüm sorulara TOPIC_LESSON_MAP uygula.
    Yanlış ders atamalı satırları düzeltir ve rapor döner.
    """
    result = reclassify_all_questions()
    return result


@router.post("/questions/parse-all")
def parse_all_analyses():
    """sgs_questions'ta satırı olmayan tüm analizleri AI subject ile otomatik parse eder.
    Önceden yüklenmiş ama parse edilmemiş PDF'ler için çalıştırılır.
    """
    result = parse_all_unparsed_analyses()
    return result


# ── Veritabanı Durum Analizi ──────────────────────────────────

@router.get("/admin/db-stats")
def get_db_stats():
    """Veritabanı durum analizi: ders/konu dağılımı, yanlış sınıflandırma tespiti."""
    from collections import Counter
    from app.db.supabase import get_supabase_client as _get_sb

    supabase = _get_sb()

    # sgs_analyses tablosu — questions dahil tek sorguda (N+1 önleme)
    analyses_resp = supabase.table("sgs_analyses").select("id, pdf_name, year, total_questions, questions").order("created_at", desc=True).execute()
    all_analyses = analyses_resp.data or []
    analyses = [{"id": a["id"], "pdf_name": a["pdf_name"], "year": a.get("year"), "total_questions": a["total_questions"]} for a in all_analyses]

    # sgs_question_ranges tablosu
    ranges_resp = supabase.table("sgs_question_ranges").select("lesson_name, start_question_no, end_question_no, document_name").execute()
    ranges = ranges_resp.data or []
    range_lesson_counts = Counter(r["lesson_name"] for r in ranges)

    # sgs_questions tablosu — ders/konu dağılımı
    sq_resp = supabase.table("sgs_questions").select("lesson_name, lesson_group, topic").execute()
    sq_rows = sq_resp.data or []
    sq_by_lesson: dict = {}
    for row in sq_rows:
        lesson = row.get("lesson_name", "?")
        topic = row.get("topic") or "?"
        if lesson not in sq_by_lesson:
            sq_by_lesson[lesson] = Counter()
        sq_by_lesson[lesson][topic] += 1

    # sgs_analyses.questions JSONB — AI sınıflandırma dağılımı (tek sorguda)
    ai_by_lesson: dict = {}
    total_ai_q = 0
    for a in all_analyses:
        questions = a.get("questions") or []
        total_ai_q += len(questions)
        for q in questions:
            subj = q.get("subject", "Belirsiz")
            topic = q.get("topic", "?")
            if subj not in ai_by_lesson:
                ai_by_lesson[subj] = Counter()
            ai_by_lesson[subj][topic] += 1

    # TOPIC_LESSON_MAP ile yanlış sınıflandırma tespiti
    from app.config.sgs_groups import SGS_LESSON_GROUPS as _GROUPS
    all_lessons_set = set(l for lessons in _GROUPS.values() for l in lessons)

    suspicious: list = []
    for lesson, topic_counter in ai_by_lesson.items():
        for topic, cnt in topic_counter.most_common(5):
            # Basit kural: eğer topic başka bir ders adıyla aynıysa şüpheli
            if topic in all_lessons_set and topic != lesson:
                suspicious.append({"lesson": lesson, "topic_equals_lesson": topic, "count": cnt})

    return {
        "summary": {
            "analyses_count": len(analyses),
            "ranges_count": len(ranges),
            "sgs_questions_table_rows": len(sq_rows),
            "ai_classified_questions": total_ai_q,
        },
        "analyses": [{"pdf": a["pdf_name"], "year": a.get("year"), "total": a["total_questions"]} for a in analyses],
        "ranges_per_lesson": dict(range_lesson_counts.most_common()),
        "sgs_questions_table_topics_per_lesson": {
            lesson: dict(topics.most_common(15))
            for lesson, topics in sorted(sq_by_lesson.items())
        },
        "ai_topics_per_lesson": {
            lesson: dict(topics.most_common(15))
            for lesson, topics in sorted(ai_by_lesson.items())
        },
        "suspicious_topic_lesson_mismatches": suspicious,
    }