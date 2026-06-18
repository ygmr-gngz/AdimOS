import logging
import httpx
from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from app.modules.content.service import (
    create_normal_video, create_short_video, create_post,
    create_question_solution_video, create_topic_explanation_video,
    publish_to_youtube, publish_to_instagram,
)
from app.db.repositories.generated_contents_repo import (
    create_content, update_content, get_content, list_contents,
    delete_content as db_delete, delete_orphan_contents,
)
from app.modules.content.cleanup import (
    run_full_cleanup, run_health_check, safe_delete_content,
)

logger = logging.getLogger(__name__)
router = APIRouter()


class ContentRequest(BaseModel):
    topic: str
    duration_minutes: int = 5
    question_text: str = ""
    category: str = "smmm"  # smmm | sgs | genel


class ApproveRequest(BaseModel):
    action: str  # "approve" | "reject"
    notes: str = ""


class EditRequest(BaseModel):
    message: str


def _background_generate(content_id: str, fn, *args):
    try:
        logger.info(f"[content] üretim başladı id={content_id}")
        result = fn(*args)
        updates = {"status": "pending_approval"}
        for field in ("video_path", "audio_path", "image_path", "title", "caption", "script", "audio_base64"):
            if result.get(field):
                db_field = "video_url" if field == "video_path" else (
                    "audio_url" if field == "audio_path" else (
                    "image_url" if field == "image_path" else field))
                updates[db_field] = result[field]
        update_content(content_id, updates)
        logger.info(f"[content] üretim tamamlandı id={content_id}")
    except Exception as e:
        logger.error(f"[content] üretim hatası id={content_id} hata={e}", exc_info=True)
        update_content(content_id, {
            "status": "error",
            "error_detail": str(e)[:300],
        })


# ── Generate endpoints

@router.post("/video/generate")
def generate_video(req: ContentRequest, bg: BackgroundTasks):
    row = create_content(req.topic, "video")
    bg.add_task(_background_generate, row["id"], create_normal_video, req.topic, req.duration_minutes, req.category)
    return {"content_id": row["id"], "status": "generating"}


@router.post("/short/generate")
def generate_short(req: ContentRequest, bg: BackgroundTasks):
    row = create_content(req.topic, "short")
    bg.add_task(_background_generate, row["id"], create_short_video, req.topic, req.category)
    return {"content_id": row["id"], "status": "generating"}


@router.post("/post/generate")
def generate_post_endpoint(req: ContentRequest, bg: BackgroundTasks):
    row = create_content(req.topic, "post")
    bg.add_task(_background_generate, row["id"], create_post, req.topic)
    return {"content_id": row["id"], "status": "generating"}


@router.post("/question-solution/generate")
def generate_question_solution(req: ContentRequest, bg: BackgroundTasks):
    row = create_content(req.topic, "question_solution")
    bg.add_task(_background_generate, row["id"], create_question_solution_video, req.topic, req.question_text, req.category)
    return {"content_id": row["id"], "status": "generating"}


@router.post("/topic-explanation/generate")
def generate_topic_explanation(req: ContentRequest, bg: BackgroundTasks):
    row = create_content(req.topic, "topic_explanation")
    bg.add_task(_background_generate, row["id"], create_topic_explanation_video, req.topic, req.category)
    return {"content_id": row["id"], "status": "generating"}


# ── List / Get

@router.get("")
def list_content():
    return list_contents()


@router.get("/{content_id}")
def get_content_by_id(content_id: str):
    item = get_content(content_id)
    if not item:
        raise HTTPException(status_code=404, detail="İçerik bulunamadı")
    return item


# ── Approve / Reject

@router.patch("/{content_id}/approve")
def approve_content(content_id: str, req: ApproveRequest):
    item = get_content(content_id)
    if not item:
        raise HTTPException(status_code=404, detail="İçerik bulunamadı")
    new_status = "approved" if req.action == "approve" else "rejected"
    updates: dict = {"status": new_status}
    if req.notes:
        updates["approval_notes"] = req.notes
    return update_content(content_id, updates)


# ── Edit (doğal dil ile yeniden üretim)

@router.post("/{content_id}/edit")
def edit_content(content_id: str, req: EditRequest, bg: BackgroundTasks):
    """Doğal dil komutu ile içeriği analiz et ve arka planda yeniden üret."""
    from app.modules.content.editor import build_edit_plan

    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Düzenleme mesajı boş olamaz")

    item = get_content(content_id)
    if not item:
        raise HTTPException(status_code=404, detail="İçerik bulunamadı")

    plan = build_edit_plan(item, req.message)
    enhanced_topic = plan.get("enhanced_topic") or (
        (item.get("topic") or item.get("title", "")) + f". {req.message}"
    )
    content_type = item.get("type", "video")
    category = item.get("category", "smmm")

    fn_map = {
        "video": (create_normal_video, (enhanced_topic, 5, category)),
        "short": (create_short_video, (enhanced_topic, category)),
        "post": (create_post, (enhanced_topic,)),
        "question_solution": (create_question_solution_video, (enhanced_topic, "", category)),
        "topic_explanation": (create_topic_explanation_video, (enhanced_topic, category)),
        "sgs_topic_video": (create_topic_explanation_video, (enhanced_topic, "sgs")),
    }
    fn, args = fn_map.get(content_type, (create_normal_video, (enhanced_topic, 5, "smmm")))

    update_content(content_id, {
        "status": "generating",
        "video_url": None,
        "audio_base64": None,
        "error_detail": None,
    })

    bg.add_task(_background_generate, content_id, fn, *args)

    return {
        "content_id": content_id,
        "status": "regenerating",
        "changes_summary": plan.get("changes_summary", [req.message]),
        "explanation": plan.get("explanation", ""),
    }


