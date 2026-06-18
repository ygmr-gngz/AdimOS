"""SGS çıkmış soru analizi ve video serisi üretim endpoint'leri."""
import logging
from fastapi import APIRouter, BackgroundTasks, HTTPException, UploadFile, File
from pydantic import BaseModel

from app.modules.sgs.service import analyze_pdf_bytes, build_sgs_topic_video
from app.db.repositories.sgs_repo import (
    create_analysis, list_analyses, get_analysis, delete_analysis,
)
from app.db.repositories.generated_contents_repo import (
    create_content, update_content,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# ── PDF Analiz ────────────────────────────────────────────────

@router.post("/analyze")
async def analyze_pdf(file: UploadFile = File(...)):
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
        )
        if saved:
            result["analysis_id"] = saved.get("id")
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
