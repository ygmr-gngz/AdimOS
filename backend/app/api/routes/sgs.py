"""SGS çıkmış soru analizi ve video serisi üretim endpoint'leri."""
import logging
from fastapi import APIRouter, BackgroundTasks, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from app.modules.sgs.service import analyze_pdf_bytes, build_sgs_topic_video
from app.db.repositories.sgs_repo import (
    create_analysis, list_analyses, get_analysis, delete_analysis, update_question_subject,
    save_range, get_ranges, delete_range, get_all_questions,
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
):
    """SGS çıkmış soru PDF'ini analiz et → soru listesi + video serisi planı döndür."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Sadece PDF dosyası yüklenebilir")

    pdf_bytes = await file.read()
    if len(pdf_bytes) < 500:
        raise HTTPException(status_code=400, detail="PDF dosyası çok küçük veya boş")

    try:
        result = analyze_pdf_bytes(pdf_bytes, file.filename)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"[sgs] analiz hatası: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analiz başarısız: {e}")

    # Veritabanına kaydet
    try:
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
        logger.warning(f"[sgs] analiz kaydedilemedi (tablo yok olabilir): {db_err}")
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
    try:
        from app.db.repositories.brand_repo import configure_video_watermark
        configure_video_watermark("sgs_topic_video")
        logger.info(f"[sgs] konu videosu başladı id={content_id} topic={video_plan_item.get('topic')}")
        result = build_sgs_topic_video(video_plan_item, questions)
        updates = {"status": "pending_approval"}
        for field in ("video_path", "title", "script", "audio_base64"):
            if result.get(field):
                updates["video_url" if field == "video_path" else field] = result[field]
        update_content(content_id, updates)
        logger.info(f"[sgs] konu videosu tamamlandı id={content_id}")
    except Exception as e:
        logger.error(f"[sgs] konu video hatası id={content_id}: {e}", exc_info=True)
        update_content(content_id, {"status": "error", "error_detail": str(e)[:300]})


@router.post("/generate-topic-video")
def generate_topic_video(req: TopicVideoRequest, bg: BackgroundTasks):
    """17: Ders + konu için tüm analizlerden soru topla ve video üret."""
    questions = get_all_questions(lesson_name=req.lesson, year=req.year)
    topic_questions = [q for q in questions if q.get("topic", "") == req.topic]

    if not topic_questions:
        topic_questions = [q for q in questions if req.topic.lower() in q.get("topic", "").lower()]

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