# ── Validate (video URL erişilebilir mi?)

@router.post("/{content_id}/validate")
async def validate_content(content_id: str):
    item = get_content(content_id)
    if not item:
        raise HTTPException(status_code=404, detail="İçerik bulunamadı")

    video_url = item.get("video_url") or item.get("image_url") or ""

    if not video_url or not video_url.startswith("http"):
        return {
            "valid": False, "playable": False,
            "reason": "Video URL bulunamadı veya geçersiz",
            "storageExists": False,
        }

    try:
        async with httpx.AsyncClient(timeout=8) as client:
            resp = await client.head(video_url)
            ok = resp.status_code < 400
            size = int(resp.headers.get("content-length", 0))
            content_type = resp.headers.get("content-type", "")
            playable = ok and size > 1000 and ("video" in content_type or "octet" in content_type or video_url.endswith(".mp4"))
            return {
                "valid": ok,
                "playable": playable,
                "storageExists": ok,
                "size_bytes": size,
                "content_type": content_type,
                "reason": None if ok else f"HTTP {resp.status_code}",
            }
    except Exception as e:
        return {
            "valid": False, "playable": False,
            "storageExists": False,
            "reason": str(e)[:120],
        }


# ── Publish

@router.post("/{content_id}/publish")
def publish_content_unified(content_id: str):
    item = get_content(content_id)
    if not item:
        raise HTTPException(status_code=404, detail="İçerik bulunamadı")
    content_type = item.get("type", "video")
    if content_type in ("video", "short", "question_solution", "topic_explanation"):
        result = publish_to_youtube(item)
        platform = "youtube"
    else:
        result = publish_to_instagram(item)
        platform = "instagram"
    update_content(content_id, {"status": "published"})
    return {"content_id": content_id, "platform": platform, "status": "published", **result}


@router.post("/{content_id}/publish/youtube")
def publish_youtube(content_id: str):
    item = get_content(content_id)
    if not item:
        raise HTTPException(status_code=404, detail="İçerik bulunamadı")
    result = publish_to_youtube(item)
    update_content(content_id, {"status": "published"})
    return result


@router.post("/{content_id}/publish/instagram")
def publish_instagram(content_id: str):
    item = get_content(content_id)
    if not item:
        raise HTTPException(status_code=404, detail="İçerik bulunamadı")
    result = publish_to_instagram(item)
    update_content(content_id, {"status": "published"})
    return result


# ── Retry failed content

@router.post("/{content_id}/retry")
def retry_content(content_id: str, bg: BackgroundTasks):
    """Başarısız içeriği aynı konu ile yeniden üret."""
    item = get_content(content_id)
    if not item:
        raise HTTPException(status_code=404, detail="İçerik bulunamadı")
    if item.get("status") not in ("error", "failed", "corrupted", "rejected"):
        raise HTTPException(status_code=400, detail="Sadece hatalı içerikler yeniden üretilebilir")

    topic = item.get("topic") or item.get("title", "")
    content_type = item.get("type", "video")
    category = item.get("category", "smmm")

    fn_map = {
        "video": (create_normal_video, (topic, 5, category)),
        "short": (create_short_video, (topic, category)),
        "post": (create_post, (topic,)),
        "question_solution": (create_question_solution_video, (topic, "", category)),
        "topic_explanation": (create_topic_explanation_video, (topic, category)),
        "sgs_topic_video": (create_topic_explanation_video, (topic, "sgs")),
    }
    fn, args = fn_map.get(content_type, (create_normal_video, (topic, 5, "smmm")))

    update_content(content_id, {
        "status": "generating",
        "error_detail": None,
        "video_url": None,
        "audio_base64": None,
    })
    bg.add_task(_background_generate, content_id, fn, *args)
    return {"content_id": content_id, "status": "retrying"}


# ── Archive

@router.patch("/{content_id}/archive")
def archive_content(content_id: str):
    """İçeriği silmek yerine arşivle."""
    item = get_content(content_id)
    if not item:
        raise HTTPException(status_code=404, detail="İçerik bulunamadı")
    return update_content(content_id, {"status": "archived"})


# ── Health check + Full cleanup

@router.post("/health-check")
def health_check():
    """Sorunlu içerikleri tespit edip 'corrupted' olarak işaretle."""
    result = run_health_check()
    return result


@router.post("/cleanup")
def full_cleanup():
    """Tam sistem temizliği — hatalı, yetim, takılı içerikleri sil."""
    result = run_full_cleanup()
    return result


# ── Legacy orphan (backwards compat)

@router.delete("/orphan")
def cleanup_orphan():
    count = delete_orphan_contents()
    return {"deleted": count}


# ── Delete (storage dahil)

@router.delete("/{content_id}")
def delete_content(content_id: str):
    safe_delete_content(content_id)
    return {"message": "İçerik ve dosyalar silindi"}
