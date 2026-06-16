import logging
from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from app.modules.content.service import (
    create_normal_video, create_short_video, create_post,
    publish_to_youtube, publish_to_instagram,
)
from app.db.repositories.generated_contents_repo import (
    create_content, update_content, get_content, list_contents,
    delete_content as db_delete,
)

logger = logging.getLogger(__name__)
router = APIRouter()


class ContentRequest(BaseModel):
    topic: str
    duration_minutes: int = 5


class ApproveRequest(BaseModel):
    action: str  # "approve" | "reject"
    notes: str = ""


def _background_generate(content_id: str, fn, *args):
    try:
        logger.info(f"[content] üretim başladı id={content_id}")
        result = fn(*args)
        updates = {"status": "pending_approval"}
        if result.get("video_path"):
            updates["video_url"] = result["video_path"]
        if result.get("audio_path"):
            updates["audio_url"] = result["audio_path"]
        if result.get("image_path"):
            updates["image_url"] = result["image_path"]
        if result.get("title"):
            updates["title"] = result["title"]
        if result.get("caption"):
            updates["caption"] = result["caption"]
        if result.get("script"):
            updates["script"] = result["script"]
        if result.get("audio_base64"):
            updates["audio_base64"] = result["audio_base64"]
        update_content(content_id, updates)
        logger.info(f"[content] üretim tamamlandı id={content_id}")
    except Exception as e:
        logger.error(f"[content] üretim hatası id={content_id} hata={e}")
        update_content(content_id, {"status": "error"})


@router.post("/video/generate")
def generate_video(req: ContentRequest, bg: BackgroundTasks):
    row = create_content(req.topic, "video")
    bg.add_task(_background_generate, row["id"], create_normal_video, req.topic, req.duration_minutes)
    return {"content_id": row["id"], "status": "generating"}


@router.post("/short/generate")
def generate_short(req: ContentRequest, bg: BackgroundTasks):
    row = create_content(req.topic, "short")
    bg.add_task(_background_generate, row["id"], create_short_video, req.topic)
    return {"content_id": row["id"], "status": "generating"}


@router.post("/post/generate")
def generate_post(req: ContentRequest, bg: BackgroundTasks):
    row = create_content(req.topic, "post")
    bg.add_task(_background_generate, row["id"], create_post, req.topic)
    return {"content_id": row["id"], "status": "generating"}


@router.get("")
def list_content():
    return list_contents()


@router.get("/{content_id}")
def get_content_by_id(content_id: str):
    item = get_content(content_id)
    if not item:
        raise HTTPException(status_code=404, detail="İçerik bulunamadı")
    return item


@router.patch("/{content_id}/approve")
def approve_content(content_id: str, req: ApproveRequest):
    item = get_content(content_id)
    if not item:
        raise HTTPException(status_code=404, detail="İçerik bulunamadı")
    new_status = "approved" if req.action == "approve" else "rejected"
    updates = {"status": new_status}
    if req.notes:
        updates["approval_notes"] = req.notes
    return update_content(content_id, updates)


@router.post("/{content_id}/publish")
def publish_content_unified(content_id: str):
    item = get_content(content_id)
    if not item:
        raise HTTPException(status_code=404, detail="İçerik bulunamadı")
    content_type = item.get("type", "video")
    if content_type in ("video", "short"):
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
    if item.get("type") not in ("video", "short"):
        raise HTTPException(status_code=400, detail="Bu içerik türü YouTube'a yüklenemez")
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


@router.delete("/{content_id}")
def delete_content(content_id: str):
    db_delete(content_id)
    return {"message": "İçerik silindi"}
